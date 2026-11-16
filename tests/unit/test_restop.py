"""restop: a stop rests 10% under the fill, moved once, at 1x and at a leveraged line."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from desk import book
from desk.broker import Fill, Pretend
from desk.lines import Line
from desk.orders import Order
from desk.restop import due, move
from desk.store import Bar

LINE = Line("M", "US", "USD", 1)
MON, TUE = date(2026, 11, 16), date(2026, 11, 17)
SIGNAL = Decimal("111.62")


def _day(root: Path, fill: str) -> Pretend:
    """A buy sized at the signal close, filled at fill on Monday, its stop kept as sent."""
    bar = Bar(MON, Decimal(fill), Decimal(fill), Decimal(fill), Decimal(fill), 1)
    broker = Pretend({LINE: (bar,)}, {})
    broker.open(MON)
    order = Order("B1", LINE, 10, SIGNAL, Decimal(1), SIGNAL * Decimal("0.9"))
    book.keep(root / book.STOPS, [book.LEVELS, ("B1-stop", order.stop)])
    broker.place(order)
    (fill_,) = broker.fills()
    book.keep(root / book.LEDGER, [book.COLUMNS, _row(fill_)])
    return broker


def _row(f: Fill) -> tuple[object, ...]:
    return (f.execution_id, f.order_id, f.symbol, f.quantity, f.price, f.day)


@pytest.mark.parametrize(("fill", "stop"), [("104.92", "94.428"), ("120", "108")])
def test_the_stop_moves_once_to_ten_percent_under_the_fill(
    tmp_path: Path, fill: str, stop: str
) -> None:
    broker = _day(tmp_path, fill)
    assert due(tmp_path, {"M": LINE}) == {"B1-stop": Decimal(stop)}
    assert move(tmp_path, broker, {"M": LINE}) == ("B1-stop",)
    assert book.levels(tmp_path) == {"B1-stop": Decimal(stop)}
    assert move(tmp_path, broker, {"M": LINE}) == ()  #: a step run again moves nothing
