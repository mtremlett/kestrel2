"""incubation: an INCUBATE rule buys GBP 250 a position on its own book line, at most two open,
through the one gate; a PASS rule is left to its own rules (R-RUNNER-232)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from desk import incubation
from desk.book_parts2 import _record
from desk.broker import Fill
from desk.lines import Line
from desk.orders import Order, Refused, cost, strategy_of
from desk.strategy import Action, Decision

ON = date(2025, 11, 14)
PRICE, ONE = Decimal(40), Decimal(1)


def _line(symbol: str) -> Line:
    return Line(symbol, "LSE", "GBP", 1)


def _buy(symbol: str, answer: str = "INCUBATE", root: Path | None = None) -> Order:
    decision = Decision("rule", symbol, ON, Action.BUY)
    return incubation.buy(root or Path("none"), answer, decision, _line(symbol), PRICE, ONE)


def _hold(root: Path, symbol: str) -> None:
    order_id = f"{ON:%Y%m%d}-{incubation.LINE}-{symbol}"
    _record(root, [Fill(f"x-{symbol}", order_id, symbol, 6, PRICE, ON)])


def test_an_incubate_buy_is_250_pounds_on_the_incubation_line(tmp_path: Path) -> None:
    order = _buy("AAA", root=tmp_path)
    assert strategy_of(order.order_id) == incubation.LINE
    assert order.quantity == 6 and cost(order) <= 250 < cost(order) + PRICE


def test_a_third_open_position_is_refused_but_a_held_line_may_grow(tmp_path: Path) -> None:
    _hold(tmp_path, "AAA")
    _hold(tmp_path, "BBB")
    assert incubation.held(tmp_path) == {"AAA": 6, "BBB": 6}
    with pytest.raises(Refused, match="at most 2"):
        _buy("CCC", root=tmp_path)
    with pytest.raises(Refused, match="room"):
        _buy("AAA", root=tmp_path)  # already holds its 250 pounds: no room for more


def test_a_pass_rule_is_untouched(tmp_path: Path) -> None:
    with pytest.raises(Refused, match="not INCUBATE"):
        _buy("AAA", answer="PASS", root=tmp_path)
    assert incubation.held(tmp_path) == {}
