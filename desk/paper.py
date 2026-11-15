"""paper - THE ONE DOOR TO THE PAPER BROKER: IB Gateway's paper port on this machine, spoken
to with the standard library alone. Here the desk reads the account's holdings and the
orders resting on it, and sets them against its own book. Every conversation with the
gateway goes through this door (`dial`); what is sent that is no question, an order and a
cancel of one of the desk's own, is sent by desk/placing.py alone.

The gateway speaks in messages: four bytes of length, then fields each ended by a zero byte,
the first naming the message's kind. The desk offers one version of that language and
refuses any other, so each message it reads has one known shape."""

from __future__ import annotations

import re
import socket
import struct
import sys
from collections import Counter
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import BinaryIO, TypeVar

from desk import book
from desk.lines import Line

HOST, PORT = "127.0.0.1", 4002  #: the paper port on this machine: the only door the desk dials
CLIENT = 222  #: the desk's own client id at the gateway (docs/DECISIONS.md)
VERSION = "176"  #: the one version of the gateway's language the desk reads
SECONDS = 15  #: a gateway silent for longer has not answered
#: The kinds of message, by the gateway's own numbers.
ACCOUNTS, READY, NEWS, STATUS = "15", "9", "4", "3"
HOLDING, HOLDINGS_END, ORDER, ORDERS_END = "61", "62", "5", "53"
FILL, FEE = "11", "59"  #: a fill, and the broker's note of its fee (read in desk/reports.py)
START, ASK_HOLDINGS, ASK_ORDERS = 71, 61, 16  #: what the desk sends: none places an order
UNASKED = "-1"  #: the number a fill carries when no question of the desk's asked for it
#: News of the gateway's price feeds, which this door does not read; any other news stops
#: it, that it cannot look lines up (2157) included: nothing it then says of a line is sound.
FEEDS = frozenset({"2103", "2104", "2105", "2106", "2107", "2108", "2119", "2158"})
CANCELLED = "202"  #: its notice that an order was cancelled: news of an order, and no fault
Send = Callable[[bytes], object]  #: what puts the desk's bytes on the connection
PLAIN = re.compile("-?[0-9]+([.][0-9]+)?")  #: a number as the gateway writes one
T = TypeVar("T")


class NotPaper(Exception):
    """The gateway answered for an account that is not a paper one: the desk stops there."""


def only(code: str) -> str:
    """An account's code, given back if it is a paper one's: the broker starts a paper
    account's code with a D, and no other's."""
    if not code.startswith("D"):
        raise NotPaper(f"account {code!r} is not a paper account: this desk is paper only")
    return code


def number(text: str, fields: list[str]) -> Decimal:
    """A number from a message of the gateway's: plain digits, with a point perhaps. Nothing,
    not-a-number, an infinity and the broker's own "unset" (written with an exponent) are
    refused, and the message named."""
    if PLAIN.fullmatch(text) is None:
        raise ValueError(f"{text!r} is no plain number, in the gateway's message: {fields}")
    return Decimal(text)


@dataclass(frozen=True)
class Holding:
    account: str
    symbol: str
    kind: str  #: the broker's word for what is held: "STK" is a share or a fund
    currency: str
    shares: Decimal

    def __post_init__(self) -> None:
        """Its kind and its currency are one word each, so the name it is compared under
        (symbol, kind, currency) reads one way only; and its shares are a number."""
        if not (self.kind.isalnum() and self.currency.isalnum() and self.shares.is_finite()):
            raise ValueError(f"a holding the desk cannot trust: {self}")

    @property
    def name(self) -> str:
        """What it is compared under: the same symbol in another currency is another thing."""
        return f"{self.symbol} {self.kind} {self.currency}"


@dataclass(frozen=True)
class Resting:
    """An order the broker lists as open, whoever placed it. Whether the broker is working
    it, and for how many shares, is its state: an order refused or part done is listed too."""

    broker_id: str  #: the broker's own lasting id for the order
    number: str  #: the order's number at the client that placed it: that client cancels it by it
    client: str  #: the client id that placed it
    account: str
    symbol: str
    action: str
    shares: Decimal
    kind: str  #: the broker's word for the order: "STP" a stop, "MKT" at the market
    contract: str  #: the broker's own number for what it would trade
    ref: str  #: the reference it was placed under: on the desk's own, the desk's order id
    state: str  #: the broker's word for where it stands: "PreSubmitted", "Inactive"
    left: Decimal  #: the shares still to be done, as that state gives them
    level: Decimal | None  #: the price a stop ("STP") goes at, in the broker's unit; else None

    def __post_init__(self) -> None:
        if self.action not in ("BUY", "SELL"):
            raise ValueError(f"order {self.broker_id}: {self.action!r} neither buys nor sells")


