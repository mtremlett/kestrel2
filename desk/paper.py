"""paper - THE ONE DOOR TO THE PAPER BROKER: IB Gateway's paper port on this machine, spoken
to with the standard library alone. So far the desk only reads through it: the account's
holdings and the orders resting on it, set against the desk's own book. It places nothing.

The gateway speaks in messages: four bytes of length, then fields each ended by a zero byte,
the first naming the message's kind. The desk offers one version of that language and
refuses any other, so each message it reads has one known shape."""

from __future__ import annotations

import socket
import struct
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import BinaryIO

from desk import book
from desk.lines import LINES, Line

HOST, PORT = "127.0.0.1", 4002  #: the paper port on this machine: the only door the desk dials
CLIENT = 222  #: the desk's own client id at the gateway (docs/DECISIONS.md)
VERSION = "176"  #: the one version of the gateway's language the desk reads
SECONDS = 15  #: a gateway silent for longer has not answered
#: The kinds of message, by the gateway's own numbers.
ACCOUNTS, READY, NEWS, STATUS = "15", "9", "4", "3"
HOLDING, HOLDINGS_END, ORDER, ORDERS_END = "61", "62", "5", "53"
START, ASK_HOLDINGS, ASK_ORDERS = 71, 61, 16  #: what the desk sends: none places an order
#: News of the gateway's price feeds, which this door does not read; any other news stops it.
FEEDS = frozenset({"2103", "2104", "2105", "2106", "2107", "2108", "2119", "2157", "2158"})


class NotPaper(Exception):
    """The gateway answered for an account that is not a paper one: the desk stops there."""


def _paper(code: str) -> str:
    """The account's code, which the broker starts with a D for a paper account alone."""
    if not code.startswith("D"):
        raise NotPaper(f"account {code!r} is not a paper account: this desk is paper only")
    return code


@dataclass(frozen=True)
class Holding:
    account: str
    symbol: str
    kind: str  #: the broker's word for what is held: "STK" is a share or a fund
    currency: str
    shares: Decimal


@dataclass(frozen=True)
class Resting:
    """An order the broker is still working, whoever placed it."""

    broker_id: str  #: the broker's own lasting id for the order
    client: str  #: the client id that placed it
    account: str
    symbol: str
    action: str
    shares: Decimal
    kind: str  #: the broker's word for the order: "STP" a stop, "MKT" at the market

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


def _next(wire: BinaryIO) -> list[str]:
    """The gateway's next message, as its fields."""
    head = wire.read(4)
    size = struct.unpack(">I", head)[0] if len(head) == 4 else 0
    body = wire.read(size)
    if len(head) < 4 or len(body) < size:
        raise ConnectionError("the gateway hung up before its answer was whole")
    return body.decode().split("\0")[:-1]


def _other(fields: list[str]) -> str:
    """A message that is no holding and no order, and its kind: every account it names must
    be a paper one, its news may be of the price feeds only, and a kind the desk does not
    know is refused."""
    kind = fields[0]
    if kind == ACCOUNTS:
        for code in fields[2].split(","):
            _paper(code)
    elif kind == NEWS and fields[3] not in FEEDS:
        raise ConnectionError(f"the gateway says {fields[3]}: {fields[4]}")
    elif kind not in (NEWS, READY, STATUS, HOLDINGS_END, ORDERS_END):
        raise ValueError(f"a message of a kind the desk does not read: {fields}")
    return kind


def _holding(fields: list[str]) -> Holding:
    if len(fields) != 16:
        raise ValueError(f"a holding of a shape the desk does not read: {fields}")
    account, symbol, kind, currency, shares = (fields[n] for n in (2, 4, 5, 11, 14))
    return Holding(_paper(account), symbol, kind, currency, Decimal(shares))


def _order(fields: list[str]) -> Resting:
    """Only the head of the message is read: the line, the order and who placed it."""
    if len(fields) < 26:
        raise ValueError(f"an order of a shape the desk does not read: {fields}")
    symbol, action, shares, kind, account, client, broker_id = (
        fields[n] for n in (3, 13, 14, 15, 20, 24, 25)
    )
    return Resting(broker_id, client, _paper(account), symbol, action, Decimal(shares), kind)


def converse(wire: BinaryIO, send: Callable[[bytes], object]) -> Account:
    """Read the account over an open connection: offer the one version, start as the desk's
    client, and only once the gateway has named its accounts, all paper, ask for every
    holding and every open order, reading until it says both lists are whole."""
    offer = f"v{VERSION}".encode()
    send(b"API\0" + struct.pack(">I", len(offer)) + offer)
    version = _next(wire)[0]
    if version != VERSION:
        raise ValueError(f"the gateway speaks version {version}; the desk reads {VERSION} only")
    send(message(START, 2, CLIENT, ""))
    ready: set[str] = set()
    while not {ACCOUNTS, READY} <= ready:
        ready.add(_other(_next(wire)))
    send(message(ASK_HOLDINGS, 1) + message(ASK_ORDERS, 1))
    holdings: list[Holding] = []
    orders: list[Resting] = []
    whole: set[str] = set()
    while not {HOLDINGS_END, ORDERS_END} <= whole:
        fields = _next(wire)
        if fields[0] == HOLDING:
            holdings.append(_holding(fields))
        elif fields[0] == ORDER:
            orders.append(_order(fields))
        else:
            whole.add(_other(fields))
    return Account(tuple(holdings), tuple(orders))


def read() -> Account:
    """The paper account as the gateway gives it now. It dials the paper port and no other."""
    with (
        socket.create_connection((HOST, PORT), timeout=SECONDS) as link,
        link.makefile("rb") as wire,
    ):
        return converse(wire, link.sendall)


def quiet(account: Account, held: Mapping[str, int], lines: Iterable[Line]) -> tuple[str, ...]:
    """Every way the paper account differs from the desk's book, each named in words; none,
    and the account is quiet: nothing but the desk trades it. held is the book
    (book.positions). A holding is matched by its symbol, kind and currency, so the same
    name in another currency is another thing. Every order resting at the broker is named,
    whoever placed it: the desk rests none of its own on paper yet."""
    known = {line.symbol: line for line in lines}
    unknown = sorted(set(held) - set(known))
    if unknown:
        raise ValueError(f"the book holds lines the desk was not given: {unknown}")
    ours = {(s, "STK", known[s].currency): Decimal(shares) for s, shares in held.items()}
    theirs: dict[tuple[str, str, str], Decimal] = {}
    for h in account.holdings:
        key = (h.symbol, h.kind, h.currency)
        theirs[key] = theirs.get(key, Decimal(0)) + h.shares
    both = sorted(ours.keys() | theirs.keys())
    pairs = ((key, theirs.get(key, Decimal(0)), ours.get(key, Decimal(0))) for key in both)
    differ = [
        f"{' '.join(key)}: the broker holds {broker}, the desk's book {desk}"
        for key, broker, desk in pairs
        if broker != desk
    ]
    working = [
        f"{o.symbol}: an order resting at the broker to {o.action} {o.shares} ({o.kind}, "
        f"the broker's id {o.broker_id}, client {o.client})"
        for o in account.orders
    ]
    return (*differ, *working)


def check(root: Path, ask: Callable[[], Account] = read) -> tuple[str, ...]:
    """The daily read-only check: the paper account as it is now against the desk's book,
    every difference named. Nothing is sent to the broker but questions."""
    return quiet(ask(), book.positions(root), LINES)
