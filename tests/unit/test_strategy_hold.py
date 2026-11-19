"""STP-11: a strategy that declares a holding period is sold out of at its end."""

from __future__ import annotations

from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal

import pytest

from desk import strategy
from desk.store import Bar
from desk.strategy import Action


class _Eager:
    """A rule that always wants the line and declares three sessions."""

    declared = replace(strategy.STRATEGIES["rsi2_pullback"].declared, hold=3)

    def step(self, _bar: Bar, _holding: bool) -> bool:
        return True


def test_a_declared_holding_period_ends_in_a_sale(monkeypatch: pytest.MonkeyPatch) -> None:
    #: bought on day 0, held 3 sessions, sold on day 3, and the rule may buy again
    monkeypatch.setattr(strategy, "STRATEGIES", {"eager": _Eager})
    price = Decimal(10)
    bars = tuple(
        Bar(date(2020, 1, 1) + timedelta(n), price, price, price, price, 1) for n in range(9)
    )
    acts = [d.action for d in strategy.decide({"A": bars})]
    assert acts == [Action.BUY, *[Action.HOLD] * 2, Action.SELL] * 2 + [Action.BUY]
