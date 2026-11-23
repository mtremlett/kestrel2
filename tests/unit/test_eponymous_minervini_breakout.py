"""Minervini's breakout, known answer: on a series built so the published rule fixes the days,
the rule buys and sells on exactly those days, and not in a market that is not in an uptrend."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from desk.eponymous_minervini_breakout import MinerviniBreakout, decide
from desk.lines import LINES
from desk.store import Bar
from desk.strategy import Action, Timeframe


def _bars(closes: list[Decimal]) -> tuple[Bar, ...]:
    half = Decimal("0.5")
    return tuple(
        Bar(date(2020, 1, 1) + timedelta(n), c, c + half, c - half, c, 1000)
        for n, c in enumerate(closes)
    )


def _trades(closes: list[Decimal]) -> list[tuple[int, Action]]:
    decided = decide({"X": _bars(closes)})
    return [(n, d.action) for n, d in enumerate(decided) if d.action is not Action.HOLD]


def test_buys_the_breakout_in_the_trend_template_and_sells_under_the_50_day() -> None:
    # 260 sessions rising 0.2 a day from 100 (a year up 50%, every average stacked in order, a
    # rise of 0.2 never clears the last 15 highs, which stand 0.5 over their closes); session 260
    # jumps 2 over the pivot: the buy. Sessions 261-264 climb on; session 265 closes at 100,
    # far under the 50-day average (about 140): the sell.
    up = [Decimal(100) + Decimal("0.2") * n for n in range(260)]
    top = up[-1]
    after = [top + Decimal(x) for x in ("2", "2.2", "2.4", "2.6", "2.8")]
    closes = [*up, *after, Decimal(100)]
    assert _trades(closes) == [(260, Action.BUY), (265, Action.SELL)]


def test_does_not_buy_a_breakout_in_a_market_going_nowhere() -> None:
    flat = [Decimal(100)] * 300
    assert _trades([*flat, Decimal(104)]) == []


def test_declares_a_daily_rule_on_every_line() -> None:
    declared = MinerviniBreakout.declared
    assert (declared.bar, declared.hold, declared.universe) == (Timeframe.DAILY, None, LINES)
