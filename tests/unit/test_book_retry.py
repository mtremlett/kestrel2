"""R-RUNNER-391: an order the desk itself cancelled at 0 filled is sent once more as <id>-r1."""

from __future__ import annotations

from contextlib import nullcontext
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from desk import book
from desk.broker import Crash, Fault, Pretend
from desk.halt import Stopped
from desk.lines import Line
from desk.orders import Order, Settings
from desk.store import Bar

A, MON, ROOM = Line("A", "LSE", "GBP", 1), date(2025, 11, 10), Settings(Decimal(10_000))


def _stranded(fault: Fault) -> tuple[Pretend, Order]:
    bar = Bar(MON, Decimal(50), Decimal(51), Decimal(49), Decimal(51), 1)
    broker, order = (
        Pretend({A: (bar,)}, {"A": fault}),
        Order("o-1", A, 10, *map(Decimal, (50, 1, 45))),
    )
    broker.open(MON)
    with pytest.raises(Crash, match="died") if fault is Fault.STRAND else nullcontext():
        broker.place(order)
    return broker, order


def test_only_the_desks_own_nil_fill_cancel_is_sent_once_more(tmp_path: Path) -> None:
    today = datetime.now(UTC).date()
    broker, order = _stranded(Fault.STRAND)
    assert book.cancel_all(tmp_path, broker, today) == ("o-1",)
    sent = book.send(tmp_path, broker, order, ROOM)
    assert (sent.order_id, sent.filled) == ("o-1-r1", 10) and book.positions(tmp_path) == {"A": 10}
    assert book.send(tmp_path, broker, order, ROOM).order_id == "o-1-r1"
    assert broker.submitted() == ("o-1", "o-1-r1"), "once only, never an -r2"
    stranger, order = _stranded(Fault.STRAND)  #: cancelled by the broker, not by the desk
    stranger.cancel()
    assert book.send(tmp_path / "b", stranger, order, ROOM).order_id == "o-1"
    part, order = _stranded(Fault.PARTIAL)  #: a part fill is never retried, whoever cancelled
    part.cancel = lambda: ("o-1",)  # type: ignore[method-assign]
    book.cancel_all(tmp_path / "c", part, today)
    assert book.send(tmp_path / "c", part, order, ROOM).filled == 5
    assert part.submitted() == ("o-1",)
    both, _ = _stranded(Fault.PARTIAL)  #: a stop the broker cancelled with it is not kept
    both.cancel = lambda: ("o-1", "o-1-stop")  # type: ignore[method-assign]
    assert book.cancel_all(tmp_path / "d", both, today) == ("o-1", "o-1-stop")
    assert (tmp_path / "d" / "cancels.csv").read_text().split() == [f"o-1,{today}"]


def test_the_retry_is_refused_like_any_order_while_the_kill_switch_is_on(tmp_path: Path) -> None:
    broker, order = _stranded(Fault.STRAND)
    book.cancel_all(tmp_path, broker, datetime.now(UTC).date())
    book.turn(tmp_path, book.Switch.ON, datetime.now(UTC), "drill")
    with pytest.raises(Stopped, match="kill switch"):
        book.send(tmp_path, broker, order, ROOM)
    assert broker.submitted() == ("o-1",)
