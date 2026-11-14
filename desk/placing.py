"""placing - THE PAPER ACCOUNT BEHIND THE SEND PATH: what the desk asks of any broker
(broker.Broker), answered by the paper account through the one door (desk/paper.py): what
the broker did with an order, the desk's fills, what the account holds, the stops resting on
it, the kill switch's cancel, and the placing of an order. NO BUY GOES WITHOUT ITS STOP: the
two are sent together, the stop to wait on the buy, so the broker holds it from the moment
it has the buy; and after any order the line is left under one stop of the desk's own, for
the shares the account then holds of it, once the broker's word, its fills and the account's
shares agree.

Each answer is read from the gateway afresh, in a conversation of its own. The fills, the
open orders and the stops are the desk's own alone (desk/reports.py): anyone else's is not
the desk's, and the day's check names it (desk/clearance.py). The holdings are the whole
account's; an ended order is known by its reference alone, for the broker's list of them
names no client. An answer that cannot be read whole is an error raised. The broker tells
of the day alone: an order or a fill of an earlier day is in the desk's ledger, or nowhere.

Two things are sent that are no question. An order, by `place` alone: after the kill
switch was drilled (kill.drilled), the day's check came back clean (clearance.require), the
gateway said it is ready (gateway.known) and the broker lists no other order open (`_before`);
and the stop a line is left under (`settle`), by `place` and, after a restart, by
desk/running.py. And a cancel, for an order of the desk's own: by the kill switch, of each
still working, never a stop resting to sell what is held; by `place`, of what the broker did
not fill; and by `settle`, of a stop only once its replacement rests, or no share is left."""

from __future__ import annotations

from collections.abc import Callable, Collection, Iterator, Mapping, Sequence
from dataclasses import replace
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import BinaryIO, NamedTuple

from desk import clearance, gateway, kill, listing, paper, reports, venues
from desk.broker import Disconnected, Fill, Report
from desk.listing import Listing, Unlisted
from desk.orders import Order, Refused, Sale
from desk.paper import Resting

PLACE, CANCEL = 3, 4  #: what this module sends that is no question: an order, and a cancel
#: The rest of an order's message, after its reference: sent at once, under no other order,
#: and every one of the broker's other choices left as the published client leaves it
#: (ib_insync 0.9.86, in this version of the gateway's language; its source read, never
#: imported): no condition, no algorithm, and no "what if", which only asks.
PLAIN = (
    "1|0|0|0|0|0|0|0||0.0||||||||0||-1|0|||0|||0|0||0||||||0|||||0|||||||||||0|||0|0|||0||0|0|0|0"
    "|||||||0|||||||||0|0|0|0|||0||"
).split("|")
#: The broker's words for an order it will not work again: cancelled, or done.
GONE = frozenset({"Cancelled", "ApiCancelled"})
OVER = GONE | {"Filled"}
MARKET = ("MKT", "", "", "DAY")  #: an order's kind: at the market, no price, for the day


class Stop(NamedTuple):
    """A stop of the desk's own to sell a line's shares, resting at the broker or due there."""

    shares: Decimal
    level: Decimal  #: the price it goes at, in the broker's unit
    ref: str  #: the reference it is placed under


class NotCancelled(Exception):
    """The broker refused to cancel an order of the desk's own, and still lists it working."""


class Unprotected(Exception):
    """The desk cannot say a line is under the stop due on it: the broker ended a stop sent to
    it, or what it says of an order does not agree with the account."""


def _working(order: Resting) -> bool:
    """Whether an order of the desk's own, and no stop the broker is holding, is the kill
    switch's to cancel: not one that is over, and never a stop to sell (reports.stop_to_sell,
    the one rule for it), whose line would be left unprotected."""
    return not reports.stop_to_sell(order) and order.state not in OVER


