"""incubation: a rule the ladder calls INCUBATE trades on paper at 250 pounds a position, at most
two open, on its own book line apart from the desk's rules (R-RUNNER-232, EASING 3)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from desk import incubation, orders
from desk.broker import Fill
from desk.lines import Line
from desk.strategy import Action, Decision

ON = date(2025, 11, 14)
LINES = [Line(s, "LSE", "GBP", 1) for s in "ABC"]
VERDICTS = {"slow": "INCUBATE", "steady": "PASS"}


def _buy(rule: str, line: Line) -> Decision:
    return incubation.booked(Decision(rule, line.symbol, ON, Action.BUY), VERDICTS)


def _size(line: Line, held: dict[str, int]) -> orders.Order:
    return incubation.size(_buy("slow", line), line, Decimal(10), Decimal(1), held)


def test_an_incubate_rule_buys_250_pounds_on_its_own_line_and_a_third_is_refused() -> None:
    first = _size(LINES[0], {})
    assert incubation.is_incubating(first.order_id) and not orders.is_zoo(first.order_id)
    assert first.quantity == 24 and orders.cost(first) <= incubation.ROOM
    second = _size(LINES[1], {"A": 24})
    assert second.quantity == 24
    with pytest.raises(orders.Refused, match="at most 2"):
        _size(LINES[2], {"A": 24, "B": 24})


def test_a_pass_rule_is_untouched_and_the_desks_holdings_are_not_counted() -> None:
    decision = Decision("steady", "A", ON, Action.BUY)
    assert incubation.booked(decision, VERDICTS) == decision
    with pytest.raises(ValueError, match="incubat"):
        incubation.size(decision, LINES[0], Decimal(10), Decimal(1), {})
    desk = Fill("x", f"{ON:%Y%m%d}-steady-A", "A", 5, Decimal(10), ON)
    mine = Fill("y", f"{ON:%Y%m%d}-inc_slow-B", "B", 5, Decimal(10), ON)
    assert incubation.apart([desk, mine], {"A": 5, "B": 5}) == {"B": 5}
