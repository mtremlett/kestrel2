"""An INCUBATE rule trades small and apart: 250 pounds, two open, its own line of the book."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from desk import book, incubation
from desk.broker import Pretend
from desk.lines import Line
from desk.orders import Refused, Settings, size
from desk.store import Bar
from desk.strategy import Action, Decision

MON = date(2025, 11, 10)
LINES = [Line(s, "LSE", "GBP", 1) for s in "ABC"]
BAR = Bar(MON, Decimal(10), Decimal(11), Decimal("9.5"), Decimal(10), 10**6)


def _decision(strategy: str, symbol: str) -> Decision:
    return Decision(strategy, symbol, MON, Action.BUY)


def test_a_buy_is_250_pounds_on_its_own_line_and_a_third_is_refused(tmp_path: Path) -> None:
    broker = Pretend({line: (BAR,) for line in LINES}, {})
    broker.open(MON)
    ten = Decimal(10)
    for line in LINES[:2]:
        order = incubation.buy(tmp_path, _decision("r", line.symbol), line, ten, Decimal(1), None)
        assert order.order_id.endswith(f"-inc_r-{line.symbol}") and order.quantity <= 25
        book.send(tmp_path, broker, order, incubation.SMALL)
    assert set(incubation.held(tmp_path)) == {"A", "B"}
    with pytest.raises(Refused, match="2 open"):
        incubation.buy(tmp_path, _decision("r", "C"), LINES[2], ten, Decimal(1), None)


def test_a_pass_rule_is_untouched() -> None:
    desk = size(
        _decision("rsi", "A"), LINES[0], Decimal(10), Decimal(1), Settings(Decimal(10_000)), {}
    )
    assert not incubation.is_incubating(desk.order_id) and desk.quantity > 25