def _told(
    wire: BinaryIO, numbers: Collection[str], states: Collection[str] = OVER
) -> Iterator[tuple[str, str, str | None]]:
    """What the gateway says, for as long as it is read, of orders of the desk's own by
    their numbers: a state one stands in, of those asked for (its number, the state, None),
    or a notice of one (its number, the notice's words, its code). What it tells meanwhile
    of the orders themselves and their fills is passed over (paper.other): the account's own
    readings give it."""
    while True:
        fields = paper.receive(wire)
        if fields[0] == paper.STATUS:
            if len(fields) != 12:
                raise ValueError(f"an order's state of a shape the desk does not read: {fields}")
            if fields[1] in numbers and fields[9] == str(paper.CLIENT) and fields[2] in states:
                yield fields[1], fields[2], None
        elif fields[0] == paper.NEWS and len(fields) > 4 and fields[2] in numbers:
            yield fields[2], fields[4], fields[3]
        else:
            paper.other(fields)


def _cancel(wire: BinaryIO, send: paper.Send, numbers: Collection[str]) -> dict[str, str]:
    """Ask over an open connection that orders of the desk's own be cancelled, each by its
    number, and read until the broker has given its last word of every one: the state it is
    over in (cancelled, or filled while the cancel was on its way), or its notice refusing
    the cancel; its notice that it cancelled one is no last word. A gateway that hangs up
    first is an error: the desk does not then know what is still working."""
    paper.start(wire, send)
    send(b"".join(paper.message(CANCEL, 1, number, "") for number in numbers))
    said: dict[str, str] = {}
    for number, word, code in _told(wire, numbers):
        if code is None:
            said[number] = word
        elif code != paper.CANCELLED:
            said.setdefault(number, f"{code}: {word}")
        if len(said) == len(numbers):
            break
    return said


def _message(
    number: str, listed: Listing, deal: Sequence[str], shares: Decimal | int, ref: str, *first: str
) -> bytes:
    """The message that places one order under a number: deal is whether it buys or sells,
    then its kind (MARKET, or a stop's). It goes to the broker's router, the line by the
    broker's own number for it, the desk's id for it its reference. first is how it is sent
    where not at once and alone (PLAIN's first two): 0, held back until an order that waits
    on it is sent; 1 and that order's number, to wait on it."""
    line, (action, *kind) = listed.line, deal
    there = (listed.contract, line.symbol, "STK", "", "0.0", "", "", listing.ROUTE, "")
    asks = (action, shares, *kind, "", "", "O", 0, ref, *first, *PLAIN[len(first) :])
    return paper.message(PLACE, number, *there, line.currency, *[""] * 4, *asks)


def _selling(number: str, listed: Listing, stop: Stop, *first: str) -> bytes:
    """The message that places a stop to sell: it goes at its level, in plain digits, and
    rests until it is cancelled."""
    deal = ("SELL", "STP", "", f"{stop.level:f}", "GTC")
    return _message(number, listed, deal, stop.shares, stop.ref, *first)


def _with(listed: Listing, order: Order) -> Stop:
    """The stop a buy goes with: for its shares, at the order's own stop put down onto the
    broker's step and into the broker's unit, under the order's id with "-stop"."""
    return Stop(Decimal(order.quantity), listed.floor(order.stop), f"{order.order_id}-stop")


def _place(
    wire: BinaryIO, send: paper.Send, listed: Listing, order: Order | Sale
) -> tuple[str, str | None, tuple[str, ...]]:
    """Send an order over an open connection, once, and read the broker's word of it: the
    number it went under, the state the broker says it is over in (filled, or cancelled), or
    None, and every notice the broker gave of it. It goes at the market, for the day, under
    the number the gateway gave at the start. A BUY GOES WITH ITS STOP (_with): the buy held
    back, and behind it, under the next number, the stop, which waits on the buy and sends
    both on. The reading ends when the order is over, or when the gateway has said nothing
    for as long as the door waits (paper.SECONDS): the order is then not over (None), and is
    the desk's to cancel. A gateway that hangs up first is an error: the order may have
    arrived."""
    first, ref, shares = paper.start(wire, send), order.order_id, order.quantity
    number, numbers = str(first), [str(first)]
    if isinstance(order, Sale):
        send(_message(number, listed, ("SELL", *MARKET), shares, ref))
    else:
        numbers.append(str(first + 1))
        buy = _message(number, listed, ("BUY", *MARKET), shares, ref, "0")
        send(buy + _selling(numbers[1], listed, _with(listed, order), "1", number))
    notices: list[str] = []
    try:
        for told, word, code in _told(wire, numbers):
            if code is not None:
                notices.append(f"{code}: {word}")
            elif told == number:
                return number, word, tuple(notices)
    except TimeoutError:  #: the door's wait ran out in silence: its answer is "not over"
        pass
    return number, None, tuple(notices)


