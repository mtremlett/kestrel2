"""book - THE LEDGER AND THE BOOK. Fills are written under the broker's own ids. The book is
the sum of those fills, never the orders the desk meant to send, and reconciling compares
it with the positions the broker reports."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from desk.broker import Fill, Pretend
from desk.orders import Order, Settings


@dataclass(frozen=True)
class Sent:
    order_id: str
    filled: int
    reason: str | None  #: why it did not fill completely; None only when it did


@dataclass(frozen=True)
class RoundTrip:
    buy: Fill
    sell: Fill
    gross: Decimal  #: pounds, before costs
    costs: Decimal  #: pounds, every cost of both legs
    profit: Decimal  #: pounds, gross less costs


def send(root: Path, broker: Pretend, order: Order, settings: Settings) -> Sent:
    """Pass the pre-trade gate, send the order once, record its fills, and leave its stop
    resting at the broker."""
    raise NotImplementedError("book.send: the send path is phase 2")


def fills(root: Path) -> tuple[Fill, ...]:
    raise NotImplementedError("book.fills: the ledger is phase 2")


def positions(root: Path) -> dict[str, int]:
    raise NotImplementedError("book.positions: the book is phase 2")


def round_trips(root: Path) -> tuple[RoundTrip, ...]:
    raise NotImplementedError("book.round_trips: the ledger is phase 2")
