"""restop - THE STOP IS SET FROM THE FILL (R-RUNNER-220): a buy's stop rests where the line's
market has fallen 10% from the price the buy FILLED at, not from the close it was sized on.
A buy goes with a stop at the signal close's level, before any fill is known; at the next step
each resting stop is moved, once, to its fill's level, and the move is kept."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from pathlib import Path
from typing import Protocol

from desk import book
from desk.lines import Line
from desk.orders import stop_under


class Restops(Protocol):
    """A broker that can move the one stop resting on a line to a new level, for all its shares."""

    def restop(self, symbol: str, level: Decimal) -> None:
        """Rest the line's stop at level in place of the one resting there. Error if none rests."""


def due(root: Path, lines: Mapping[str, Line]) -> dict[str, Decimal]:
    """Each held buy's stop at its fill: "<buy>-stop" to the level under the average price the
    buy filled at, for every buy whose kept level is not that already, so a step run again,
    its levels kept, finds nothing due. Only the newest buy of a line is the line's stop."""
    kept, fills = book.levels(root), book.fills(root)
    held = book.positions(root)
    newest: dict[str, str] = {f.symbol: f.order_id for f in fills if f.quantity > 0}
    out: dict[str, Decimal] = {}
    for symbol, buy in newest.items():
        name = f"{buy}-stop"
        if symbol not in held or name not in kept:
            continue
        bought = [f for f in fills if f.order_id == buy]
        paid = sum((f.price * f.quantity for f in bought), Decimal(0)) / sum(
            f.quantity for f in bought
        )
        if (level := stop_under(lines[symbol], paid)) != kept[name]:
            out[name] = level
    return out


def move(root: Path, broker: Restops, lines: Mapping[str, Line]) -> tuple[str, ...]:
    """Move every stop due (due) to its fill's level, and keep the new level once the broker has
    it; the names moved. A level kept only after the broker rests it: a failure moves nothing
    the book believes."""
    levels, moved = book.levels(root), []
    for name, level in due(root, lines).items():
        symbol = next(f.symbol for f in book.fills(root) if f"{f.order_id}-stop" == name)
        broker.restop(symbol, level)
        levels[name] = level
        book.keep(root / book.STOPS, [book.LEVELS, *levels.items()])
        moved.append(name)
    return tuple(moved)
