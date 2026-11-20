"""incubation: an INCUBATE rule's buy is 250 pounds on its own line; a third is refused."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from desk import incubation
from desk.broker import Fill
from desk.lines import Line
from desk.orders import Order, Refused, cost
from desk.strategy import Action, Decision

DAY = date(2025, 11, 10)


def _buy(symbol: str, rule: str = "x") -> Decision:
    return incubation.incubate(Decision(rule, symbol, DAY, Action.BUY))


def _fill(symbol: str, rule: str) -> Fill:
    return Fill("e", f"20251110-{rule}-{symbol}", symbol, 3, Decimal(50), DAY)


def _size(symbol: str, ledger: list[Fill]) -> Order:
    line = Line(symbol, "LSE", "GBP", 1)
    return incubation.size_incubating(_buy(symbol), line, Decimal(50), Decimal(1), ledger)


def test_a_buy_is_two_fifty_on_the_incubation_line_and_a_third_is_refused() -> None:
    order = _size("A", [])
    assert order.order_id == "20251110-inc_x-A"
    assert Decimal(250) - Decimal(50) < cost(order) <= Decimal(250)
    own = [_fill("A", "inc_x"), _fill("B", "inc_y")]
    assert incubation.held(own) == {"A": 3, "B": 3}
    assert _size("A", own).quantity == order.quantity - 3
    with pytest.raises(Refused, match="at most 2"):
        _size("C", own)


def test_a_pass_rule_is_untouched() -> None:
    desk = [_fill("A", "ema"), _fill("B", "ema"), _fill("C", "ema")]
    assert incubation.held(desk) == {}
    assert _size("D", desk).quantity > 0
    with pytest.raises(ValueError, match="not an incubating rule"):
        incubation.size_incubating(
            Decision("ema", "A", DAY, Action.BUY),
            Line("A", "LSE", "GBP", 1),
            Decimal(50),
            Decimal(1),
            [],
        )
