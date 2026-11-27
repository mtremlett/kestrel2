"""book_parts2 - THE LEDGER FILE: the fills the desk has recorded, read and added to under the
broker's ids, the found ones apart, and the stop levels it rested. desk.book builds on it and gives
these to its callers under the same names."""

from __future__ import annotations

import csv
from collections.abc import Iterable
from dataclasses import astuple
from datetime import date
from decimal import Decimal
from pathlib import Path

from desk.book_parts import keep, read_once
from desk.broker import Fill
from desk.handpark import is_foreign
from desk.lines import Line

LEDGER = "ledger.csv"
STOPS, LEVELS = "stops.csv", ("stop", "level")  #: each buy's stop level, kept as the buy goes
COLUMNS = ("execution_id", "order_id", "symbol", "quantity", "price", "day")


def levels(root: Path) -> dict[str, Decimal]:
    """THE STOPS THE DESK RESTED, by buy ("<buy>-stop"): a history, not a register of live ones."""
    if not (path := root / STOPS).exists():
        return {}
    with path.open(newline="", encoding="utf-8") as kept:
        rows = list(csv.reader(kept))
    if rows[:1] != [list(LEVELS)]:
        raise ValueError(f"{path}: not the desk's stop levels")
    return {name: Decimal(level) for name, level in rows[1:]}


def fills(root: Path) -> tuple[Fill, ...]:
    """Every fill the desk has recorded, in the order it learned of them; found ones are apart."""
    path = root / LEDGER
    return read_once(path, _apart)[0] if path.exists() else ()


def found(root: Path) -> tuple[Fill, ...]:
    """THE FILLS FOUND, not traded: on the account under an order id that is not the desk's own."""
    path = root / LEDGER
    return read_once(path, _apart)[1] if path.exists() else ()


def _apart(path: Path) -> tuple[tuple[Fill, ...], tuple[Fill, ...]]:
    """The ledger's rows told apart once for every ask (read_once): the desk's, and the found."""
    rows = read_once(path, _parse)
    apart = {fill.execution_id for fill in rows if is_foreign(fill.order_id)}
    return tuple(f for f in rows if f.execution_id not in apart), tuple(
        f for f in rows if is_foreign(f.order_id)
    )


def _ledger(root: Path) -> tuple[Fill, ...]:
    """Every row of the ledger file, the desk's and the found; read again only once it changed."""
    path = root / LEDGER
    return read_once(path, _parse) if path.exists() else ()


def _parse(path: Path) -> tuple[Fill, ...]:
    """The ledger file read whole, every row a fill."""
    with path.open(newline="", encoding="utf-8") as ledger:
        rows = csv.reader(ledger)
        if next(rows, None) != list(COLUMNS):
            raise ValueError(f"{path}: not the desk's ledger")
        return tuple(
            Fill(e, o, y, int(q), Decimal(p), date.fromisoformat(d)) for e, o, y, q, p, d in rows
        )


def _revision(execution_id: str) -> tuple[str, int]:
    """An execution id as its fill and version: a correction changes the last part (.01 to .02)."""
    fill, _, last = execution_id.rpartition(".")
    return (fill, int(last)) if last.isdecimal() and fill else (execution_id, 0)


def _record(root: Path, new: Iterable[Fill]) -> None:
    """Add the fills not in the ledger; a corrected fill replaces its earlier version."""
    kept = _ledger(root)
    latest = {_revision(f.execution_id)[0]: f for f in kept}
    for fill in new:
        name = _revision(fill.execution_id)[0]
        latest[name] = max(latest.get(name, fill), fill, key=lambda f: _revision(f.execution_id)[1])
    if tuple(latest.values()) != tuple(kept):
        keep(root / LEDGER, [COLUMNS, *(astuple(fill) for fill in latest.values())])


def adopt(root: Path, line: Line, shares: int, price: Decimal, on: date) -> None:
    """Write a stranger's shares into the ledger as bought on the day at price (the line's last
    close, the broker having given none) under an order of the stranger's own, so the book is
    the broker's and a sale of them can be sent."""
    order_id = f"{on:%Y%m%d}-stranger-{line.symbol}"
    _record(root, [Fill(f"stranger-{on}-{line.symbol}", order_id, line.symbol, shares, price, on)])
