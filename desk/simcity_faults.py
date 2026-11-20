"""simcity_faults: THE BROKER FAULT MATRIX (R-RUNNER-392). Every message class IBKR can send,
crossed with every moment of a send; each cell holds the promises the desk must keep there.
A cell is built (run drives it through the send path) or listed as not yet built, counted and
printed; an unbuilt cell raises NotImplementedError and never passes."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from desk import book
from desk.broker import Fault, Pretend
from desk.halt import Blocker
from desk.orders import Order, Settings

CLASSES = (
    "1100", "1101", "1102", *(str(n) for n in range(2103, 2159)),  # fmt: skip
    "201", "202", "10147", "100", "162", "hang-up",
)  # fmt: skip
MOMENTS = (
    "before transmit", "after accept", "after a part fill", "while resting the stop",
    "during recovery",
)  # fmt: skip
PROMISES = (
    "no order sent twice",
    "the book equals the broker after the next step",
    "trading resumes without the operator",
    "the kill switch only for a true unknown",
)
Cell = tuple[str, str]
CELLS: tuple[Cell, ...] = tuple((c, m) for c in CLASSES for m in MOMENTS)
#: the built cells and the fault each injects: the Friday 20 November blip, link news (2110,
#: 2157) after the broker accepted a buy
BUILT: dict[Cell, Fault] = {
    ("2110", "after accept"): Fault.LINK,
    ("2157", "after accept"): Fault.LINK,
}


def summary() -> str:
    """The matrix counted: how many cells are built and how many are not yet."""
    unbuilt = len(CELLS) - len(BUILT)
    return f"fault matrix: {len(BUILT)} of {len(CELLS)} cells built, {unbuilt} not yet built"


def run(cell: Cell, root: Path, broker: Pretend, order: Order, settings: Settings) -> list[str]:
    """Send the buy through the cell's fault (the broker, open, holds it for the order's line);
    the promises it broke, none when it kept them all."""
    if cell not in BUILT:
        raise NotImplementedError(f"fault matrix cell {cell} is not yet built")
    broke, nxt = [], replace(order, order_id=f"{order.order_id}-next")
    try:
        book.send(root, broker, order, settings)  #: the fault; the next step settles it
        book.send(root, broker, order, settings)
        resumed = book.send(root, broker, nxt, settings)
    except book.Alarm as alarm:
        return [f"{PROMISES[3]}: {alarm}"]
    if broker.submitted().count(order.order_id) != 1:
        broke.append(PROMISES[0])
    if book.fills(root) != broker.fills() or book.reconcile(root, broker):
        broke.append(PROMISES[1])
    if resumed.blocker is Blocker.BROKER or book.killed(root) is not None:
        broke.append(PROMISES[2])
    return broke
