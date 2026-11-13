"""kill - THE KILL SWITCH (EMG-02): one command, and the desk sends no new order, the broker
cancels every order of the desk's still working, and the desk says so. The stops resting at
the broker stay: nothing held is left unprotected. THE DRILL pulls the switch for real on a
rehearsal desk at the pretend broker; only one that kept every promise goes on the record."""

from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

from desk import book
from desk.book import Switch
from desk.broker import Broker, Crash, Fault, Pretend
from desk.lines import Line
from desk.orders import Order, Refused, Sale, Settings
from desk.store import Bar

DRILL_DAYS = 31  #: a drill counts on its own day and this many after: one a month (EMG-02)


class Failed(Exception):
    """A drill of the kill switch broke a promise: it is not on the record as a drill."""


@dataclass(frozen=True)
class Killed:
    """What the desk says once the switch is pulled."""

    at: datetime
    why: str
    cancelled: tuple[str, ...]  #: the working orders the broker cancelled, by the desk's ids
    held: tuple[tuple[str, int], ...]  #: the book: each line still held, and its shares
    differ: tuple[str, ...]  #: the lines on which the book is not the broker's, stops included

    def words(self) -> str:
        """One message, in plain English, for whoever must be told."""
        names = f": {', '.join(self.cancelled)}" if self.cancelled else ""
        held = ", ".join(f"{symbol} {shares}" for symbol, shares in self.held) or "nothing"
        agree = (
            f"The book is NOT the broker's on {', '.join(self.differ)}: its shares, or its stop."
            if self.differ
            else "The book is the broker's, and each line held is under its stop there."
        )
        return (
            f"KILL SWITCH ON since {self.at:%Y-%m-%d %H:%M} UTC ({self.why}). The desk sends no "
            f"order until it is released. The broker cancelled {len(self.cancelled)} still "
            f"working{names}. Still held: {held}. {agree}"
        )


def pull(root: Path, broker: Broker, at: datetime, why: str) -> Killed:
    """THE ONE COMMAND. The switch goes on the record first, so the send path sends nothing
    from then on even if the broker cannot be reached; then the broker cancels what is still
    working; then the book is set against the broker's. A broker that cannot answer is an
    error raised, with the switch on. Pulled again, it does all of it again; pulled with no
    reason it still stops the desk, and says none was given."""
    why = why.strip() or "no reason given"
    book.turn(root, Switch.ON, at, why)
    cancelled = tuple(broker.cancel())
    differ = book.reconcile(root, broker)
    return Killed(at, why, cancelled, tuple(book.positions(root).items()), differ)


def release(root: Path, at: datetime, why: str) -> None:
    """The switch turned off, so the desk sends again: the operator's act alone, with his
    reason. Nothing in the desk calls it for itself."""
    if book.killed(root) is None:
        raise ValueError(f"the kill switch is not on: nothing to release at {at} for {why!r}")
    book.turn(root, Switch.OFF, at, why)


def drill(root: Path, at: datetime) -> tuple[str, ...]:
    """THE DRILL: every promise of the switch, tried on a rehearsal desk at the pretend
    broker. If all were kept the drill goes on this desk's record, dated, and they are
    named; one broken is an error naming it, and no drill is recorded."""
    with TemporaryDirectory() as scratch:
        promises = _rehearse(Path(scratch), at)
    broken = [promise for promise, kept in promises.items() if not kept]
    if broken:
        raise Failed(f"the kill switch's drill at {at:%Y-%m-%d %H:%M} UTC broke: {broken}")
    book.turn(root, Switch.DRILLED, at, "; ".join(promises))
    return tuple(promises)


def drilled(root: Path, day: date) -> bool:
    """A drill that kept every promise is on the record, made on day or in the DRILL_DAYS
    before it. The paper lane sends no order without one."""
    return any(
        to is Switch.DRILLED and 0 <= (day - at.date()).days <= DRILL_DAYS
        for at, to, _ in book.switch(root)
    )


def _rehearse(desk: Path, at: datetime) -> dict[str, bool]:
    """A desk that holds one line under its stop and died leaving a second order working;
    the switch is pulled, two orders are tried, the next market opens, and it is released.
    Each promise, and whether it was kept."""
    held, working, new = (Line(f"DRILL{n}", "LSE", "GBP", 1) for n in (1, 2, 3))
    today, room = at.date(), Settings(Decimal(10_000))
    days = (today, today + timedelta(days=1))
    bars = tuple(Bar(day, Decimal(50), Decimal(51), Decimal(49), Decimal(51), 1) for day in days)
    broker = Pretend({line: bars for line in (held, working, new)}, {working.symbol: Fault.STRAND})

    def buy(order_id: str, line: Line) -> Order:
        return Order(order_id, line, 10, Decimal(50), Decimal(1), Decimal(45))

    broker.open(today)
    book.send(desk, broker, buy("drill-held", held), room)
    with suppress(Crash):  #: the rehearsal's desk dies here, its order left working
        book.send(desk, broker, buy("drill-working", working), room)
    said = pull(desk, broker, at, "the drill")
    orders = (buy("drill-buy", new), Sale("drill-sale", held, 10))
    answers = [_answer(desk, broker, order, room) for order in orders]
    reached = broker.submitted()
    broker.open(days[1])
    still = ((held.symbol, 10),)
    after = (broker.holdings(), broker.stops(), book.reconcile(desk, broker))
    release(desk, at, "the drill is over")
    return {
        "the order left working was cancelled, and named": said.cancelled == ("drill-working",),
        "a new buy was refused, the switch given as the reason": "kill switch" in answers[0],
        "a sale was refused, the switch given as the reason": "kill switch" in answers[1],
        "nothing more reached the broker": reached == ("drill-held", "drill-working"),
        "the cancelled order never filled": after[0] == still == said.held,
        "the stop still rests for the shares held": after[1:] == (still, ()) and not said.differ,
        "the desk said so": all(word in said.words() for word in ("ON", "drill-working")),
        "released, the desk sends again": _answer(desk, broker, orders[0], room) == "sent",
    }


def _answer(desk: Path, broker: Broker, order: Order | Sale, room: Settings) -> str:
    """What the send path did with the order: "sent", or its refusal in its own words."""
    try:
        book.send(desk, broker, order, room)
    except Refused as refusal:
        return str(refusal)
    return "sent"