@dataclass(frozen=True)
class Account:
    """The paper account as the broker gave it at one moment."""

    holdings: tuple[Holding, ...]
    orders: tuple[Resting, ...]


def message(*fields: object) -> bytes:
    """One message for the gateway: its length, then each field ended by a zero byte."""
    body = "".join(f"{field}\0" for field in fields).encode()
    return struct.pack(">I", len(body)) + body


def receive(wire: BinaryIO) -> list[str]:
    """The gateway's next message, as its fields."""
    head = wire.read(4)
    size = struct.unpack(">I", head)[0] if len(head) == 4 else 0
    body = wire.read(size)
    if len(head) < 4 or len(body) < size:
        raise ConnectionError("the gateway hung up before its answer was whole")
    fields = body.decode().split("\0")[:-1]
    if not fields:
        raise ValueError("a message from the gateway cut short: it names no kind")
    return fields


def other(fields: list[str]) -> str:
    """A message that answers no question of the desk's, and its kind: every account it
    names must be a paper one, its news may be of the price feeds only, and a kind the desk
    does not know is refused. What the gateway tells unasked of an order as it changes (the
    order, its state, that it was cancelled, a fill under no question's number, the fill's
    fee) is passed over: a reading that asks for orders takes it as its answer, and no other
    needs it."""
    kind = fields[0]
    if len(fields) < {ACCOUNTS: 3, NEWS: 5}.get(kind, 1):
        raise ValueError(f"a message from the gateway cut short: {fields}")
    if kind == ACCOUNTS:
        for code in fields[2].split(","):
            only(code)
    elif kind == NEWS and fields[3] != CANCELLED and fields[3] not in FEEDS:
        raise ConnectionError(f"the gateway says {fields[3]}: {fields[4]}")
    elif kind not in (NEWS, READY, STATUS, HOLDINGS_END, ORDERS_END, ORDER, FEE) and (
        fields[:2] != [FILL, UNASKED]
    ):
        raise ValueError(f"a message of a kind the desk does not read: {fields}")
    return kind


def _holding(fields: list[str]) -> Holding:
    if len(fields) != 16:
        raise ValueError(f"a holding of a shape the desk does not read: {fields}")
    account, symbol, kind, currency, shares = (fields[n] for n in (2, 4, 5, 11, 14))
    return Holding(only(account), symbol, kind, currency, number(shares, fields))


def _order(fields: list[str], states: Mapping[str, tuple[str, Decimal]]) -> Resting:
    """Only the head of the message is read: the line, the order and who placed it, and a
    stop's level. It stands where the broker last said (states, by its ids): one it told no
    state of is no order the desk can read, nor is one under no id of the broker's, for by
    that id one order is told from another."""
    if len(fields) < 26 or not (fields[25].isascii() and fields[25].isdigit() and int(fields[25])):
        raise ValueError(f"an order of a shape the desk does not read, or under no id: {fields}")
    its, contract, symbol, action, shares, kind, level, account, ref, client, broker_id = (
        fields[n] for n in (1, 2, 3, 13, 14, 15, 17, 20, 23, 24, 25)
    )
    head = (broker_id, its, client, only(account), symbol, action, number(shares, fields), kind)
    if broker_id not in states:
        raise ValueError(f"an order the broker told no state of, by its id for it: {broker_id}")
    at = number(level, fields) if kind == "STP" else None
    return Resting(*head, contract, ref, *states[broker_id], at)


def _state(fields: list[str]) -> tuple[str, tuple[str, Decimal]]:
    """Where an order stands, under the broker's own id for it: the broker's word, and the
    shares still to be done."""
    if len(fields) != 12:
        raise ValueError(f"an order's state of a shape the desk does not read: {fields}")
    return fields[6], (fields[2], number(fields[4], fields))


