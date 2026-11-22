"""The fast engine for spec rows against the desk's own: the same position after every bar of
the golden series, cut short and whole, for each row, or a refusal, never a guess."""

from __future__ import annotations

import tomllib
from collections.abc import Sequence
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from test_strategy import GOLDEN, START, _bars, _jumpy, _walk

from desk.store import Bar
from lab import blocks, fast, grid, variants
from lab.spec import Spec, SpecRule

#: Either side of the warm-ups, and the middle of a walk.
CUTS = (0, 1, 2, 9, 10, 11, 19, 20, 21, 99, 100, 101, 199, 200, 201, 777)
#: What the fast engine refuses on the golden series: nothing.
REFUSED = 0


def _row(name: str, n: int, blocks_: tuple[str, str, str], **given: dict[str, Any]) -> Spec:
    """A row of entry `n` days, with the exit, stop and filter blocks named; its one known
    answer is a flat run of `n` bars, a breakout, then a collapse."""
    flat = [[11, 9, 10]] * n
    case = {"bars": [*flat, [13, 11, 12], [10, 7, 8]], "wants": [0] * n + [1, 0]}
    return Spec.parse(
        {
            "name": name,
            "entry": "highest_high",
            "exit": blocks_[0],
            "stop": blocks_[1],
            "filter": blocks_[2],
            "params": {"entry": {"n": n}, "exit": {"n": 10}, "stop": {}, "filter": {}} | given,
            "source": "a test row",
            "cases": [case],
        }
    )


LOW, AVG, TRAIL, NONE, ABOVE, ALL = (
    "lowest_low",
    "close_below_average",
    "trailing_stop",
    "no_stop",
    "close_above_average",
    "no_filter",
)
ROWS = (
    _row("donchian 20/10", 20, (LOW, NONE, ALL)),
    _row("donchian 5/5", 5, (LOW, NONE, ALL), exit={"n": 5}),
    _row("sma exit", 60, (AVG, NONE, ALL), exit={"n": 50}),
    _row("stopped", 55, (LOW, TRAIL, ALL), stop={"pct": 10}),
    _row("tight", 10, (AVG, TRAIL, ABOVE), stop={"pct": "2.5"}, filter={"n": 10}),
    _row("filtered", 100, (LOW, TRAIL, ABOVE), stop={"pct": 1}, filter={"n": 50}),
)


def _desk(spec: Spec, bars: Sequence[Bar]) -> list[bool]:
    """The row in the market or out of it after each bar, by the desk's own engine."""
    rule, holding, out = SpecRule(spec), False, []
    for bar in bars:
        holding = rule.step(bar, holding)
        out.append(holding)
    return out


def _series() -> dict[str, tuple[Bar, ...]]:
    out = {}
    for label in GOLDEN:
        kind, seed = label.split()
        out[label] = _walk(int(seed), 1200) if kind == "walk" else _jumpy(int(seed))
    return out


def test_every_row_trades_on_the_golden_series_as_the_desk_trades() -> None:
    refused, trades = 0, 0
    for label, bars in _series().items():
        for spec in ROWS:
            desk = _desk(spec, bars)
            trades += sum(a and not b for a, b in zip(desk, [False, *desk], strict=False))
            for cut in (*CUTS, len(bars)):
                try:
                    found = fast.held(spec, fast.Shared(bars[:cut])).tolist()
                except grid.TooClose:
                    refused += 1
                    continue
                assert found == desk[:cut], f"{spec.name} on {label}, its first {cut} bars"
    assert trades > 100  # the rows trade, so the match means something
    assert refused == REFUSED


def test_the_fast_engine_has_a_firing_for_every_block_that_needs_no_position() -> None:
    assert {*fast.FIRES, *fast.DATED, *fast.VOLUMED} == set(blocks.BLOCKS) - {
        "trailing_stop",
        "time_stop",
        "under_entry_low",
        "darvas_box",
        "darvas_stop",
        "breadth_thrust",  # on ratio bars, not price bars: the fast engine serves none
    }


def test_rows_on_one_line_share_one_working_of_a_block() -> None:
    shared = fast.Shared(_walk(1, 300))
    first = shared.fires("highest_high", {"n": 20})
    assert shared.fires("highest_high", {"n": 20}) is first
    assert shared.fires("highest_high", {"n": 21}) is not first


def test_a_close_exactly_on_the_stop_sells_and_a_penny_over_holds() -> None:
    spec = ROWS[3]  # donchian 55, trailing 10 per cent: from a held peak of 102, 91.8 is the stop
    for last, held in (("91.8", False), ("91.81", True)):
        closes = ["100"] * 55 + ["102", "102", last]
        bars = [
            Bar(START + timedelta(n), Decimal(c), Decimal(c) + 1, Decimal(79), Decimal(c), 1000)
            for n, c in enumerate(closes)
        ]
        assert _desk(spec, bars)[-1] is held
        assert fast.held(spec, fast.Shared(bars)).tolist()[-1] is held


def test_prices_too_close_for_floating_point_are_refused() -> None:
    bars = list(_bars([100] * 60 + [101, 100, 99]))
    last, price = bars[-1], Decimal("90.0000000000000000000000001")
    bars[-1] = Bar(last.day, price, last.high, last.low, price, 1000)
    with pytest.raises(grid.TooClose):
        fast.held(ROWS[3], fast.Shared(bars))


def test_every_row_of_the_spec_book_trades_on_the_fast_engine_as_the_desk_trades() -> None:
    book = tomllib.loads((Path(__file__).parents[2] / "lab" / "catalogue.toml").read_text("utf-8"))
    bars = tuple(  # a swinging volume, so the volume rows trade
        replace(b, volume=1000 + 900 * (n * 7 % 5 - 2) // 2)
        for n, b in enumerate(next(iter(_series().values())))
    )
    for name, row in book.items():
        spec = Spec.parse({"name": name, **row})
        if name == "zweig_breadth_thrust":  # judged on ratio bars, which this price series is not
            continue
        made = variants.variants(spec) if spec.ranges else ()  # the settings the grid sweeps too
        for each in (spec, *(variant.spec for variant in made)):
            assert fast.held(each, fast.Shared(bars)).tolist() == _desk(each, bars), each.name
    demark = {"name": "demark_sequential", **book["demark_sequential"]}
    with pytest.raises(ValueError, match="case 0 gives"):  # a setting, not the book's constant
        Spec.parse({**demark, "params": {"entry": {"n": 7}, "exit": {"n": 7}}})
