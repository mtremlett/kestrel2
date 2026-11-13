"""book: every order sent once, its fills written under the broker's ids, and the book, which
the gate reads, built from every fill. Scene 4 holds the gate's refusal and a crash's restart."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from desk import book
from desk.broker import Crash, Fault, Pretend
from desk.lines import Line
from desk.orders import Order, Refused, Settings
from desk.store import Bar

A, MON, TUE = Line("A", "LSE", "GBP", 1), date(2025, 11, 10), date(2025, 11, 11)
SIX, ROOM = (A, *(Line(symbol, "LSE", "GBP", 1) for symbol in "BCDEF")), Settings(Decimal(10_000))


def _bar(day: date, low: int) -> Bar:
    return Bar(day, Decimal(50), Decimal(51), Decimal(low), Decimal(51), 1)


WEEK = {line: (_bar(MON, 49), _bar(TUE, 44 if line == A else 49)) for line in SIX}  #: A's stop: 45


def _send(root: Path, broker: Pretend, name: str = "o-1", line: Line = A, n: int = 10) -> book.Sent:
    return book.send(root, broker, Order(name, line, n, *map(Decimal, (50, 1, 45))), ROOM)


def test_an_order_the_broker_already_has_is_recorded_not_judged_again(tmp_path: Path) -> None:
    broker = Pretend(WEEK, {"A": Fault.CRASH})
    broker.open(MON)
    with pytest.raises(Crash):
        _send(tmp_path, broker)
    order = Order("o-1", A, 10, *map(Decimal, (50, 1, 45)))
    assert book.send(tmp_path, broker, order, Settings(Decimal(1))).filled == 10, "fills unwritten"


@pytest.mark.parametrize("fault", [None, Fault.REJECT, Fault.PARTIAL, Fault.DISCONNECT])
def test_an_order_is_sent_once_its_fault_stated_and_only_a_lost_one_sent_again(
    tmp_path: Path, fault: Fault | None
) -> None:
    broker = Pretend(WEEK, {} if fault is None else {"A": fault})
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


def test_the_book_is_every_fill_the_broker_made_and_the_gate_reads_it(tmp_path: Path) -> None:
    broker = Pretend(WEEK, {})
    broker.open(MON)
    for n, line in enumerate(SIX[:5]):
        _send(tmp_path, broker, f"o-{n}", line)
    with pytest.raises(Refused, match="5 holdings already"):
        _send(tmp_path, broker, "o-5", SIX[5])
    with pytest.raises(Refused, match="a fifth"):  #: 40 shares of A at 50, and 3 commission
        _send(tmp_path, broker, "o-6", n=30)
    broker.open(TUE)  #: A's stop sells it: a sale in no order's answer
    assert book.positions(tmp_path) == {s: 10 for s in "ABCDE"}, "learned of the sale untold"
    assert _send(tmp_path, broker, "o-7", SIX[5]).filled == 10, "a sold line still held"
    broker.inject("A", 7)
    book.collect(tmp_path, broker)
    assert book.fills(tmp_path) == broker.fills(), "a fill missed, or written twice"
    assert book.positions(tmp_path) == {s: 10 for s in "BCDEF"}, "a book not built from fills"
    assert "o-5" not in broker.submitted() and "o-6" not in broker.submitted()
    ledger = "execution_id,order_id,symbol,quantity,price\nX1,o-1,A,-1,50\n"
    (tmp_path / book.LEDGER).write_text(ledger, encoding="utf-8")
    with pytest.raises(ValueError, match="A"):
        book.positions(tmp_path)
