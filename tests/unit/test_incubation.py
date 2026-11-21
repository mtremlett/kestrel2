"""incubation: an INCUBATE rule's buy is GBP 250 on its own book line, at most two open."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from desk import incubation
from desk.broker import Fill
from desk.lines import Line
from desk.orders import Order, Refused
from desk.strategy import Action, Decision

ON = date(2025, 11, 14)
RULES = frozenset({"inc"})


def _line(symbol: str) -> Line:
    return Line(symbol, "LSE", "GBP", 1)


def _fill(strategy: str, symbol: str, quantity: int) -> Fill:
    return Fill(
        f"e-{strategy}-{symbol}", f"20251113-{strategy}-{symbol}", symbol, quantity, Decimal(10), ON
    )


def _buy(strategy: str, symbol: str) -> Decision:
    return Decision(strategy, symbol, ON, Action.BUY)


def _order(strategy: str, symbol: str, ledger: list[Fill]) -> Order:
    return incubation.buy(
        _buy(strategy, symbol), _line(symbol), Decimal(10), Decimal(1), RULES, ledger
    )


def test_a_buy_is_two_hundred_and_fifty_pounds_booked_on_the_incubation_line() -> None:
    order = _order("inc", "A", [])
    assert order.quantity == 24 and order.order_id == "20251114-inc-A"
    assert incubation.held([_fill("inc", "A", 25)], RULES) == {"A": 25}


def test_a_third_open_position_is_refused_and_a_held_one_is_not() -> None:
    ledger = [_fill("inc", "A", 25), _fill("inc", "B", 25)]
    with pytest.raises(Refused, match="at most 2"):
        _order("inc", "C", ledger)
    with pytest.raises(Refused, match="no room"):
        _order("inc", "A", ledger)


def test_a_pass_rule_is_untouched() -> None:
    ledger = [_fill("pass", "A", 100), _fill("pass", "B", 100), _fill("inc", "C", 25)]
    assert incubation.held(ledger, RULES) == {"C": 25}
    assert _order("inc", "A", ledger).quantity == 24
    with pytest.raises(ValueError, match="not an INCUBATE rule"):
        _order("pass", "D", ledger)
