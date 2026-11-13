"""book - THE LEDGER AND THE BOOK. Fills are written under the broker's own ids. The book is
the sum of those fills, never the orders the desk meant to send, and reconciling compares
it with the positions the broker reports."""

from __future__ import annotations

import csv
from collections.abc import Iterable
from dataclasses import astuple, dataclass
from decimal import Decimal
from pathlib import Path

from desk.broker import Disconnected, Fill, Pretend
from desk.orders import Order, Settings, gate

LEDGER = "ledger.csv"
COLUMNS = ("execution_id", "order_id", "symbol", "quantity", "price")


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
    """Ask the broker what it did with the order's id, so a desk that restarts never sends
    it twice; if it never received it, pass the pre-trade gate and send it. Its fills are
    recorded and its stop rests at the broker."""
    report = broker.report(order.order_id)
    if report is None:
        gate(order, settings)
        try:
            report = broker.place(order)
        except Disconnected as lost:  #: never received: stated, and sent again next time
            return Sent(order.order_id, 0, str(lost))
    _record(root, report.fills)
    return Sent(order.order_id, sum(fill.quantity for fill in report.fills), report.reason)


def fills(root: Path) -> tuple[Fill, ...]:
    """Every fill the desk has recorded, in the order it learned of them."""
    path = root / LEDGER
    if not path.exists():
        return ()
    with path.open(newline="", encoding="utf-8") as ledger:
        rows = list(csv.DictReader(ledger))
    return tuple(
        Fill(r["execution_id"], r["order_id"], r["symbol"], int(r["quantity"]), Decimal(r["price"]))
        for r in rows
    )


def _record(root: Path, new: Iterable[Fill]) -> None:
    """Add the fills not already in the ledger, under the broker's execution ids. The ledger
    is written whole, then swapped in, so a desk that dies mid-write leaves the old one."""
    ledger = fills(root)
    known = {fill.execution_id for fill in ledger}
    added = tuple(fill for fill in new if fill.execution_id not in known)
    if not added:
        return
    root.mkdir(parents=True, exist_ok=True)
    path = root / LEDGER
    written = path.with_suffix(".tmp")
    with written.open("w", newline="", encoding="utf-8") as out:
        csv.writer(out).writerows([COLUMNS, *(astuple(fill) for fill in ledger + added)])
    written.replace(path)


def positions(root: Path) -> dict[str, int]:
    raise NotImplementedError("book.positions: the book is phase 2")


def round_trips(root: Path) -> tuple[RoundTrip, ...]:
    raise NotImplementedError("book.round_trips: the ledger is phase 2")
