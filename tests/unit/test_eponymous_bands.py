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


def test_four_week_rule_trades_on_the_days_it_fixes() -> None:
    # 20 flat sessions (highs 100.5, lows 99.5), then: 21 is not a breakout, 22 closes over the
    # 20-day high (101.0 on session 21 is the high; 102 > 101), 24 closes under the 20-day low.
    closes = ["100"] * 20 + ["100.5", "102", "103", "99", "98"]
    bars = _bars(closes)
    with pytest.MonkeyPatch.context() as only:
        only.setattr(
            strategy,
            "STRATEGIES",
            {"donchian_channel_breakout": EPONYMOUS["donchian_channel_breakout"]},
        )
        decided = strategy.decide({"X": bars})
    trades = [(n, d.action) for n, d in enumerate(decided) if d.action is not Action.HOLD]
    assert trades == [(21, Action.BUY), (23, Action.SELL)]
    assert {d.strategy for d in decided} == {"donchian_channel_breakout"}


def test_declares_a_daily_rule_on_every_line() -> None:
    declared = DonchianChannelBreakout.declared
    assert (declared.bar, declared.hold, declared.universe) == (Timeframe.DAILY, None, LINES)


def test_fade_buys_the_floor_and_sells_the_middle() -> None:
    # 20 flat sessions (channel 99.5-100.5, middle 100); 20 closes under the floor; 21 stays
    # under the middle (99.5); 22 closes at 100, the middle of the channel, and sells.
    bars = _bars(["100"] * 20 + ["99", "99.2", "100", "100"])
    with pytest.MonkeyPatch.context() as only:
        only.setattr(
            strategy, "STRATEGIES", {"donchian_fade_chop": EPONYMOUS["donchian_fade_chop"]}
        )
        decided = strategy.decide({"X": bars})
    assert [(n, d.action) for n, d in enumerate(decided) if d.action is not Action.HOLD] == [
        (20, Action.BUY),
        (22, Action.SELL),
    ]
    assert DonchianFadeChop.declared == DonchianChannelBreakout.declared