def _rest(wire: BinaryIO, send: paper.Send, listed: Listing, stop: Stop) -> None:
    """Send a stop to sell over an open connection, alone, under the number the gateway gave
    at the start, and read until the broker says it holds it. One the broker ends instead is
    an error, with its notices; so is its silence, and a gateway that hangs up: the desk does
    not then know that the stop rests."""
    number = str(paper.start(wire, send))
    send(_selling(number, listed, stop))
    notices: list[str] = []
    for _, word, code in _told(wire, (number,), OVER | reports.HELD):
        if code is not None:
            notices.append(f"{code}: {word}")
        elif word in reports.HELD:
            return
        else:
            raise Unprotected(f"{stop.ref}: the broker ended the stop, {word}; it said: {notices}")


def _due(before: Stop | None, held: Decimal, moved: int, new: Stop | None) -> Stop | None:
    """The one stop a line is to be left under once an order has moved shares on it (bought,
    or sold: negative), or None for none: for all the shares the account then holds of it. A
    buy that bought puts it at the level and under the reference of the stop it went with
    (new); a sale, and a buy that bought none, leave it at the level and under the reference
    of the stop the line was under before, and a line under none before is given none."""
    kept = new if moved > 0 and new else before
    return kept._replace(shares=held) if kept and held > 0 else None


def on(account: paper.Account, listed: Listing) -> tuple[Decimal, list[Resting]]:
    """A line in one reading of the account: the shares the account holds of it, and the
    desk's own stops to sell open on it, held by the broker or not yet."""
    name = paper.own(listed.line)
    held = sum((h.shares for h in account.holdings if h.name == name), Decimal(0))
    stops = [
        o
        for o in account.orders
        if o.contract == listed.contract and o.state not in OVER
        if reports.ours(o.client, o.ref) and reports.stop_to_sell(o)
    ]
    return held, stops


