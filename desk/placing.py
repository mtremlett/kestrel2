"""placing - THE PAPER ACCOUNT BEHIND THE SEND PATH: what the desk asks of any broker
(broker.Broker), answered by the paper account through the one door (desk/paper.py): what
the broker did with an order, the desk's fills, what the account holds, the stops resting on
it, the kill switch's cancel, and the placing of a sale. A BUY IS NOT SENT YET: the stop a
buy leaves resting is not built, and no buy goes without it; nor does a sale on a line under
a stop of the desk's own, whose shares it could not take off that stop. Both raise.

Each answer is read from the gateway afresh, in a conversation of its own. The fills, the
open orders and the stops are the desk's own alone (desk/reports.py): anyone else's is not
the desk's, and the day's check names it (desk/clearance.py). The holdings are the whole
account's; an ended order is known by its reference alone, for the broker's list of them
names no client. An answer that cannot be read whole is an error raised. The broker tells
of the day alone: an order or a fill of an earlier day is in the desk's ledger, or nowhere.

Two things are sent that are no question. An order, by `place` alone: after the kill
switch was drilled (kill.drilled), the day's check came back clean (clearance.require) and
the gateway said it is ready (gateway.known).
And a cancel, for an order of the desk's own still working: by the kill switch, and by
`place` for what the broker did not fill. A stop resting to sell what is held is never
cancelled."""

from __future__ import annotations

from collections.abc import Callable, Collection, Iterator, Mapping
from dataclasses import replace
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import BinaryIO

from desk import clearance, gateway, kill, listing, paper, reports
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
CANCELLED = "202"  #: the gateway's notice that an order was cancelled, as it was asked
#: The broker's words for an order it will not work again: cancelled, or done.
GONE = frozenset({"Cancelled", "ApiCancelled"})
OVER = GONE | {"Filled"}


class NotCancelled(Exception):
    """The broker refused to cancel an order of the desk's own, and still lists it working."""


def _working(order: Resting) -> bool:
    """Whether an order of the desk's own, and no stop the broker is holding, is the kill
    switch's to cancel: not one that is over, and never a stop to sell (reports.stop_to_sell,
    the one rule for it), whose line would be left unprotected."""
    return not reports.stop_to_sell(order) and order.state not in OVER


def _told(wire: BinaryIO, numbers: Collection[str]) -> Iterator[tuple[str, str, str | None]]:
    """What the gateway says, for as long as it is read, of orders of the desk's own by
    their numbers: the state one is over in (its number, the state, None), or a notice of
    one (its number, the notice's words, its code). What it tells meanwhile of the orders
    themselves and their fills is passed over (paper.other): the account's own readings
    give it."""
    while True:
        fields = paper.receive(wire)
        if fields[0] == paper.STATUS:
            if len(fields) != 12:
                raise ValueError(f"an order's state of a shape the desk does not read: {fields}")
            if fields[1] in numbers and fields[9] == str(paper.CLIENT) and fields[2] in OVER:
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
        elif code != CANCELLED:
            said.setdefault(number, f"{code}: {word}")
        if len(said) == len(numbers):
            break
    return said


def _place(
    wire: BinaryIO, send: paper.Send, listed: Listing, sale: Sale
) -> tuple[str, bool, tuple[str, ...]]:
    """Send a sale over an open connection, once, and read the broker's word of it: the
    number it went under, whether the broker says it is over (filled, or cancelled), and
    every notice the broker gave of it. It goes at the market, for the day, to the broker's
    router, the line by the broker's own number for it, under the number the gateway gave
    at the start and the desk's order id as its reference. The reading ends when the order
    is over, or when the gateway has said nothing for as long as the door waits
    (paper.SECONDS): the order is then not over, and is the desk's to cancel. A gateway that
    hangs up first is an error: the order may have arrived."""
    number, line = str(paper.start(wire, send)), listed.line
    line_there = (listed.contract, line.symbol, "STK", "", "0.0", "", "", listing.ROUTE, "")
    asks = ("SELL", sale.quantity, "MKT", "", "", "DAY", "", "", "O", 0, sale.order_id)
    send(paper.message(PLACE, number, *line_there, line.currency, *[""] * 4, *asks, *PLAIN))
    notices: list[str] = []
    try:
        for _, word, code in _told(wire, (number,)):
            if code is None:
                return number, True, tuple(notices)
            notices.append(f"{code}: {word}")
    except TimeoutError:  #: the door's wait ran out in silence: its answer is "not over"
        pass
    return number, False, tuple(notices)


