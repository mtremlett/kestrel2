"""R-RUNNER-232: an INCUBATE rule trades 250 pounds a position, two at most, on its own line."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from desk import book, incubation
from desk.broker import Pretend
from desk.lines import Line
from desk.orders import Order, Refused, Settings
from desk.store import Bar
from desk.strategy import Action, Decision

MON = date(2025, 11, 10)
LINES = [Line(s, "LSE", "GBP", 1) for s in "ABC"]
BAR = Bar(MON, Decimal(50), Decimal(51), Decimal(49), Decimal(51), 1)


def _decision(symbol: str) -> Decision:
    return Decision("rule", symbol, MON, Action.BUY)


def _buy(root: Path, broker: Pretend, line: Line) -> Order:
    order = incubation.buy(root, _decision(line.symbol), line, Decimal(50), Decimal(1))
    assert incubation.send(root, broker, order).filled == order.quantity
    return order


def test_a_buy_is_two_fifty_on_the_incubation_line_two_open_and_a_pass_rule_untouched(
    tmp_path: Path,
) -> None:
    broker = Pretend({line: (BAR,) for line in LINES}, {})
    broker.open(MON)
    first = _buy(tmp_path, broker, LINES[0])
    assert (first.order_id, first.quantity) == ("inc-20251110-rule-A", 4)
    assert first.quantity * first.price <= incubation.POUNDS
    desk = Order("20251110-pass-C", LINES[2], 10, *map(Decimal, (50, 1, 45)))
    assert book.send(tmp_path, broker, desk, Settings(Decimal(10_000))).filled == 10
    _buy(tmp_path, broker, LINES[1])
    assert incubation.held(tmp_path) == {"A": 4, "B": 4}  #: C is the desk's, not incubation's
    assert book.positions(tmp_path) == {"A": 4, "B": 4, "C": 10}
    with pytest.raises(Refused, match="at most 2"):
        incubation.buy(tmp_path, _decision("C"), LINES[2], Decimal(50), Decimal(1))
    with pytest.raises(ValueError, match="not an incubation order"):
        incubation.send(tmp_path, broker, desk)
    sale = incubation.sell(tmp_path, "sell-A", LINES[0])
    assert incubation.send(tmp_path, broker, sale).filled == 4
    assert incubation.held(tmp_path) == {"B": 4}
