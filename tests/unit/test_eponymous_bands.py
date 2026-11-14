"""Donchian's four-week rule, known answer: on a series built so the published rule fixes the
days, the rule buys and sells on exactly those days, and declares itself as a daily, long-only
rule on every line."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest

from desk import strategy
from desk.eponymous_bands import EPONYMOUS, DonchianChannelBreakout
from desk.lines import LINES
from desk.store import Bar
from desk.strategy import Action, Timeframe


def _bars(closes: list[int | str]) -> tuple[Bar, ...]:
    out = []
    for n, value in enumerate(closes):
        close = Decimal(str(value))
        day = date(2020, 1, 1) + timedelta(n)
        out.append(Bar(day, close, close + Decimal("0.5"), close - Decimal("0.5"), close, 1000))
    return tuple(out)


def test_four_week_rule_trades_on_the_days_it_fixes() -> None:
    # 20 flat sessions (highs 100.5, lows 99.5), then: 21 is not a breakout, 22 closes over the
    # 20-day high (101.0 on session 21 is the high; 102 > 101), 24 closes under the 20-day low.
    closes: list[int | str] = [100] * 20 + ["100.5", 102, 103, 99, 98]
    bars = _bars(closes)
    with pytest.MonkeyPatch.context() as only:
        only.setattr(strategy, "STRATEGIES", EPONYMOUS)
        decided = strategy.decide({"X": bars})
    trades = [(n, d.action) for n, d in enumerate(decided) if d.action is not Action.HOLD]
    assert trades == [(21, Action.BUY), (23, Action.SELL)]
    assert {d.strategy for d in decided} == {"donchian_channel_breakout"}


def test_declares_a_daily_rule_on_every_line() -> None:
    declared = DonchianChannelBreakout.declared
    assert (declared.bar, declared.hold, declared.universe) == (Timeframe.DAILY, None, LINES)
