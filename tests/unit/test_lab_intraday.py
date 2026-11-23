"""The opening range breakout on five-minute bars: two LSE sessions with a hand-worked list of
actions, and the rule future-blind (decisions on the first k bars are the first k decisions)."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import ClassVar

import pytest

import lab.intraday as lab_intraday
from desk import bars, intraday, orders, venues
from desk.lines import LINES
from desk.orders import Leg, Settings
from desk.rollup import Candle
from desk.spans import Five
from desk.strategy import Action
from lab import rung, trials
from lab.intraday import IntradayMeanReversion, OpeningRangeBreakout
from lab.rung import Answer


def _session(
    day: date, closes: dict[int, float], rng: tuple[float, float], base: float
) -> list[Candle]:
    """The 102 bars of an LSE day: six bars spanning `rng`, then flat bars at `base` but for the
    closes given by bar number."""
    start, made = venues.hours("LSE", day).open, []
    for n in range(102):
        c = Decimal(str(closes.get(n, base)))
        high, low = (Decimal(str(rng[0])), Decimal(str(rng[1]))) if n < 6 else (c, c)
        made.append(
            Candle(start + timedelta(minutes=5 * n), c, max(high, c), min(low, c), c, 1, "x")
        )
    return made


FIRST = _session(date(2026, 11, 16), {6: 102, 8: 98, 9: 98, 10: 102}, (101, 99), 100)
SECOND = _session(date(2026, 11, 17), {7: 100, 8: 113, 20: 109}, (112, 110), 111)
BARS = FIRST + SECOND


def _run(bars: list[Candle]) -> list[Action]:
    return [d.action for d in intraday.run("orb", OpeningRangeBreakout(), "LSE", "X", bars)]


def test_the_breakout_is_bought_the_fall_sold_and_each_session_starts_fresh() -> None:
    got = {n: a for n, a in enumerate(_run(BARS)) if a is not Action.HOLD}
    assert got == {
        6: Action.BUY,  # a close of 102 over the range's high of 101
        8: Action.SELL,  # 98 under the low of 99
        10: Action.BUY,  # back over the high
        101: Action.SELL,  # flat 100 is inside the range, held to the session's last bar
        102 + 8: Action.BUY,  # 113 over the new range's high of 112; 100 at bar 7 bought nothing
        102 + 20: Action.SELL,  # 109 under the new low of 110
    }
    held = _session(date(2026, 11, 16), dict.fromkeys(range(6, 102), 102), (101, 99), 100)
    assert _run(held)[-1] is Action.SELL  # a position is closed at the session's last bar


def test_decisions_on_the_first_k_bars_are_the_first_k_decisions() -> None:
    every = _run(BARS)
    for k in (1, 6, 7, 9, 11, 102, 105, 110, 150, 204):
        assert _run(BARS[:k]) == every[:k]


def _flat(day: date, closes: dict[int, float]) -> list[Candle]:
    """The 102 bars of an LSE day, flat at 100 but for the closes given by bar number."""
    t, c = venues.hours("LSE", day).open, [Decimal(str(closes.get(n, 100))) for n in range(102)]
    return [Candle(t + timedelta(minutes=5 * n), x, x, x, x, 1, "x") for n, x in enumerate(c)]


REVERT = (
    _flat(date(2026, 11, 16), {5: 50})  # a dip before the band is full: nothing to buy under
    + _flat(date(2026, 11, 17), {19: 90})  # 90 under 99.5 less two deviations of 2.18
    + _flat(date(2026, 11, 18), dict.fromkeys(range(19, 102), 90))
)


def _revert(bars: list[Candle]) -> list[Action]:
    return [d.action for d in intraday.run("mr", IntradayMeanReversion(), "LSE", "X", bars)]


def test_the_band_buys_under_sells_over_the_middle_and_is_out_at_the_close() -> None:
    got = {n: a for n, a in enumerate(_revert(REVERT)) if a is not Action.HOLD}
    assert got == {
        102 + 19: Action.BUY,
        102 + 20: Action.SELL,  # 100 over the middle, 99.5
        204 + 19: Action.BUY,
        204 + 101: Action.SELL,  # held at 90 (never over the middle) to the last bar
    }
    for k in (5, 19, 20, 121, 122, 223, 306):  # future-blind
        assert _revert(REVERT[:k]) == _revert(REVERT)[:k]


class _Hold:
    """A stub rule: in the market on the bars numbered `wanted`."""

    span: ClassVar[intraday.Span] = intraday.Span.FIVE_MINUTES

    def __init__(self, wanted: range) -> None:
        self.wanted, self.n = wanted, -1

    def step(self, bar: Candle, holding: bool) -> bool:
        del bar, holding  # a stub rule reads neither
        self.n += 1
        return self.n in self.wanted


def _ramp(day: date) -> list[Candle]:
    """An LSE day whose bar n opens at 100 + n and closes half a point above."""
    t = venues.hours("LSE", day).open
    return [
        Candle(t + timedelta(minutes=5 * n), o, o + 1, o, o + Decimal("0.5"), 1, "x")
        for n, o in ((n, Decimal(100 + n)) for n in range(102))
    ]


def _priced(wanted: range) -> tuple[rung.Priced, ...]:
    bars, isf = _ramp(date(2026, 11, 16)), next(x for x in LINES if x.symbol == "ISF")
    got = intraday.run("t", _Hold(wanted), "LSE", "ISF", bars)
    return lab_intraday.priced(isf, [*got], bars, {}, Settings(Decimal(10000)))


def test_each_fill_is_the_next_opens_costed_by_orders_charges_and_a_last_bar_is_forced() -> None:
    isf = next(x for x in LINES if x.symbol == "ISF")
    sold, forced = _priced(range(2, 5))[0], _priced(range(98, 102))[0]
    # bought at bar 3's open (103), the sale decided on bar 5 filling at bar 6's open (106)
    n = sold.shares
    cost = orders.charges(isf, Leg.BUY, n, Decimal(103), Decimal(1)) + orders.charges(
        isf, Leg.SALE, n, Decimal(106), Decimal(1)
    )
    assert (sold.paid, sold.received, sold.costs) == (Decimal(103 * n), Decimal(106 * n), cost)
    assert sold.gain == (3 * n - cost.total) / (103 * n)
    # bought at 199 (bar 99's open); no bar follows bar 101, so out at its close, 201.5
    assert (forced.paid, forced.received) == (
        Decimal(199 * forced.shares),
        Decimal("201.5") * forced.shares,
    )


def test_the_gains_are_judged_by_the_rungs_rule_thin_and_refused_without_spread() -> None:
    two = (*_priced(range(2, 5)), *_priced(range(98, 102)))
    assert len(two) == 2
    assert lab_intraday.judged(two) is Answer.THIN
    with pytest.raises(ValueError, match="no spread"):
        lab_intraday.judged((two[0], two[0]))


def test_the_set_runs_two_rules_on_two_lines_and_counts_every_trial_before_judging(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    one, two = LINES[0], LINES[1]
    with bars.writing(tmp_path / bars.LIVE) as opened:
        for line in (one, two):
            opened.five(
                line, [Five(c.start, c.open, c.high, c.low, c.close, 1) for c in BARS[:102]]
            )
    register = tmp_path / "ladder" / "INTRADAY.trials.jsonl"
    counted: list[int] = []
    real = lab_intraday.judged

    def spy(trades: Sequence[rung.Priced]) -> Answer:
        counted.append(trials.count(register, lab_intraday.QUESTION))
        return real(trades)

    monkeypatch.setattr(lab_intraday, "judged", spy)
    said = lab_intraday.judge_set(tmp_path, {})
    assert counted == [4] * 4  # all four trials were entered before the first was judged
    table = (tmp_path / "ladder" / "sets" / "INTRADAY.md").read_text(encoding="utf-8")
    assert "PRE-REVIEW" in table and said.startswith("SET INTRADAY: 2 rules, 0 passed")
    assert (
        sum(f"| {r} | {x.symbol} (LSE) |" in table for r in lab_intraday.RULES for x in (one, two))
        == 4
    )
    assert (table.count("THIN"), table.count("FAULT")) == (2, 2)  # the band never trades a day
