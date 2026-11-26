"""R-PAPER-11: a place whose word, fills and account do not agree halts buying, tells him once,
and the order that has gone is never sent again; a sale still goes."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from desk import book, halt
from desk.broker import Pretend, Report
from desk.halt import Stopped
from desk.lines import Line
from desk.orders import Order, Sale, Settings
from desk.placing import Unprotected
from desk.store import Bar

A, MON = Line("A", "LSE", "GBP", 1), date(2025, 11, 10)


def test_a_place_that_disagrees_halts_buying_tells_him_once_and_a_sale_still_goes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bar = Bar(MON, Decimal(50), Decimal(51), Decimal(49), Decimal(51), 1)
    broker, quiet, told = Pretend({A: (bar,)}, {}), Pretend({A: (bar,)}, {}), []
    broker.open(MON)
    quiet.open(MON)

    def disagree(broker: Pretend) -> Callable[[Order | Sale], Report]:
        place = broker.place

        def placed(order: Order | Sale) -> Report:
            place(order)  #: the order has gone, then the door finds the account does not agree
            raise Unprotected("o-1: these do not agree")

        return placed

    monkeypatch.setattr(broker, "place", disagree(broker))
    monkeypatch.setattr(quiet, "place", disagree(quiet))
    buy, room = Order("o-1", A, 10, *map(Decimal, (50, 1, 45))), Settings(Decimal(10_000))
    with pytest.raises(book.Alarm):  #: with no one to tell, the kill switch's alarm stands
        book.send(tmp_path / "quiet", quiet, buy, room)
    sent = book.send(tmp_path, broker, buy, room, lambda name, words: told.append((name, words)))
    assert sent.filled == 10
    assert len(halt.in_force(tmp_path)) == 1 and book.killed(tmp_path) is None
    assert (
        [name for name, _ in told] == ["disagree o-1"]
        and "o-1" in told[0][1]
        and "do not agree" in told[0][1]
    )
    assert book.positions(tmp_path) == {"A": 10}, "fills unwritten"
    assert not (tmp_path / book.GOING).exists(), "the order is recorded as gone"
    monkeypatch.undo()
    assert book.send(tmp_path, broker, buy, room).order_id == "o-1"  #: asked, never sent again
    assert broker.submitted() == ("o-1",) and len(told) == 1
    with pytest.raises(Stopped, match="halt is in force"):
        book.send(tmp_path, broker, Order("o-2", A, 1, *map(Decimal, (50, 1, 45))), room)
    book.send(tmp_path, broker, Sale("s-1", A, sent.filled), room)
    assert broker.submitted() == ("o-1", "s-1")


def test_a_stranger_under_a_working_broker_stop_is_not_sold_on_top_of_it() -> None:
    """R-RUNNER-517: shares the book lacks that sit under the desk's stop at the broker are left
    to it (deep SimCity's world 4 sold them twice); one share more than the stop covers is not."""
    broker = Pretend({A: ()}, {})
    broker.inject("Z", 5)
    broker.inject("Y", 7)
    broker.put_stop_back("Z", Decimal(40))
    broker.put_stop_back("Y", Decimal(40))
    broker.inject("Y", 2)
    assert dict(book.strangers(Path("none"), broker)) == {"Y": 2}, "Z is stopped, Y's 2 are bare"
