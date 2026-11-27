"""book.send's fault matrix (failure pattern 23; design L8): every kind of answer the broker's door
can give, at every moment of a send, in one table. Whatever breaks, an order the broker received is
never forgotten (its fills are in the book, its note is kept for the next send, or the kill switch
is on), and the send that follows never buys it twice."""

from __future__ import annotations

from contextlib import suppress
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from desk import book
from desk.broker import Crash, Disconnected, Pretend, Report
from desk.halt import Stopped
from desk.lines import Line
from desk.orders import Order, Sale, Settings
from desk.store import Bar

A, MON = Line("A", "LSE", "GBP", 1), date(2025, 11, 10)
ROOM = Settings(Decimal(10_000))
#: the broker's door is asked these, in this order, by one send
MOMENTS = ("report", "holdings", "stops", "before place", "after place", "fills")
#: every kind of answer the door can give instead of the one asked for
ANSWERS = (
    Disconnected("the link dropped"),
    Crash("the desk died"),
    TimeoutError("no answer in time"),
    RuntimeError("a gateway word the desk does not know"),
)


class Door(Pretend):
    """The pretend broker, its door breaking once at one moment with one answer."""

    def __init__(self, moment: str, answer: Exception) -> None:
        bar = Bar(MON, Decimal(50), Decimal(51), Decimal(49), Decimal(51), 1)
        super().__init__({A: (bar,)}, {})
        self.moment, self.answer = moment, answer

    def _break(self, moment: str) -> None:
        if self.moment == moment:
            self.moment = ""
            raise self.answer

    def report(self, order_id: str) -> Report | None:
        self._break("report")
        return super().report(order_id)

    def holdings(self) -> tuple[tuple[str, int], ...]:
        self._break("holdings")
        return super().holdings()

    def stops(self) -> Any:  # noqa: ANN401 - the pretend's own answer, passed through
        self._break("stops")
        return super().stops()

    def place(self, order: Order | Sale) -> Report:
        self._break("before place")
        report = super().place(order)
        self._break("after place")
        return report

    def fills(self) -> Any:  # noqa: ANN401 - the pretend's own answer, passed through
        self._break("fills")
        return super().fills()


def _send(root: Path, broker: Door) -> None:
    order = Order("o-1", A, 10, *map(Decimal, (50, 1, 45)))
    with suppress(Disconnected, Crash, TimeoutError, RuntimeError, book.Alarm):  #: the table's
        book.send(root, broker, order, ROOM)  #: input: the invariants judge what it left


@pytest.mark.parametrize("answer", ANSWERS, ids=lambda a: type(a).__name__)
@pytest.mark.parametrize("moment", MOMENTS)
def test_an_order_the_broker_holds_is_never_forgotten_nor_bought_twice(
    tmp_path: Path, moment: str, answer: Exception
) -> None:
    broker = Door(moment, answer)
    broker.open(MON)
    _send(tmp_path, broker)
    received = "o-1" in broker.submitted()
    known = (
        any(f.order_id == "o-1" for f in book.fills(tmp_path))
        or (tmp_path / book.GOING).exists()
        or book.killed(tmp_path) is not None
    )
    assert known or not received, f"{moment}, {answer!r}: the broker holds o-1, the book forgot it"
    killed = book.killed(tmp_path) is not None
    try:  #: the next send: the order once, or, with the switch on, nothing new
        _send(tmp_path, broker)
    except Stopped as stopped:
        assert killed and "kill switch" in str(stopped), f"{moment}, {answer!r}: {stopped}"
    book.collect(tmp_path, broker)
    bought = sum(f.quantity for f in broker.fills() if f.symbol == "A" and f.quantity > 0)
    assert bought in ((0, 10) if killed else (10,)), f"{moment}, {answer!r}: {bought} of 10 bought"
    assert broker.submitted().count("o-1") <= 1, f"{moment}, {answer!r}: o-1 sent twice"
    assert book.fills(tmp_path) == broker.fills(), f"{moment}, {answer!r}: book is not the broker's"
