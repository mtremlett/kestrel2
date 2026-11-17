"""The day's standing against the loss and order-rate limits, given to the gate on the send path."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from desk import book, day
from desk.broker import Pretend
from desk.halt import Blocker, Stopped
from desk.lines import Line
from desk.orders import Charges, Order, Settings
from desk.risk import Standing
from desk.store import Bar

MON, TUE, A = date(2025, 11, 10), date(2025, 11, 11), Line("A", "LSE", "GBP", 1)
BARS = {A: tuple(Bar(d, Decimal(50), Decimal(51), Decimal(49), Decimal(51), 1) for d in (MON, TUE))}


def test_a_lost_day_is_the_standing_that_makes_the_send_path_refuse_a_buy(tmp_path: Path) -> None:
    free = Charges(*[Decimal(0)] * 5)
    lost = day.Record(MON, Decimal(-300), free, Decimal(0), (), Decimal(0), 0)
    book._write(tmp_path / day.RECORDS, [day.HEADER, day._row(lost)])
    standing = day.standing(tmp_path, TUE)
    assert standing == Standing(Decimal(300), Decimal(300), 0)
    broker, order = Pretend(BARS, {}), Order("o-1", A, 1, *map(Decimal, (50, 1, 45)))
    broker.open(TUE)
    try:
        book.send(tmp_path, broker, order, Settings(Decimal(10_000)), None, standing)
    except Stopped as stopped:
        assert stopped.blocker is Blocker.GATE and "day-loss limit" in str(stopped)
    else:
        raise AssertionError("a buy past the day's loss limit was sent")
