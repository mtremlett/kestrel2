"""simcity_faults: THE BROKER FAULT MATRIX (R-RUNNER-392). Every message class IBKR can send,
crossed with every moment of a send; each cell holds the promises the desk must keep there.
A cell is built (run drives it through the send path) or listed as not yet built, counted and
printed; an unbuilt cell raises NotImplementedError and never passes."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import replace
from pathlib import Path

from desk import book
from desk.broker import Crash, Fault, Pretend
from desk.halt import Blocker, Stopped
from desk.lines import Line
from desk.orders import Order, Settings
from desk.store import Bar

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
#: the built cells, and how the pretend broker plays each (the one send path runs them all):
#: None, the link breaks after the broker filled the buy (Pretend link_breaks: link news 2110,
#: 2157, 1100, 1101, 1102); a Fault, played on the line's first order (DISCONNECT: never
#: received; CRASH: the desk hangs up with the broker holding it)
PLAYS: dict[Cell, Fault | None] = {
    ("2110", "after accept"): None,
    ("2157", "after accept"): None,
    ("1100", "before transmit"): Fault.DISCONNECT,
    ("1100", "after accept"): None,
    ("1101", "after accept"): None,
    ("1102", "after accept"): None,
    ("hang-up", "after accept"): Fault.CRASH,
}
BUILT: frozenset[Cell] = frozenset(PLAYS)


def pretend(cell: Cell, archive: Mapping[Line, Sequence[Bar]]) -> Pretend:
    """The pretend broker set to play the cell on the archive's first line."""
    symbol, play = next(iter(archive)).symbol, PLAYS[cell]
    breaks = {symbol} if play is None else set()
    return Pretend(archive, {} if play is None else {symbol: play}, breaks)


def summary() -> str:
    """The matrix counted: how many cells are built and how many are not yet."""
    unbuilt = len(CELLS) - len(BUILT)
    return f"fault matrix: {len(BUILT)} of {len(CELLS)} cells built, {unbuilt} not yet built"


def _steps(root: Path, broker: Pretend, order: Order, settings: Settings) -> tuple[bool, bool]:
    """The fault, then the steps after it; whether the fault played and trading resumed."""
    try:  #: the fault; the next step settles it
        played = book.send(root, broker, order, settings).blocker is Blocker.BROKER
    except Crash:  #: the desk hung up here: its note stays, the broker has the order
        played = True
    book.send(root, broker, order, settings)
    book.send(root, broker, order, settings)  #: asked once more: answered, never resent
    try:
        blocker = book.send(
            root, broker, replace(order, order_id=f"{order.order_id}-next"), settings
        ).blocker
    except Stopped as refused:  #: the next order refused: trading did not resume
        blocker = refused.blocker
    return played, blocker is None


def run(cell: Cell, root: Path, broker: Pretend, order: Order, settings: Settings) -> list[str]:
    """Send the buy through the cell's fault (the broker, open, holds it for the order's line);
    the promises it broke, none when it kept them all."""
    if cell not in BUILT:
        raise NotImplementedError(f"fault matrix cell {cell} is not yet built")
    try:
        played, resumed = _steps(root, broker, order, settings)
    except book.Alarm as alarm:
        return [f"{PROMISES[3]}: {alarm}"]
    broke = [] if played else ["the cell's fault was not played"]
    if broker.submitted().count(order.order_id) != 1:
        broke.append(PROMISES[0])
    if book.fills(root) != broker.fills() or book.reconcile(root, broker):
        broke.append(PROMISES[1])
    if not resumed or book.killed(root) is not None:
        broke.append(PROMISES[2])
    return broke
