"""Donchian's four-week rule, known answer: on a series built so the published rule fixes the
days, the rule buys and sells on exactly those days, and declares itself as a daily, long-only
rule on every line."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest

from desk import strategy
from desk.eponymous_bands import EPONYMOUS, DonchianChannelBreakout, DonchianFadeChop
from desk.lines import LINES
from desk.store import Bar
from desk.strategy import Action, Timeframe


def _bars(closes: list[str]) -> tuple[Bar, ...]:
    out = []
    for n, value in enumerate(closes):
        close = Decimal(str(value))
        day = date(2020, 1, 1) + timedelta(n)
        out.append(Bar(day, close, close + Decimal("0.5"), close - Decimal("0.5"), close, 1000))
    return tuple(out)


def _trades(name: str, closes: list[str]) -> list[tuple[int, Action]]:
    with pytest.MonkeyPatch.context() as only:
        only.setattr(strategy, "STRATEGIES", {name: EPONYMOUS[name]})
        decided = strategy.decide({"X": _bars(closes)})
    return [(n, d.action) for n, d in enumerate(decided) if d.action is not Action.HOLD]


def test_four_week_rule_trades_on_the_days_it_fixes() -> None:
    # 20 flat sessions (highs 100.5, lows 99.5), then: 21 is not a breakout, 22 closes over the
    # 20-day high (101.0 on session 21 is the high; 102 > 101), 24 closes under the 20-day low.
    closes = ["100"] * 20 + ["100.5", "102", "103", "99", "98"]
    assert _trades("donchian_channel_breakout", closes) == [(21, Action.BUY), (23, Action.SELL)]


def test_fade_in_chop_buys_the_low_edge_and_sells_the_midpoint() -> None:
    # 20 flat sessions: channel 99.5-100.5 is a range. 99 closes under its low: buy (20). The
    # channel is now 98.5-100.5, midpoint 99.5: 99.2 is held (21); 100 is over it: sell (22).
    closes = ["100"] * 20 + ["99", "99.2", "100"]
    assert _trades("donchian_fade_chop", closes) == [(20, Action.BUY), (22, Action.SELL)]


def test_fade_in_chop_leaves_a_trend_alone() -> None:
    # A channel 20% wide is no range: the close under its low is not faded.
    closes = [str(100 + n * 2) for n in range(20)] + ["90"]
    assert _trades("donchian_fade_chop", closes) == []


def test_declares_a_daily_rule_on_every_line() -> None:
    for rule in (DonchianChannelBreakout, DonchianFadeChop):
        declared = rule.declared
        assert (declared.bar, declared.universe) == (Timeframe.DAILY, LINES)
    assert DonchianChannelBreakout.declared.hold is None
    assert DonchianFadeChop.declared.hold is None
