"""reports - WHAT THE PAPER BROKER SAYS WAS DONE, AND WHOSE IT IS: the fills made on the
paper account today, asked through the one door (desk/paper.py), and each fill and each
resting order told apart as the desk's own or anyone else's. Only a question is sent.

The desk's own is what the desk's own client placed under an order id of the desk's, which
the broker carries as the order's reference. A fill of the desk's own comes back as the
ledger keeps it (broker.Fill): under the broker's execution id, with the desk's order id, its
line's symbol, and its price turned from the broker's unit (pence on some London lines)
back into the line's currency. A fill or an order of anyone else's is kept apart, exactly
as the broker gave it. An answer the desk cannot read or cannot trust stops the reading."""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import BinaryIO

from desk import paper
from desk.broker import Fill
from desk.listing import Listing, Unlisted
from desk.paper import Resting

ASK_FILLS = 7  #: what this module sends: one question, which places no order
FILL, FILLS_END, FEE = "11", "55", "59"  #: the answers, by the gateway's own numbers
NUMBER = "1"  #: the number the desk gives its one question, which the answers carry back
SIDES = {"BOT": 1, "SLD": -1}  #: the broker's words for a fill that bought and one that sold
#: When a fill was made, as the gateway tells it: the day and the time, on a clock it names.
WHEN = re.compile(r"(\d{8} \d\d:\d\d:\d\d) (\S.*)")
#: The clock the gateway tells each venue's fills on, seen on real fills of both: the one
#: it keeps the exchange's hours on (for London an hour ahead of London's own, the same day
#: all session long), so a fill's day there is the day of its session.
CLOCKS = {"LSE": "MET", "US": "US/Eastern"}
#: The broker's words for an order it holds and will act on: a stop in either is resting.
HELD = frozenset({"PreSubmitted", "Submitted"})


@dataclass(frozen=True)
class Execution:
    """One fill as the broker reports it, whoever's order made it."""

    execution_id: str  #: the broker's own lasting id for the fill
    client: str  #: the client id that placed its order
    ref: str  #: the reference its order was placed under: on the desk's own, the desk's order id
    account: str
    contract: str  #: the broker's own number for what was traded
    symbol: str
    shares: Decimal  #: positive bought, negative sold
    price: Decimal  #: in the broker's unit: pence on some London lines
    made: datetime  #: when it was made, on the clock the gateway names
    clock: str  #: that clock, in the gateway's word for it

    def __post_init__(self) -> None:
        """It has an id to be kept under, shares that moved, and a price that is a price."""
        if not (self.execution_id and self.shares.is_finite() and self.shares and self.price > 0):
            raise ValueError(f"a fill the desk cannot trust: {self}")


@dataclass(frozen=True)
class Fills:
    #: The desk's own, as its ledger keeps them, in the order given: a line's in the order made.
    ours: tuple[Fill, ...]
    others: tuple[Execution, ...]  #: every other fill on the account, as the broker gave it


@dataclass(frozen=True)
class Orders:
    """The orders the broker lists as open on the account, by whose they are."""

    #: The desk's own stops resting to sell, entry by entry: its line's symbol and the shares
    #: the broker still holds it for, as the desk's one comparison takes them (book.differences).
    stops: tuple[tuple[str, Decimal], ...]
    #: The desk's own orders that are no such stop: one still to fill, or a stop the broker is
    #: not holding (refused, being cancelled, its state not read). None of them protects.
    unsettled: tuple[Resting, ...]
    others: tuple[Resting, ...]  #: every order of anyone else's


def _execution(fields: list[str]) -> Execution:
    if len(fields) != 31:
        raise ValueError(f"a fill of a shape the desk does not read: {fields}")
    contract, symbol, execution_id, time, account, side, shares, price, client, ref = (
        fields[n] for n in (3, 4, 14, 15, 16, 18, 19, 20, 22, 26)
    )
    when, count = WHEN.fullmatch(time), paper.number(shares, fields)
    if when is None or side not in SIDES or count.is_signed():
        raise ValueError(f"a fill the desk cannot trust: {fields}")
    return Execution(
        execution_id,
        client,
        ref,
        paper.only(account),
        contract,
        symbol,
        SIDES[side] * count,
        paper.number(price, fields),
        datetime.strptime(when[1], "%Y%m%d %H:%M:%S"),  # noqa: DTZ007 its clock is kept beside it
        when[2],
    )


