"""Each strategy beside simply holding its market: both figures after the same costs, and the
difference."""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

import pytest
from test_lab_rung import POUND, SHAPE, TEN_K, _bars, _judge

from desk import orders
from desk.orders import Leg
from lab import holding


def test_a_strategy_and_its_market_give_both_figures_and_the_difference() -> None:
    bars = _bars(SHAPE)
    verdict = _judge(bars, 24)
    line = verdict.key.cell.line
    found = holding.beside(verdict, bars, line, bars, POUND, TEN_K)
    #: the one trade: 192 shares bought at 2054.40 and sold at 1797.12, 11.64828 of costs
    assert found.strategy == Decimal("-268.92864") / 10_000
    #: 199 shares bought at the first open, 10, and sold at the last close, 9.40
    costs = sum(
        orders.charges(line, leg, 199, price, Decimal(1)).total
        for leg, price in ((Leg.BUY, Decimal(10)), (Leg.SALE, Decimal("9.40")))
    )
    assert found.shares == 199
    assert found.held == (Decimal("-119.4") - costs) / 10_000
    assert found.difference == found.strategy - found.held < 0, "holding beat this rule"
    assert found.row() == "-2.69% strategy, -1.29% holding VUSA, -1.40% difference"


def test_bars_that_did_not_make_the_verdict_or_a_market_with_no_window_are_refused() -> None:
    bars = _bars(SHAPE)
    verdict = _judge(bars, 24)
    line = verdict.key.cell.line
    with pytest.raises(ValueError, match="did not make the verdict"):
        holding.beside(verdict, bars[:-1], line, bars, POUND, TEN_K)
    later = [replace(bar, day=bar.day.replace(year=2020)) for bar in bars]
    with pytest.raises(ValueError, match="no bar from"):
        holding.beside(verdict, bars, line, later, POUND, TEN_K)
