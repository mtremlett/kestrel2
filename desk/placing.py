"""placing - THE PAPER ACCOUNT BEHIND THE SEND PATH: what the desk asks of any broker
(broker.Broker), answered by the paper account through the one door (desk/paper.py). It
answers every question but one: what the broker did with an order, the desk's fills, what
the account holds, the stops resting on it, and the kill switch's cancel. PLACING IS NOT
BUILT: `place` raises, and no order is sent.

Each answer is read from the gateway afresh, in a conversation of its own, and is of the
desk's own alone (desk/reports.py): anyone else's fill, order or stop is not the desk's,
and the day's check names it (desk/clearance.py). An answer that cannot be read whole is an
error raised. The broker tells of the day alone: an order or a fill of an earlier day is in
the desk's ledger, or nowhere.

One thing is sent that is no question, and only by the kill switch: a cancel for each order
of the desk's own still working. A stop resting to sell what is held is never cancelled."""

from __future__ import annotations

from collections.abc import Collection, Mapping
from decimal import Decimal
from typing import BinaryIO

from desk import paper, reports
from desk.broker import Fill, Report
from desk.listing import Listing, Unlisted
from desk.orders import Order, Sale
from desk.paper import Resting

CANCEL = 4  #: what this module sends that is no question: cancel one order, by its number
CANCELLED = "202"  #: the gateway's notice that an order was cancelled, as it was asked
#: The broker's words for an order it will not work again: cancelled, or done.
GONE = frozenset({"Cancelled", "ApiCancelled"})
OVER = GONE | {"Filled"}
#: What the gateway tells unasked of an order and its fills while it is being cancelled.
PASSED = (paper.ORDER, reports.FILL, reports.FEE)


def _working(order: Resting) -> bool:
    """Whether an order of the desk's own, and no stop the broker is holding, is the kill
    switch's to cancel: not one that is over, and never a stop to sell, whose line would be
    left unprotected."""
    return (order.action, order.kind) != ("SELL", "STP") and order.state not in OVER


def _cancel(wire: BinaryIO, send: paper.Send, numbers: Collection[str]) -> dict[str, str]:
    """Ask over an open connection that orders of the desk's own be cancelled, each by its
    number, and read until the broker has said of every one that it is over: its word for
    each, cancelled, or filled before the cancel reached it. What it tells meanwhile of the
    orders themselves and their fills is passed over: the account's own readings give it.
    Anything else it says of one (a cancel it refuses), and a gateway that hangs up first,
    is an error: the desk does not then know what is still working."""
    paper.start(wire, send)
    send(b"".join(paper.message(CANCEL, 1, number, "") for number in numbers))
    confirmed = {(paper.NEWS, number, CANCELLED) for number in numbers}
    over: dict[str, str] = {}
    while len(over) < len(numbers):
        fields = paper.receive(wire)
        if fields[0] == paper.STATUS:
            if len(fields) != 12:
                raise ValueError(f"an order's state of a shape the desk does not read: {fields}")
            if fields[1] in numbers and fields[9] == str(paper.CLIENT) and fields[2] in OVER:
                over[fields[1]] = fields[2]
        elif fields[0] not in PASSED and (fields[0], *fields[2:4]) not in confirmed:
            paper.other(fields)
    return over


class Paper:
    """The paper account, as a broker the send path, the day run and the kill switch can
    stand on."""

    def __init__(self, listings: Mapping[str, Listing | Unlisted]) -> None:
        """listings is each of the desk's lines as the broker lists it now (listing.read):
        by them a fill, an order and a holding are known as a line's."""
        self._listings = dict(listings)

    def _orders(self) -> reports.Orders:
        return reports.orders(paper.read().orders, self._listings)

    def report(self, order_id: str) -> Report | None:
        """What the broker did today with an order id, or None if it tells nothing of it. Its
        open orders are read first, then the day's ended ones, then the day's fills: an order
        that ends or fills between the readings is seen in one of them, never taken as
        unknown and sent again. The reason is None only for an order the broker lists once,
        ended and filled whole, whose fills come to the shares it says were filled; otherwise
        it is everything the broker says of it."""
        listed = [o for o in self._orders().unsettled if o.ref == order_id]
        ended = [e for e in reports.ended() if e.ref == order_id]
        fills = tuple(fill for fill in self.fills() if fill.order_id == order_id)
        if not (listed or ended or fills):
            return None
        done = sum(abs(fill.quantity) for fill in fills)
        if not listed and ended == [reports.Ended(order_id, "Filled", Decimal(done), Decimal(0))]:
            return Report(order_id, fills, None)
        said = [f"{o.state}, {o.left} shares still to be done" for o in listed]
        said += [f"{e.state}, {e.filled} shares filled and {e.left} not" for e in ended]
        told = "; ".join(said) or "nothing of the order"
        reason = f"{order_id}: the broker says {told}; its fills today come to {done} shares"
        return Report(order_id, fills, reason)

    def place(self, order: Order | Sale) -> Report:
        raise NotImplementedError(
            f"placing.Paper.place: {order.order_id} is not sent; no order is sent to the paper "
            "broker until placing is built (docs/PLAN.md, the paper lane's book)"
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
        day's fills. None working: nothing is sent, and none named."""
        working = {o.number: o.ref for o in self._orders().unsettled if _working(o)}
        if not working:
            return ()
        over = paper.dial(lambda wire, send: _cancel(wire, send, tuple(working)))
        return tuple(ref for number, ref in working.items() if over[number] in GONE)
