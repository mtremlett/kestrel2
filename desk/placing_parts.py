"""placing_parts - what the paper account's placing is built of, apart from the account: the
messages that place an order and a stop, what the gateway says of orders by their numbers
(told) and the cancel (cancel), the stop a line is due, and the stop moved."""

from __future__ import annotations

from collections.abc import Collection, Iterator, Sequence
from decimal import Decimal
from typing import BinaryIO, NamedTuple

from desk import listing, paper, reports
from desk.listing import Listing
from desk.paper import Resting

PLACE = 3  #: what is sent that is no question: an order
CANCEL = 4  #: what is sent that is no question besides an order: a cancel
#: The broker's words for an order it will not work again: cancelled, or done.
GONE = frozenset({"Cancelled", "ApiCancelled"})
OVER = GONE | {"Filled"}


class Stop(NamedTuple):
    """A stop of the desk's own to sell a line's shares, resting at the broker or due there."""

    shares: Decimal
    level: Decimal  #: the price it goes at, in the broker's unit
    ref: str  #: the reference it is placed under


#: The rest of an order's message after its reference: sent at once, under no other order, every
#: other choice left as the published client (ib_insync 0.9.86, never imported) leaves it.
PLAIN = (
    "1|0|0|0|0|0|0|0||0.0||||||||0||-1|0|||0|||0|0||0||||||0|||||0|||||||||||0|||0|0|||0||0|0|0|0"
    "|||||||0|||||||||0|0|0|0|||0||"
).split("|")


def message(
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


def selling(number: str, listed: Listing, stop: Stop, *first: str) -> bytes:
    """The message that places a stop to sell, at its level in plain digits, until cancelled."""
    deal = ("SELL", "STP", "", f"{stop.level:f}", "GTC")
    return message(number, listed, deal, stop.shares, stop.ref, *first)


def due(before: Stop | None, held: Decimal, moved: int, new: Stop | None) -> Stop | None:
    """The one stop a line is to be left under once an order has moved shares on it (bought,
    or sold: negative), or None for none: for all the shares the account then holds of it. A
    buy that bought puts it at the level and under the reference of the stop it went with
    (new); a sale, and a buy that bought none, leave it at the level and under the reference
    of the stop the line was under before, and a line under none before is given none."""
    kept = new if moved > 0 and new else before
    return kept._replace(shares=held) if kept and held > 0 else None


def moved(listed: Listing, held: Decimal, stops: Sequence[Resting], level: Decimal) -> Stop:
    """The stop a line's one resting stop is moved to: its reference, for all the shares held,
    at level (the line's currency) put onto the broker's step and unit. A line with not
    exactly one stop resting, or none held, is an error: there is nothing to move."""
    rests = [o for o in stops if o.state in reports.HELD and o.level is not None]
    if len(rests) != 1 or len(stops) != 1 or held <= 0:
        raise ValueError(f"{listed.line.symbol}: {len(stops)} stops and {held} shares, none moved")
    return Stop(held, listed.floor(level), rests[0].ref)


def told(
    wire: BinaryIO, numbers: Collection[str], door: paper.Door, states: Collection[str] = OVER
) -> Iterator[tuple[str, str, str | None]]:
    """What the gateway says, for as long as it is read, of orders of the desk's own by their
    numbers: a state one stands in (its number, the state, None), or a notice of one (its
    number, the words, its code). The rest is passed over (paper.other)."""
    while True:
        fields = paper.receive(wire)
        if fields[0] == paper.STATUS:
            if len(fields) != 12:
                raise ValueError(f"an order's state of a shape the desk does not read: {fields}")
            if fields[1] in numbers and fields[9] == str(door.client) and fields[2] in states:
                yield fields[1], fields[2], None
        elif fields[0] == paper.NEWS and len(fields) > 4 and fields[2] in numbers:
            yield fields[2], fields[4], fields[3]
        else:
            paper.other(fields)


def cancel(
    wire: BinaryIO, send: paper.Send, numbers: Collection[str], door: paper.Door
) -> dict[str, str]:
    """Ask over an open connection that orders of the desk's own be cancelled, each by its
    number, and read until the broker has given its last word of every one: the state it is
    over in, or its notice refusing the cancel. A gateway that hangs up first is an error."""
    paper.start(wire, send, door)
    send(b"".join(paper.message(CANCEL, 1, number, "") for number in numbers))
    said: dict[str, str] = {}
    for number, word, code in told(wire, numbers, door):
        if code is None:
            said[number] = word
        elif code != paper.CANCELLED:
            said.setdefault(number, f"{code}: {word}")
        if len(said) == len(numbers):
            break
    return said
