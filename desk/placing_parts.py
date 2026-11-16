"""placing_parts - THE WIRE HALF OF THE SEND PATH, split from desk/placing.py (which imports
it): the messages of an order, a stop and a cancel, and the broker's word of each read back
over an open connection. desk/placing.py decides what is sent and when; this only sends and
reads."""

from __future__ import annotations

from collections.abc import Collection, Iterator, Sequence
from decimal import Decimal
from typing import BinaryIO, NamedTuple

from desk import listing, paper, reports
from desk.listing import Listing
from desk.orders import Order, Sale

PLACE, CANCEL = 3, 4  #: what this module sends that is no question: an order, and a cancel
#: The rest of an order's message after its reference: sent at once, under no other order, every
#: other choice left as the published client (ib_insync 0.9.86, never imported) leaves it.
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


def _told(
    wire: BinaryIO, numbers: Collection[str], states: Collection[str] = OVER
) -> Iterator[tuple[str, str, str | None]]:
    """What the gateway says, for as long as it is read, of orders of the desk's own by their
    numbers: a state one stands in (its number, the state, None), or a notice of one (its
    number, the words, its code). The rest is passed over (paper.other)."""
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
    over in, or its notice refusing the cancel. A gateway that hangs up first is an error."""
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
    broker's own number, the desk's id its reference. first is how it is sent where not at
    once and alone (PLAIN's first two): 0, held back until the order that waits on it is
    sent; 1 and that order's number, to wait on it."""
    line, (action, *kind) = listed.line, deal
    there = (listed.contract, line.symbol, "STK", "", "0.0", "", "", listing.ROUTE, "")
    asks = (action, shares, *kind, "", "", "O", 0, ref, *first, *PLAIN[len(first) :])
    return paper.message(PLACE, number, *there, line.currency, *[""] * 4, *asks)


def _selling(number: str, listed: Listing, stop: Stop, *first: str) -> bytes:
    """The message that places a stop to sell, at its level in plain digits, until cancelled."""
    deal = ("SELL", "STP", "", f"{stop.level:f}", "GTC")
    return _message(number, listed, deal, stop.shares, stop.ref, *first)


def _with(listed: Listing, order: Order) -> Stop:
    """The stop a buy goes with: its shares, at the order's stop put onto the broker's step
    and unit, under the order's id and "-stop"."""
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
    """Send a stop to sell over an open connection, alone, and read until the broker says it
    holds it. One it ends instead is an error with its notices; so are silence and a hang-up."""
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