def converse(wire: BinaryIO, send: paper.Send) -> tuple[Execution, ...]:
    """Ask over an open connection for every fill made on the account today, whoever's order
    made it, reading until the gateway says the list is whole. The broker's note of each
    fill's fee is passed over."""
    paper.start(wire, send)
    send(paper.message(ASK_FILLS, 3, NUMBER, 0, "", "", "", "", "", ""))
    found: list[Execution] = []
    while True:
        fields = paper.receive(wire)
        if fields[:2] == [FILL, NUMBER]:
            found.append(_execution(fields))
        elif fields[0] == FILLS_END and fields[2:] == [NUMBER]:
            return tuple(found)
        elif fields[0] != FEE:
            paper.other(fields)


def read() -> tuple[Execution, ...]:
    """Every fill the paper broker made on the account today, as the gateway gives them now."""
    return paper.dial(converse)


def ours(client: str, ref: str) -> bool:
    """Whether an order, or a fill of one, is the desk's own: placed by the desk's own
    client, under an order id of the desk's. Anything else on the account is someone
    else's: a hand at the broker's screen, the old desk, another program."""
    return client == str(paper.CLIENT) and bool(ref.strip())


def _line(contract: str, listings: Mapping[str, Listing | Unlisted], whose: object) -> Listing:
    """The desk's line the broker gives a number for. The desk orders listed lines alone, so
    an order or fill of its own on anything else is one it cannot explain."""
    for listed in listings.values():
        if isinstance(listed, Listing) and listed.contract == contract:
            return listed
    raise ValueError(f"the desk's own, on no line the broker lists for it ({contract}): {whose}")


def fills(executions: Iterable[Execution], listings: Mapping[str, Listing | Unlisted]) -> Fills:
    """The broker's fills told apart: the desk's own as its ledger keeps them, each priced
    in its line's currency, and everyone else's as given. listings is each line as the
    broker lists it now (listing.read). A fill of the desk's own that cannot be given whole
    and once is an error raised, never left out: on no listed line, not in whole shares, its
    day not told on its exchange's clock, made before the line's last, or given twice or
    beside the broker's correction of it (the same id but for its last part)."""
    own: list[Fill] = []
    others: list[Execution] = []
    last: dict[str, datetime] = {}
    for e in executions:
        if not ours(e.client, e.ref):
            others.append(e)
            continue
        listed = _line(e.contract, listings, e)
        symbol, price = listed.line.symbol, e.price / listed.magnifier
        faults = {
            "not in whole shares": e.shares != int(e.shares),
            "not told on its exchange's clock": e.clock != CLOCKS[listed.line.venue],
            "made before the line's last": last.get(symbol, e.made) > e.made,
        }
        if any(faults.values()):
            wrong = ", ".join(fault for fault, found in faults.items() if found)
            raise ValueError(f"a fill of the desk's own {wrong}: {e}")
        last[symbol] = e.made
        own.append(Fill(e.execution_id, e.ref, symbol, int(e.shares), price, e.made.date()))
    made = Counter(fill.execution_id.rsplit(".", 1)[0] for fill in own)
    twice = sorted(fill for fill, times in made.items() if times > 1)
    if twice:
        raise ValueError(
            f"fills of the desk's own given twice, or corrected by the broker: {twice}"
        )
    return Fills(tuple(own), tuple(others))


def orders(resting: Iterable[Resting], listings: Mapping[str, Listing | Unlisted]) -> Orders:
    """The orders the broker lists as open told apart: the desk's own stops resting to
    sell, the desk's own other orders, and everyone else's. resting is the account's open
    orders (paper.read); listings, each line as the broker lists it now (listing.read)."""
    stops: list[tuple[str, Decimal]] = []
    unsettled: list[Resting] = []
    others: list[Resting] = []
    for order in resting:
        if not ours(order.client, order.ref):
            others.append(order)
            continue
        line = _line(order.contract, listings, order).line
        if (order.action, order.kind) == ("SELL", "STP") and order.state in HELD:
            stops.append((line.symbol, order.left))
        else:
            unsettled.append(order)
    return Orders(tuple(stops), tuple(unsettled), tuple(others))
