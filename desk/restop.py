"""restop - THE STOP IS SET FROM THE FILL (R-RUNNER-220). A buy is sized on the signal close
and leaves its stop there; once the fill is known the line's stop is moved to the level
under the fill's own price (orders.stop_under), so a gap down puts it under the fill and a
gap up keeps it 10% under its own. Every step looks again and moves a stop only once."""

from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal
from pathlib import Path

from desk import book
from desk.book_parts import keep
from desk.broker import Restopping
from desk.lines import Line
from desk.orders import stop_under


def move(root: Path, broker: Restopping, lines: Iterable[Line]) -> dict[str, Decimal]:
    """Move each held line's resting stop to the level its newest buy's fill is due, and keep
    the level as the desk's own (book.levels) once the broker has it; the lines moved, by
    symbol, with the new level. A level already kept is not sent again, so a step run twice
    moves nothing. A line with no stop resting is left to the day's list (day._bare). Kill
    switch on: nothing is sent."""
    if book.killed(root) is not None:
        return {}
    kept = book.levels(root)
    named = {line.symbol: line for line in lines}
    paid: dict[str, dict[str, list[tuple[int, Decimal]]]] = {}
    for fill in book.fills(root):
        if fill.quantity > 0:
            paid.setdefault(fill.symbol, {}).setdefault(fill.order_id, []).append(
                (fill.quantity, fill.price)
            )
    due: dict[str, tuple[str, Decimal]] = {}
    for symbol in book.positions(root):
        order_id, fills = list(paid[symbol].items())[-1]
        shares = sum(quantity for quantity, _ in fills)
        level = stop_under(named[symbol], sum((q * p for q, p in fills), Decimal(0)) / shares)
        if kept.get(name := f"{order_id}-stop") != level:
            due[symbol] = name, level
    resting = dict(broker.stops()) if due else {}  #: asked only when a stop is to move
    moved: dict[str, Decimal] = {}
    for symbol, (name, level) in due.items():
        if symbol in resting:
            broker.restop(symbol, level)
            kept[name] = level
            keep(root / book.STOPS, [book.LEVELS, *kept.items()])
            moved[symbol] = level
    return moved
