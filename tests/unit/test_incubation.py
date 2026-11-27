"""incubation: an INCUBATE rule trades 250 pounds a position, two open, on its own book line."""

from __future__ import annotations

from dataclasses import replace
from datetime import date
from decimal import Decimal

import pytest

from desk import incubation, orders
from desk.broker import Fill
from desk.lines import Line
from desk.strategy import Action, Decision

ON = date(2025, 11, 14)


def _line(symbol: str) -> Line:
    return Line(symbol, "LSE", "GBP", 1)


def _buy(symbol: str) -> orders.Order:
    return incubation.buy("rule", _line(symbol), ON, Decimal(10), Decimal(1), {})


def test_an_incubate_buy_is_250_pounds_on_the_incubation_line_and_a_third_is_refused() -> None:
    first = _buy("A")
    assert orders.cost(first) <= 250 < orders.cost(replace(first, quantity=first.quantity + 1))
    assert incubation.is_incubating(first.order_id) and not orders.is_zoo(first.order_id)
    with pytest.raises(orders.Refused, match="at most 2 open"):
        incubation.buy("rule", _line("C"), ON, Decimal(10), Decimal(1), {"A": 20, "B": 20})
    incubation.buy("rule", _line("A"), ON, Decimal(10), Decimal(1), {"A": 5, "B": 20})


def test_a_pass_rules_buy_is_untouched_and_not_on_the_incubation_line() -> None:
    plain = orders.size(
        Decision("pass", "A", ON, Action.BUY),
        _line("A"),
        Decimal(10),
        Decimal(1),
        orders.Settings(Decimal(10_000)),
        {},
    )
    assert plain.quantity > _buy("A").quantity and not incubation.is_incubating(plain.order_id)
    fills = [
        Fill("x1", plain.order_id, "A", 5, Decimal(10), ON),
        Fill("x2", _buy("B").order_id, "B", 5, Decimal(10), ON),
    ]
    assert incubation.side(fills, {"A": 5, "B": 5}) == {"B": 5}
