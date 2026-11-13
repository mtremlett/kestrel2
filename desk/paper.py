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
from typing import BinaryIO, TypeVar

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
Send = Callable[[bytes], object]  #: what puts the desk's bytes on the connection
T = TypeVar("T")


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
    does not know is refused."""
    kind = fields[0]
    if len(fields) < {ACCOUNTS: 3, NEWS: 5}.get(kind, 1):
        raise ValueError(f"a message from the gateway cut short: {fields}")
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


def start(wire: BinaryIO, send: Send) -> None:
    """Open a conversation: offer the one version, start as the desk's client, and read
    until the gateway is ready and has named its accounts, all paper. Nothing is asked
    before."""
    offer = f"v{VERSION}".encode()
    send(b"API\0" + struct.pack(">I", len(offer)) + offer)
    greeting = receive(wire)
    if len(greeting) != 2 or greeting[0] != VERSION:
        raise ValueError(f"the gateway greeted with {greeting}; the desk reads {VERSION} only")
    send(message(START, 2, CLIENT, ""))
    ready: set[str] = set()
    while not {ACCOUNTS, READY} <= ready:
        ready.add(other(receive(wire)))


def converse(wire: BinaryIO, send: Send) -> Account:
    """Read the account over an open connection: once it is started, ask for every holding
    and every open order, reading until the gateway says both lists are whole."""
    start(wire, send)
    send(message(ASK_HOLDINGS, 1) + message(ASK_ORDERS, 1))
    holdings: list[Holding] = []
    orders: list[Resting] = []
    whole: set[str] = set()
    while not {HOLDINGS_END, ORDERS_END} <= whole:
        fields = receive(wire)
        if fields[0] == HOLDING:
            holdings.append(_holding(fields))
        elif fields[0] == ORDER:
            orders.append(_order(fields))
        else:
            whole.add(other(fields))
    return Account(tuple(holdings), tuple(orders))


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


def differences(
    account: Account, held: Mapping[str, int], lines: Iterable[Line]
) -> tuple[str, ...]:
    """Every way the paper account differs from the desk's book, each named in words; none,
    and nothing but the desk trades the account. held is the book (book.positions). A
    holding is matched by its symbol, kind and currency, so the same name in another
    currency is another thing. Each row the broker gives must be the book's own shares:
    rows that only add up to them are two places, or a change while it was read. Every
    order resting at the broker is named, whoever placed it: the desk rests none yet."""
    known = {line.symbol: line for line in lines}
    unknown = sorted(set(held) - set(known))
    if unknown:
        raise ValueError(f"the book holds lines the desk was not given: {unknown}")
    ours = {(s, "STK", known[s].currency): Decimal(shares) for s, shares in held.items()}
    rows = [((h.symbol, h.kind, h.currency), h.shares) for h in account.holdings]
    rows += [(key, Decimal(0)) for key in ours.keys() - {key for key, _ in rows}]
    differ = [
        f"{' '.join(key)}: the broker holds {shares}, the desk's book {ours.get(key, 0)}"
        for key, shares in sorted(rows)
        if shares != ours.get(key, 0)
    ]
    working = [
        f"{o.symbol}: an order resting at the broker to {o.action} {o.shares} ({o.kind}, "
        f"the broker's id {o.broker_id}, client {o.client})"
        for o in account.orders
    ]
    return (*differ, *working)


def mismatches(root: Path, ask: Callable[[], Account] = read) -> tuple[str, ...]:
    """The daily read-only check: the paper account as it is now against the desk's book,
    every difference named; none, and the account is quiet. Nothing is sent to the broker
    but questions."""
    return differences(ask(), book.positions(root), LINES)
