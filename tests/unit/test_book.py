"""book: every order sent once however often the desk asks, and its fills written under the
broker's own ids. Scene 4 holds the gate's refusal and the restart after a crash."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from desk import book
from desk.broker import Crash, Fault, Pretend
from desk.lines import Line
from desk.orders import Order, Settings
from desk.store import Bar

A, MON = Line("A", "LSE", "GBP", 1), date(2025, 11, 10)
ARCHIVE = {A: (Bar(MON, Decimal(50), Decimal(51), Decimal(49), Decimal(51), 1),)}
ROOM = Settings(Decimal(10_000))


def _send(root: Path, broker: Pretend, order_id: str = "o-1", room: Settings = ROOM) -> book.Sent:
    order = Order(order_id, A, 10, Decimal(50), Decimal(1), Decimal(45))
    return book.send(root, broker, order, room)


def test_an_order_the_broker_already_has_is_recorded_not_judged_again(tmp_path: Path) -> None:
    broker = Pretend(ARCHIVE, {"A": Fault.CRASH})
    broker.open(MON)
    with pytest.raises(Crash):
        _send(tmp_path, broker)
    assert _send(tmp_path, broker, room=Settings(Decimal(1))).filled == 10, "fills left unwritten"


@pytest.mark.parametrize("fault", [None, Fault.REJECT, Fault.PARTIAL, Fault.DISCONNECT])
def test_an_order_is_sent_once_its_fault_stated_and_only_a_lost_one_sent_again(
    tmp_path: Path, fault: Fault | None
) -> None:
    broker = Pretend(ARCHIVE, {} if fault is None else {"A": fault})
    broker.open(MON)
    sent = _send(tmp_path, broker)
    assert (sent.reason is None) == (fault is None)
    assert sent.reason is None or "o-1" in sent.reason
    assert sent.filled == {None: 10, Fault.PARTIAL: 5}.get(fault, 0)
    assert len(broker.submitted()) == (fault is not Fault.DISCONNECT)
    assert book.fills(tmp_path) == broker.fills()
    again = [_send(tmp_path, broker), _send(tmp_path, broker, "o-2"), _send(tmp_path, broker)]
    assert broker.submitted() == ("o-1", "o-2"), "an order the broker had was sent twice"
    assert (
        again[0] == again[2] == (book.Sent("o-1", 10, None) if fault is Fault.DISCONNECT else sent)
    )
    assert book.fills(tmp_path) == broker.fills() and again[1].filled == 10