class Paper:
    """The paper account, as a broker the send path, the day run and the kill switch can
    stand on."""

    def __init__(
        self, listings: Mapping[str, Listing | Unlisted], root: Path, clock: Callable[[], datetime]
    ) -> None:
        """listings is each of the desk's lines as the broker lists it now (listing.read): by
        them a fill, an order and a holding are known as a line's. root holds the desk's record,
        the day's checks among it; clock gives the moment, in UTC: read only before a send."""
        self._listings, self._root, self._clock = dict(listings), root, clock

    def _orders(self) -> reports.Orders:
        return reports.orders(paper.read().orders, self._listings)

    def report(self, order_id: str) -> Report | None:
        """What the broker did today with an order id, or None if it tells nothing of it. Its
        open orders are read first, then the day's ended ones, then the day's fills, so that
        an order which ends or fills between the readings is in one of them: read the other
        way round it could be in none, and be sent again. (Seen on real orders, 14 November
        2026: the ended list had each at once after its cancel, and keeps one refused on
        entry, as cancelled; a fill is still unseen.) The reason is None only for an order
        the broker lists once, ended and filled whole, with fills that come to the shares it
        says were filled; otherwise it is everything the broker says of it."""
        listed = [o for o in self._orders().unsettled if o.ref == order_id]
        ended = [e for e in reports.ended() if e.ref == order_id]
        fills = tuple(fill for fill in self.fills() if fill.order_id == order_id)
        if not (listed or ended or fills):
            return None
        done = sum(abs(fill.quantity) for fill in fills)
        whole = reports.Ended(order_id, "Filled", Decimal(done), Decimal(0))
        if fills and not listed and ended == [whole]:
            return Report(order_id, fills, None)
        said = [f"{o.state}, {o.left} shares still to be done" for o in listed]
        said += [f"{e.state}, {e.filled} shares filled and {e.left} not" for e in ended]
        told = "; ".join(said) or "nothing of the order"
        reason = f"{order_id}: the broker says {told}; its fills today come to {done} shares"
        return Report(order_id, fills, reason)

    def place(self, order: Order | Sale) -> Report:
        """Send an order to the paper broker and give its last answer (_place): what the
        broker has not ended when it falls silent is cancelled, and the answer is what the
        broker then says it did with the order (report), with the notices it gave when it
        did not fill whole. A buy goes with its stop, and whatever the broker did, the line
        is then left under the one stop due on it (_due, settle): but only once the
        account's shares of the line have moved by exactly the order's fills, and an order
        the broker called filled has fills for all its shares. Otherwise a stop has sold
        meanwhile or a reading is late: Unprotected, and the line's stops are left as they
        are. Nothing is sent, and the reason raised, unless the order is cleared to go
        (_cleared: Refused, or Disconnected, the order never received) and what the line is
        under is settled (_before: Refused). An error once the order has gone is not
        Disconnected, and nothing more is sent, no cancel either: the order stands as the
        broker has it, working perhaps, a buy with its stop behind it, and the broker is
        asked (report) before it is ever sent again."""
        (listed, new), ref = self._cleared(order), order.order_id
        was, before = self._before(listed, ref)
        number, last, notices = paper.dial(lambda wire, send: _place(wire, send, listed, order))
        if last is None:
            last = self._cancelled({number: ref})[number]
        report = self.report(ref) or Report(ref, (), f"{ref}: the broker tells nothing of it")
        moved = sum(fill.quantity for fill in report.fills)
        held, stops = on(paper.read(), listed)
        if held != was + moved or (last == "Filled" and abs(moved) != order.quantity):
            raise Unprotected(
                f"{ref}: the broker's last word of it was {last}, its fills come to {moved} "
                f"shares, and the account's {listed.line.symbol} went from {was} to {held}: "
                "these do not agree, and the line's stops are left as they are"
            )
        self.settle(listed, held, stops, _due(before, held, moved, new))
        if report.reason is None or not notices:
            return report
        return replace(report, reason=f"{report.reason}; it said: {'; '.join(notices)}")

    def _cleared(self, order: Order | Sale) -> tuple[Listing, Stop | None]:
        """The line as the broker lists it, and the stop a buy goes with (_with), for an
        order cleared to go: the broker lists the line (Refused) and has a price at or below
        the buy's stop (an error raised: no line of the desk's is priced that low), the
        order's id is dated the session of its venue before today's, so it was decided on
        yesterday's bars and no older (Refused), the kill switch was drilled within its
        month and today's check of the account came back clean (Refused, both), and the
        gateway says it is ready: Disconnected, the order never received."""
        symbol, now = order.line.symbol, self._clock()
        listed = self._listings.get(symbol)
        if not isinstance(listed, Listing):
            why = listed.reason if listed else "it was not asked for the line"
            raise Refused(f"{order.order_id}: not sent, the broker does not list {symbol}: {why}")
        new = _with(listed, order) if isinstance(order, Order) else None
        last = venues.sessions(order.line.venue, now.date() - timedelta(days=9), now.date())[-2:]
        if [f"{day:%Y%m%d}" for day in last] != [order.order_id[:8], f"{now:%Y%m%d}"]:
            why = f"{now:%Y-%m-%d} is not the session of {order.line.venue}'s next after"
            raise Refused(f"{order.order_id}: not sent, {why} the one it is dated")
        if not kill.drilled(self._root, now.date()):
            why = f"the kill switch was not drilled in the last {kill.DRILL_DAYS} days"
            raise Refused(f"{order.order_id}: not sent, {why}")
        clearance.require(self._root, now, order.order_id)
        known = gateway.known(now)
        if not known:
            raise Disconnected(f"{order.order_id}: not sent, {known.words}")
        return listed, new

    def _before(self, listed: Listing, order_id: str) -> tuple[Decimal, Stop | None]:
        """A line before an order goes: the shares the account holds of it and the one stop of
        the desk's own it is under, or None. Refused: two stops open on it, or one the broker
        is not holding; and WHILE ANY OTHER ORDER IS OPEN AT THE BROKER, on any line, anyone's,
        as this reading of the account alone tells: it could fill behind the book's gate."""
        account = paper.read()
        (held, stops), told = on(account, listed), reports.orders(account.orders, self._listings)
        kept = [o for o in stops if o.state in reports.HELD]
        rests = [Stop(o.left, o.level, o.ref) for o in kept if o.level is not None]
        if len(stops) > 1 or len(rests) != len(stops):
            said = [f"{o.ref} ({o.state})" for o in stops]
            where = f"the desk's own stops on {listed.line.symbol} are not settled: {said}"
            raise Refused(f"{order_id}: not sent, {where}")
        idle = [f"{o.ref} ({o.state})" for o in told.unsettled + told.others if o.state not in OVER]
        if idle:
            raise Refused(f"{order_id}: not sent, orders are still open at the broker: {idle}")
        return held, (rests[0] if rests else None)

    def settle(
        self, listed: Listing, held: Decimal, stops: Sequence[Resting], due: Stop | None
    ) -> None:
        """Leave a line under the one stop due on it, or under none; held is the shares the
        account has of it and stops the desk's own open on it, as just read. One the broker
        holds for those shares at that level is kept, whatever its reference. With none
        such, the stop due is sent to rest first (_rest), and only then is every other
        cancelled: the line is never under none meanwhile, and for a moment under more than
        the shares held. A stop that sold as it was being cancelled, or ended unseen and the
        account's shares with it, is Unprotected: the stop due is for shares no longer held."""
        resting = (o for o in stops if o.state in reports.HELD)
        kept = next((o for o in resting if due and (o.left, o.level) == due[:2]), None)
        if due is not None and kept is None:
            paper.dial(lambda wire, send: _rest(wire, send, listed, due))
        spare = {o.number: o.ref for o in stops if o is not kept}
        said = self._cancelled(spare) if spare else {}
        odd = {spare[number]: word for number, word in said.items() if word not in GONE}
        if odd and ("Filled" in odd.values() or on(paper.read(), listed)[0] != held):
            raise Unprotected(
                f"a stop of the desk's own on {listed.line.symbol} ended another way as it was "
                f"being cancelled, sold perhaps: {odd}"
            )

    def fills(self) -> tuple[Fill, ...]:
        """The desk's own fills of today, as its ledger keeps them (reports.fills)."""
        return reports.fills(reports.read(), self._listings).ours

    def holdings(self) -> tuple[tuple[str, Decimal], ...]:
        """Every holding of the account, entry by entry: one of a line of the desk's under
        the line's symbol, anything else under its own name (paper.Holding.name)."""
        lines = {paper.own(listed.line): symbol for symbol, listed in self._listings.items()}
        return tuple((lines.get(h.name, h.name), h.shares) for h in paper.read().holdings)

    def stops(self) -> tuple[tuple[str, Decimal], ...]:
        """The desk's own stops the broker is holding to sell, entry by entry."""
        return self._orders().stops

    def cancel(self) -> tuple[str, ...]:
        """THE KILL SWITCH'S QUESTION: every order of the desk's own still working is sent
        a cancel, and each the broker then says is cancelled is named by the desk's order
        id, in the order listed; one that filled first is not named, and its fill is in the
        day's fills. None working: nothing is sent, and none named. A cancel the broker
        refuses is settled by the account read again: an order no longer working there was
        over before the cancel reached it; one still working is an error raised."""
        working = {o.number: o.ref for o in self._orders().unsettled if _working(o)}
        said = self._cancelled(working) if working else {}
        return tuple(ref for number, ref in working.items() if said[number] in GONE)

    def _cancelled(self, working: Mapping[str, str]) -> dict[str, str]:
        """Send a cancel for each of the desk's own orders given, its order id by its number,
        and give the broker's last word of each. A cancel the broker refuses is settled by
        the account read again; an order still open there, a stop the broker still holds
        among them, is an error raised."""
        said = paper.dial(lambda wire, send: _cancel(wire, send, tuple(working)))
        refused = {number: word for number, word in said.items() if word not in OVER}
        listed = paper.read().orders if refused else ()
        still = [
            f"{o.ref} ({refused[o.number]})"
            for o in listed
            if o.number in refused and o.client == str(paper.CLIENT) and o.state not in OVER
        ]
        if still:
            raise NotCancelled(f"the broker still lists as working, its cancel refused: {still}")
        return said
