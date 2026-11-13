"""book: every order sent once, its fills written under the broker's ids, and the book, which
the gate reads, built from every fill. Scene 4 holds the gate's refusal and a crash's restart."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from desk import book
from desk.broker import Broker, Crash, Fault, Pretend
from desk.lines import STAMP_DUTY, Line
from desk.orders import Charges, Order, Refused, Sale, Settings
from desk.store import Bar

A, MON, TUE = Line("A", "LSE", "GBP", 1), date(2025, 11, 10), date(2025, 11, 11)
SIX, ROOM = (A, *(Line(symbol, "LSE", "GBP", 1) for symbol in "BCDEF")), Settings(Decimal(10_000))


def _bar(day: date, low: int) -> Bar:
    return Bar(day, Decimal(50), Decimal(51), Decimal(low), Decimal(51), 1)


WEEK = {line: (_bar(MON, 49), _bar(TUE, 44 if line == A else 49)) for line in SIX}  #: A's stop: 45


def _send(root: Path, broker: Broker, name: str = "o-1", line: Line = A, n: int = 10) -> book.Sent:
    return book.send(root, broker, Order(name, line, n, *map(Decimal, (50, 1, 45))), ROOM)


def test_an_order_the_broker_already_has_is_recorded_not_judged_again(tmp_path: Path) -> None:
    broker = Pretend(WEEK, {"A": Fault.CRASH})
    broker.open(MON)
    with pytest.raises(Crash):
        _send(tmp_path, broker)
    order = Order("o-1", A, 10, *map(Decimal, (50, 1, 45)))
    broker.inject("B", 1)  #: nor refused while the books differ: the broker has it
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
    lost = fault is Fault.DISCONNECT
    assert again[0] == again[2] == (book.Sent("o-1", 10, None) if lost else sent)
    assert book.fills(tmp_path) == broker.fills() and again[1].filled == 10


def test_the_book_is_every_fill_the_broker_made_and_the_gate_reads_it(tmp_path: Path) -> None:
    broker = Pretend(WEEK, {"E": Fault.CRASH})  #: E's fill is the broker's, not yet the desk's
    broker.open(MON)
    for n, line in enumerate(SIX[:4]):
        _send(tmp_path, broker, f"o-{n}", line)
    with pytest.raises(Crash):
        _send(tmp_path, broker, "o-4", SIX[4])
    with pytest.raises(Refused, match="5 holdings already"):
        _send(tmp_path, broker, "o-5", SIX[5])
    with pytest.raises(Refused, match="a fifth"):  #: 40 shares of A at 50, and 3 commission
        _send(tmp_path, broker, "o-6", n=30)
    broker.open(TUE)  #: A's stop sells it: a sale in no order's answer
    assert _send(tmp_path, broker, "o-7").filled == 10, "a line its stop sold still held"
    assert book.positions(tmp_path) == {s: 10 for s in "BCDE"}, "the day's own stop unwritten"
    _send(tmp_path, broker, "o-8", SIX[5])
    broker.inject("A", 7)
    book.collect(tmp_path, broker)
    assert book.fills(tmp_path) == broker.fills(), "a fill missed, or written twice"
    assert book.positions(tmp_path) == {s: 10 for s in "BCDEF"}, "a book not built from fills"
    (tmp_path / book.LEDGER).write_text(
        ",".join(book.COLUMNS) + "\nX,o,A,-1,5,2025-11-10\n", "utf-8"
    )
    with pytest.raises(ValueError, match="A"):
        book.positions(tmp_path)


def test_while_the_book_is_not_the_brokers_nothing_is_bought_and_no_such_line_sold(
    tmp_path: Path,
) -> None:
    broker = Pretend(WEEK, {})
    broker.open(MON)
    for n, line in enumerate(SIX[:3]):
        _send(tmp_path, broker, f"o-{n}", line)
    assert book.reconcile(tmp_path, broker) == ()
    broker.inject("E", 7)  #: bought by hand, and three more of A
    broker.inject("A", 3)
    assert book.reconcile(tmp_path, broker) == ("A", "E")
    with pytest.raises(Refused, match=r"o-3: .*\['A', 'E'\]"):
        _send(tmp_path, broker, "o-3", SIX[3])
    with pytest.raises(Refused, match="s-0: .*not the broker's"):
        book.send(tmp_path, broker, Sale("s-0", A, 10), ROOM)
    assert book.send(tmp_path, broker, Sale("s-1", SIX[1], 10), ROOM).filled == 10, "B agrees"
    assert broker.submitted() == ("o-0", "o-1", "o-2", "s-1"), "sent while the books differ"
    broker.inject("E", -7)
    broker.inject("A", -3)
    assert _send(tmp_path, broker, "o-3", SIX[3], 1).filled == 1, "the books agree again"
    broker.open(TUE)  #: A's stop sells it: the ledger learns of it before the books are compared
    assert book.reconcile(tmp_path, broker) == () and "A" not in book.positions(tmp_path)
    broker.cancel_stop("C")
    assert book.reconcile(tmp_path, broker) == ("C",), "a held line with no stop resting"
    with pytest.raises(Refused, match=r"o-4: .*\['C'\]"):
        _send(tmp_path, broker, "o-4", SIX[4])
    assert book.send(tmp_path, broker, Sale("s-2", SIX[2], 10), ROOM).filled == 10, "unprotected"
    broker.inject("D", -1)  #: all of D sold by hand and its stop cancelled: only the book has it
    broker.cancel_stop("D")
    assert book.reconcile(tmp_path, broker) == ("D",)
    with pytest.raises(Refused, match="s-3"):
        book.send(tmp_path, broker, Sale("s-3", SIX[3], 1), ROOM)
    broker.place(Order("x-1", SIX[5], 10, *map(Decimal, (50, 1, 45))))
    broker.cancel_stop("F")
    broker.place(Order("x-2", SIX[5], 5, *map(Decimal, (50, 1, 45))))  #: F's stop: 5 of its 15
    assert book.reconcile(tmp_path, broker) == ("D", "F"), "a stop for fewer shares than held"
    for line in SIX:
        broker.inject(line.symbol, 1)
    assert book.reconcile(tmp_path, broker) == tuple("ABCDEF"), "named in no order"


def test_while_the_kill_switch_is_on_nothing_is_sent_and_every_refusal_says_why(
    tmp_path: Path,
) -> None:
    broker = Pretend(WEEK, {"B": Fault.CRASH})
    broker.open(MON)
    _send(tmp_path, broker)
    with pytest.raises(Crash):  #: the broker has o-2 and the desk has no answer yet
        _send(tmp_path, broker, "o-2", SIX[1])
    at = datetime(2025, 11, 10, 9, 30, tzinfo=UTC)
    book.turn(tmp_path, book.Switch.DRILLED, at, "a drill is not a pull")
    assert book.killed(tmp_path) is None
    book.turn(tmp_path, book.Switch.ON, at, "his word")
    book.turn(tmp_path, book.Switch.DRILLED, at, "nor is it a release")
    for order in (Order("o-3", SIX[2], 10, *map(Decimal, (50, 1, 45))), Sale("s-1", A, 10)):
        with pytest.raises(Refused, match=f"{order.order_id}: .*kill switch.*09:30 UTC: his word"):
            book.send(tmp_path, broker, order, ROOM)
    assert broker.submitted() == ("o-1", "o-2"), "sent while the kill switch was on"
    assert _send(tmp_path, broker, "o-2", SIX[1]).filled == 10, "what the broker did, unrecorded"
    broker.open(TUE)  #: A's stop sells: the ledger still learns of it
    book.collect(tmp_path, broker)
    assert book.positions(tmp_path) == {"B": 10}
    book.turn(tmp_path, book.Switch.OFF, at, "his word again")
    assert _send(tmp_path, broker, "o-3", SIX[2]).filled == 10, "off, and still nothing sent"
    assert [(to.value, why) for when, to, why in book.switch(tmp_path) if when == at] == [
        ("drilled", "a drill is not a pull"),
        ("on", "his word"),
        ("drilled", "nor is it a release"),
        ("off", "his word again"),
    ], "the record does not read back as it was written"
    for when, why in ((datetime(2025, 11, 10, 9, 30), "no zone"), (at, " ")):
        with pytest.raises(ValueError, match="kill switch"):
            book.turn(tmp_path, book.Switch.ON, when, why)
    door = Account(broker)  #: pulled while the broker is answering the send path
    door.between.append(lambda: book.turn(tmp_path, book.Switch.ON, at, "as it answered"))
    with pytest.raises(Refused, match="o-4: .*kill switch.*as it answered"):
        _send(tmp_path, door, "o-4", SIX[3])
    assert broker.submitted() == ("o-1", "o-2", "o-3"), "sent after the switch was pulled"
    stamp = "2025-11-10T09:30:00"
    for torn in ("", f"{stamp}+00:00,on,x\n", f"at,turn,why\n{stamp},on,x\n", "at,turn,why\n\n"):
        (tmp_path / book.SWITCH).write_text(torn, "utf-8")
        with pytest.raises(ValueError):  #: a record that cannot be read never reads as off
            _send(tmp_path, broker, "o-4", SIX[3])


class Account:
    """Any broker, not the pretend one by name: its rows as a real account's door gives them,
    and each reading of them counted."""

    def __init__(self, inner: Pretend) -> None:
        self.report, self.place, self.fills = inner.report, inner.place, inner.fills
        self.cancel = inner.cancel
        self.inner, self.read, self.between = inner, 0, list[Callable[[], None]]()
        self.rows, self.resting = (list[tuple[str, Decimal | int]]() for _ in range(2))

    def holdings(self) -> Iterable[tuple[str, Decimal | int]]:
        self.read += 1
        return self._then(self.rows or self.inner.holdings())

    def stops(self) -> Iterable[tuple[str, Decimal | int]]:
        return self._then(self.resting or self.inner.stops())

    def _then(
        self, answer: Iterable[tuple[str, Decimal | int]]
    ) -> Iterable[tuple[str, Decimal | int]]:
        """Give the answer; whatever waits between two readings happens after the first."""
        while self.between:
            self.between.pop()()
        return answer


def test_any_broker_stands_behind_the_send_path_its_rows_read_once_and_never_added(
    tmp_path: Path,
) -> None:
    pretend = Pretend(WEEK, {})
    pretend.open(MON)
    door = Account(pretend)
    assert _send(tmp_path, door).filled == 10 and door.read == 1, "one order, two readings"
    for second in (Decimal(4), 10):  #: two entries are never added up to the book's ten,
        door.rows = [("A", 6), ("A", second)]  #: nor is the first dropped for the second
        assert book.reconcile(tmp_path, door) == ("A",)
    with pytest.raises(Refused, match="s-1"):
        book.send(tmp_path, door, Sale("s-1", A, 10), ROOM)
    door.rows = [("A", 10), ("A CFD", 3)]  #: another product under A's name is not the line
    with pytest.raises(Refused, match=r"o-2: .*\['A CFD'\]"):
        _send(tmp_path, door, "o-2", SIX[1])
    assert book.send(tmp_path, door, Sale("s-2", A, 10), ROOM).filled == 10, "A's shares agree"
    assert door.read == 6, "the broker's holdings read more than once for an order"
    door.rows = []
    assert _send(tmp_path, door, "o-3").filled == 10
    for second in (Decimal(4), 10):  #: nor are two stops added up, or one dropped
        door.resting = [("A", 6), ("A", second)]
        assert book.reconcile(tmp_path, door) == ("A",)
    door.resting = []
    door.between.append(lambda: pretend.open(TUE))  #: A's stop sells while the broker is read
    with pytest.raises(Refused, match=r"s-3: .*\['A'\]"):  #: or its sale would sell A short
        book.send(tmp_path, door, Sale("s-3", A, 10), ROOM)


@pytest.mark.parametrize(
    ("held", "entries", "named"),
    [
        ({"A": 25}, [("A", Decimal(25)), ("B", 0), ("B", 0)], []),  #: listed at no shares: not held
        ({}, [("A", 25)], [("A", 25, 0)]),
        ({"A": 25}, [], [("A", 0, 25)]),
        ({"A": 25}, [("A", 0)], [("A", 0, 25)]),
        ({"A": 25, "B": 4}, [("B", 5), ("A", -25)], [("A", -25, 25), ("B", 5, 4)]),
        ({}, [("A", Decimal("0.5"))], [("A", Decimal("0.5"), 0)]),
        #: entries that only add up to the book are two places, or a change while it was read
        ({"A": 25}, [("A", 20), ("A", 5)], [("A", 5, 25), ("A", 20, 25)]),
        ({"A": 25}, [("A", 25), ("A", 0)], [("A", 0, 25)]),
        ({}, [("A", 25), ("A", 0), ("A", -25)], [("A", -25, 0), ("A", 25, 0)]),
        ({"A": 25}, [("A", 25), ("A", 25)], [("A", 25, 25)] * 2),  #: fifty, in two places
        ({"A": 25}, [("A", 25), ("A", 5)], [("A", 5, 25), ("A", 25, 25)]),
    ],
)
def test_every_entry_of_the_brokers_is_the_books_own_shares_or_it_is_named(
    held: dict[str, int],
    entries: list[tuple[str, Decimal | int]],
    named: list[tuple[str, Decimal | int, int]],
) -> None:
    assert book.differences(held, iter(entries)) == tuple(book.Difference(*n) for n in named)


def test_a_round_trip_pairs_each_sale_with_the_buys_it_closes_in_pounds_after_every_cost(
    tmp_path: Path,
) -> None:
    dollar, share = Line("U", "US", "USD", 1), replace(A, uk_tax=STAMP_DUTY)
    broker = Pretend({**WEEK, dollar: WEEK[SIX[1]]}, {})
    for on, rate in ((MON, "0.8"), (TUE, "0.75")):
        broker.open(on)
        book.record_rates(tmp_path, on, {"GBP": Decimal(1), "USD": Decimal(rate)})
        if on == MON:
            _send(tmp_path, broker)
            book.send(
                tmp_path, broker, Order("o-2", dollar, 10, *map(Decimal, (50, 0.8, 45))), ROOM
            )
            book.send(tmp_path, broker, Sale("s-1", A, 4), ROOM)
    book.send(tmp_path, broker, Sale("s-2", dollar, 10), ROOM)  #: after A's stop sold the rest
    trips = book.round_trips(tmp_path, (share, dollar))
    assert [(t.sell.order_id, t.buy.quantity, t.sell.quantity) for t in trips] == [
        ("s-1", 4, -4),
        ("o-1-stop", 6, -6),
        ("s-2", 10, -10),
    ]
    assert {t.buy.execution_id for t in trips[:2]} == {broker.fills()[0].execution_id}
    #: each leg's costs shared by its shares: 3 pounds a London order, 0.05% of each leg to the
    #: spread and to slippage, three times that as the stop sells at 45, and the buy's tax
    assert [(t.gross, t.costs) for t in trips[:2]] == [
        (Decimal(0), Charges(*map(Decimal, ("4.2", "0.2", "0.2", "0", "1")))),
        (Decimal(-30), Charges(*map(Decimal, ("4.8", "0.285", "0.555", "0", "1.5")))),
    ]
    #: 500 dollars at 0.8, back at 0.75: a dollar's commission each way and the regulators'
    #: 1.225 cents on the sale; 0.03% conversion on the dollars moved each way
    conversion = Decimal("0.0003") * (501 * Decimal("0.8") + Decimal("498.98775") * Decimal("0.75"))
    assert trips[2].gross == -25 and trips[2].costs == Charges(
        Decimal("1.5591875"), Decimal("0.3875"), Decimal("0.3875"), conversion, Decimal(0)
    )
    assert [t.profit for t in trips[:2]] == [Decimal("-5.6"), Decimal("-37.14")], "every line off"
    assert trips[2].profit == trips[2].gross - trips[2].costs.total
    #: a day's dealing is its own fills' money and costs, at its own rate: here, every trip's
    (out, mon), (back, tue) = (book.dealt(tmp_path, (share, dollar), on) for on in (MON, TUE))
    assert out == -700 and back == 645
    assert mon + tue == trips[0].costs + trips[1].costs + trips[2].costs
    assert book.positions(tmp_path, MON) == {"A": 6, "U": 10} and book.positions(tmp_path) == {}
    days = (MON, TUE, date(2025, 11, 14))  #: a day's rate is the newest kept on or before it
    assert [str(book.rate(tmp_path, "USD", on)) for on in days] == ["0.8", "0.75", "0.75"]
    with pytest.raises(ValueError, match="USD"):
        book.rate(tmp_path, "USD", date(2025, 11, 7))
    with pytest.raises(ValueError, match="U"):
        book.round_trips(tmp_path, (A,))
    with pytest.raises(ValueError, match="kept at 0.75"):  #: a day's fills are never repriced
        book.record_rates(tmp_path, TUE, {"USD": Decimal("0.76")})
    for wrong in ({"GBP": Decimal("0.9")}, {"USD": Decimal(0)}):
        with pytest.raises(ValueError, match="a rate of"):
            book.record_rates(tmp_path, date(2025, 11, 12), wrong)