class Paper:
    """The paper account, as a broker the send path, the day run and the kill switch can
    stand on."""

    def __init__(
        self, listings: Mapping[str, Listing | Unlisted], root: Path, clock: Callable[[], datetime]
    ) -> None:
        """listings is each of the desk's lines as the broker lists it now (listing.read):
        by them a fill, an order and a holding are known as a line's. root holds the desk's
        record, the day's checks among it; clock gives the moment, in UTC. Both are read
        only before an order is sent."""
        self._listings, self._root, self._clock = dict(listings), root, clock

    def _orders(self) -> reports.Orders:
        return reports.orders(paper.read().orders, self._listings)

    def report(self, order_id: str) -> Report | None:
        """What the broker did today with an order id, or None if it tells nothing of it. Its
        open orders are read first, then the day's ended ones, then the day's fills, so that
        an order which ends or fills between the readings is in one of them: read the other
        way round it could be in none, and be sent again. (Unproven on a real order: that
        the ended list never lags the open one, and that it keeps an order refused on
        entry.) The reason is None only for an order the broker lists once, ended and filled
        whole, with fills that come to the shares it says were filled; otherwise it is
        everything the broker says of it."""
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
        """Send a sale to the paper broker and give its last answer (_place): what the
        broker has not ended when it falls silent is cancelled, and the answer is what the
        broker then says it did with the order (report), with the notices it gave when it
        did not fill whole. Nothing is sent, and the reason raised, unless the broker lists
        the line, the kill switch was drilled within its month and today's check of the
        account came back clean (Refused), and the gateway says it is ready: Disconnected,
        the order never received. NOT BUILT, and raised before anything is sent: a buy, for
        the stop it must leave; and a sale on a line where a stop of the desk's own is open,
        held or not yet, for the shares it must take off that stop. An error once the order
        has gone is not Disconnected, and nothing more is sent, no cancel either: the order
        stands as the broker has it, working perhaps, and the broker is asked (report)
        before it is ever sent again."""
        if not isinstance(order, Sale):
            raise NotImplementedError(
                f"placing.Paper.place: {order.order_id} is not sent; no buy is sent to the paper "
                "broker until the stop it leaves is built (docs/PLAN.md, paper-stops)"
            )
        symbol, now = order.line.symbol, self._clock()
        listed = self._listings.get(symbol)
        if not isinstance(listed, Listing):
            why = listed.reason if listed else "it was not asked for the line"
            raise Refused(f"{order.order_id}: not sent, the broker does not list {symbol}: {why}")
        if not kill.drilled(self._root, now.date()):
            why = f"the kill switch was not drilled in the last {kill.DRILL_DAYS} days"
            raise Refused(f"{order.order_id}: not sent, {why}")
        clearance.require(self._root, now, order.order_id)
        known = gateway.known(now)
        if not known:
            raise Disconnected(f"{order.order_id}: not sent, {known.words}")
        if any(
            reports.ours(o.client, o.ref) and reports.stop_to_sell(o) and o.state not in OVER
            for o in paper.read().orders
            if o.contract == listed.contract
        ):
            raise NotImplementedError(
                f"placing.Paper.place: {order.order_id} is not sent; a stop of the desk's own is "
                f"open on {symbol}, and taking a sale's shares off it is not built "
                "(docs/PLAN.md, paper-stops)"
            )
        number, over, notices = paper.dial(lambda wire, send: _place(wire, send, listed, order))
        if not over:
            self._cancelled({number: order.order_id})
        nothing = Report(order.order_id, (), f"{order.order_id}: the broker tells nothing of it")
        report = self.report(order.order_id) or nothing
        if report.reason is None or not notices:
            return report
        return replace(report, reason=f"{report.reason}; it said: {'; '.join(notices)}")

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
        the account read again; an order still working there is an error raised."""
        said = paper.dial(lambda wire, send: _cancel(wire, send, tuple(working)))
        refused = {number: word for number, word in said.items() if word not in OVER}
        listed = self._orders().unsettled if refused else ()
        still = [
            f"{o.ref} ({refused[o.number]})" for o in listed if o.number in refused and _working(o)
        ]
        if still:
            raise NotCancelled(f"the broker still lists as working, its cancel refused: {still}")
        return said