def start(wire: BinaryIO, send: Send) -> int:
    """Open a conversation: offer the one version, start as the desk's client, and read
    until the gateway is ready and has named its accounts, all paper. Nothing is asked
    before. It gives the number the gateway, ready, takes this client's next order under."""
    offer = f"v{VERSION}".encode()
    send(b"API\0" + struct.pack(">I", len(offer)) + offer)
    greeting = receive(wire)
    if len(greeting) != 2 or greeting[0] != VERSION:
        raise ValueError(f"the gateway greeted with {greeting}; the desk reads {VERSION} only")
    send(message(START, 2, CLIENT, ""))
    told: dict[str, list[str]] = {}
    while not {ACCOUNTS, READY} <= told.keys():
        fields = receive(wire)
        told[other(fields)] = fields
    ready = told[READY]
    if len(ready) != 3 or not (ready[2].isascii() and ready[2].isdigit()):
        raise ValueError(f"the gateway is ready with no number for the next order: {ready}")
    return int(ready[2])


def converse(wire: BinaryIO, send: Send) -> Account:
    """Read the account over an open connection: once it is started, ask for every holding
    and every open order, reading until the gateway says both lists are whole. Each order
    is then read with the state the broker last told of it, wherever in the answer it came.
    One told more than once is one order, by the broker's id for it, as last told: the gateway
    tells an order again, unasked, as it settles it (seen of a real stop, 14 November 2026)."""
    start(wire, send)
    send(message(ASK_HOLDINGS, 1) + message(ASK_ORDERS, 1))
    holdings: list[Holding] = []
    orders: list[list[str]] = []
    states: dict[str, tuple[str, Decimal]] = {}
    whole: set[str] = set()
    while not {HOLDINGS_END, ORDERS_END} <= whole:
        fields = receive(wire)
        if fields[0] == HOLDING:
            holdings.append(_holding(fields))
        elif fields[0] == ORDER:
            orders.append(fields)
        elif fields[0] == STATUS:
            states.update([_state(fields)])
        else:
            whole.add(other(fields))
    told = {order.broker_id: order for order in (_order(fields, states) for fields in orders)}
    return Account(tuple(holdings), tuple(told.values()))


def dial(talk: Callable[[BinaryIO, Send], T]) -> T:
    """Hold one conversation with the gateway. It dials the paper port and no other."""
    with (
        socket.create_connection((HOST, PORT), timeout=SECONDS) as link,
        link.makefile("rb") as wire,
    ):
        return talk(wire, link.sendall)


def read() -> Account:
    """The paper account as the gateway gives it now."""
    return dial(converse)


def named(
    held: Mapping[str, int], entries: Iterable[tuple[str, Decimal]], saying: str
) -> tuple[str, ...]:
    """The desk's book against a broker's entries by the desk's one rule (book.differences),
    each difference named in words, saying first what the entries are; and it is said when
    the broker gives a name in more than one entry."""
    rows = list(entries)
    given = Counter(name for name, _ in rows)
    several = {name: f" in one of {n} entries" for name, n in given.items() if n > 1}
    return tuple(
        f"{d.name}: {saying} {d.broker}{several.get(d.name, '')}, the desk's book {d.book}"
        for d in book.differences(held, rows)
    )


def differences(
    account: Account, held: Mapping[str, int], lines: Iterable[Line]
) -> tuple[str, ...]:
    """Every way the paper account's holdings differ from the desk's book, each named in
    words; none, and it holds what the book holds. held is the book (book.positions). The
    door gives the desk's one rule each holding under its symbol, kind and currency, so the
    same name in another currency is another thing. The orders resting on the account are
    told apart and named by the day's check (desk/clearance.py)."""
    known = {line.symbol: line for line in lines}
    unknown = sorted(set(held) - set(known))
    if unknown:
        raise ValueError(f"the book holds lines the desk was not given: {unknown}")
    ours = {own(known[symbol]): shares for symbol, shares in held.items()}
    return named(ours, [(h.name, h.shares) for h in account.holdings], "the broker holds")


def own(line: Line) -> str:
    """The name a holding of the desk's line goes under (Holding.name): a share or a fund,
    in the line's currency."""
    return f"{line.symbol} STK {line.currency}"


if __name__ == "__main__":
    from desk import conformance  #: the command's home; it imports this module, so only here

    sys.exit(conformance.main(sys.argv[1:]))
