"""The building blocks, known answers on hand-made bars: each fires on exactly the bars its
definition fixes, and not before it has seen enough."""

from __future__ import annotations

import random
from datetime import date, timedelta
from decimal import Decimal, localcontext
from pathlib import Path

import pytest

from desk.eponymous_clenow_momentum import score
from desk.store import Bar
from desk.strategy import ARITHMETIC
from lab.block_base import Block, Kind
from lab.blocks import BLOCKS, SIZES, LogSlope, VolatilitySize


def _fire(name: str, bars: list[tuple[int, int, int]], holding: bool = False, **params: int) -> str:
    block: Block = BLOCKS[name].make(
        **{k: Decimal(v) if name == "trailing_stop" else v for k, v in params.items()}
    )
    out = ""
    for n, (high, low, close) in enumerate(bars):
        c, h, lo = map(Decimal, (close, high, low))
        bar = Bar(date(2020, 1, 1) + timedelta(n), c, h, lo, c, 1000)
        out += "1" if block.see(bar, holding) else "0"
    return out


FLAT = [(11, 9, 10)] * 3


@pytest.mark.parametrize(
    ("name", "bars", "holding", "params", "answer"),
    [
        ("highest_high", [*FLAT, (12, 10, 12), (13, 11, 13)], False, {"n": 3}, "00011"),
        ("lowest_low", [*FLAT, (9, 7, 8), (8, 7, 8)], False, {"n": 3}, "00010"),
        (
            "close_below_average",
            [(1, 1, 3), (1, 1, 3), (1, 1, 3), (1, 1, 2)],
            False,
            {"n": 3},
            "0001",
        ),
        (
            "close_above_average",
            [(1, 1, 1), (1, 1, 1), (1, 1, 1), (1, 1, 5)],
            False,
            {"n": 3},
            "0001",
        ),
        (
            "trailing_stop",
            [(1, 1, 100), (1, 1, 110), (1, 1, 100), (1, 1, 99)],
            True,
            {"pct": 10},
            "0001",
        ),
        ("trailing_stop", [(1, 1, 1), (1, 1, 1)], False, {"pct": 10}, "00"),
        ("no_stop", FLAT, True, {}, "000"),
        ("lower_run", [(10, 8, 9), (9, 7, 8), (8, 6, 7), (9, 7, 8)], False, {"n": 2}, "0010"),
        (
            "close_near_range_low",
            [(10, 0, 5), (10, 0, 5), (10, 0, 1), (10, 0, 9)],
            False,
            {"n": 3, "pct": 20},
            "0010",
        ),
        (
            "close_near_range_high",
            [(10, 0, 5), (10, 0, 5), (10, 0, 9), (10, 0, 1)],
            False,
            {"n": 3, "pct": 20},
            "0010",
        ),
        (
            "close_at_range_low",
            [*[(101, 99, 100)] * 3, (100, 98, 99), (100, 98, 98)],
            False,
            {"n": 3},
            "00011",
        ),
        ("close_at_range_low", [*FLAT, (10, 8, 8)], False, {"n": 3}, "0000"),
        ("close_at_midpoint", [*FLAT, (10, 10, 10), (9, 9, 9)], False, {"n": 3}, "00010"),
        (
            "close_under_close_ago",
            [(5, 5, 5), (6, 6, 6), (7, 7, 7), (4, 4, 4), (8, 8, 8)],
            False,
            {"n": 2},
            "00010",
        ),
        ("close_at_or_under_average", [(3, 3, 3)] * 4, False, {"n": 3}, "0011"),
        (
            "big_move",
            [(c, c, c) for c in (100, 100, 120, 120, 120)],
            False,
            {"n": 2, "pct": 10},
            "00110",
        ),
        ("time_stop", FLAT, True, {"n": 2}, "011"),
        ("time_stop", FLAT, False, {"n": 2}, "000"),
        (
            "rising_score",
            [(c, c, c) for c in (100, 101, 102, 120)],
            False,
            {"n": 3, "pct": 10},
            "0010",
        ),
        (
            "rsi_under",
            [(c, c, c) for c in (10, 11, 12, 9, 8, 5)],
            False,
            {"n": 2, "pct": 10},
            "000001",
        ),
        (
            "highest_high_on_volume",
            [(11, 9, 10)] * 3 + [(13, 11, 12)],
            False,
            {"n": 3, "pct": 101},
            "0000",
        ),
        ("no_exit", FLAT, True, {}, "000"),
        ("no_filter", FLAT, False, {}, "111"),
    ],
)
def test_block_fires_on_the_bars_its_definition_fixes(
    name: str, bars: list[tuple[int, int, int]], holding: bool, params: dict[str, int], answer: str
) -> None:
    assert _fire(name, bars, holding, **params) == answer


def test_every_block_has_its_kind_and_parameters_in_range() -> None:
    spots = (*BLOCKS.values(), *SIZES.values())
    assert {s.kind for s in spots} == set(Kind)
    assert (
        {s.kind for s in SIZES.values()}
        == {Kind.SIZE}
        == set(Kind) - {s.kind for s in BLOCKS.values()}
    )
    assert all(p.low < p.high for s in spots for p in s.params.values())


def test_the_rolling_log_slope_scores_exactly_as_the_desks_clenow_score() -> None:
    rng, slope, closes = random.Random(7), LogSlope(90), []  # noqa: S311 - a test draw
    with localcontext(ARITHMETIC):
        for _ in range(300):
            closes.append(Decimal(f"{100 + rng.gauss(0, 5):.4f}"))
            slope.add(closes[-1])
            if slope.full:
                assert slope.score() == score(closes[-90:])


def test_the_sizing_block_sizes_by_the_desks_volatility_rule() -> None:
    def size(n: int, closes: tuple[int, ...]) -> list[int]:
        sizer, sized = VolatilitySize(n), []
        for close in closes:
            c = Decimal(close)
            assert not sizer.see(Bar(date(2020, 1, 1), c, c, c, c, 1000), holding=False)
            sized.append(sizer.shares(Decimal(1000)))
        return sized

    assert size(2, (100, 110, 99)) == [0, 0, 71]  # +10%, -10%: 1000 / (99 x 0.1414)
    assert size(2, (50, 100, 110, 99)) == [0, 0, 14, 71]  # the oldest close drops out
    with pytest.raises(ValueError, match="positive risk, price and volatility"):
        size(2, (100, 100, 100))  # a line that never moved has no risk to size by
    with pytest.raises(ValueError, match="two or more"):
        VolatilitySize(1)


def test_no_lab_module_imports_the_retiring_clenow_desk_module() -> None:
    for path in Path("lab").glob("*.py"):
        assert "desk.eponymous_clenow_momentum" not in path.read_text(encoding="utf-8"), path
