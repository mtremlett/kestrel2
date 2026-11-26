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

from desk.book_parts import keep
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
    rows = _ledger(root)
    apart = {fill.execution_id for fill in rows if is_foreign(fill.order_id)}
    return tuple(fill for fill in rows if fill.execution_id not in apart)


def found(root: Path) -> tuple[Fill, ...]:
    """THE FILLS FOUND, not traded: on the account under an order id that is not the desk's own."""
    return tuple(fill for fill in _ledger(root) if is_foreign(fill.order_id))


#: each ledger as last read, under the file's (inode, mtime ns, size) then: SimCity asks for the
#: fills some forty times a simulated day, and reading it whole each time hung the deep run; only
#: the newest ledger is kept, so a night of a hundred worlds never holds a hundred ledgers
_READ: dict[Path, tuple[tuple[int, int, int], tuple[Fill, ...]]] = {}


def _ledger(root: Path) -> tuple[Fill, ...]:
    """Every row of the ledger file, the desk's and the found; read again only once it changed."""
    if not (path := root / LEDGER).exists():
        _READ.pop(path, None)
        return ()
    seen = path.stat()
    stamp = (seen.st_ino, seen.st_mtime_ns, seen.st_size)
    if (kept := _READ.get(path)) is None or kept[0] != stamp:
        _READ.clear()
        _READ[path] = kept = (stamp, _parse(path))
    return kept[1]


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
        _READ.pop(root / LEDGER, None)  #: the one writer: the next read is of what it wrote


def adopt(root: Path, line: Line, shares: int, price: Decimal, on: date) -> None:
    """Write a stranger's shares into the ledger as bought on the day at price (the line's last
    close, the broker having given none) under an order of the stranger's own, so the book is
    the broker's and a sale of them can be sent."""
    order_id = f"{on:%Y%m%d}-stranger-{line.symbol}"
    _record(root, [Fill(f"stranger-{on}-{line.symbol}", order_id, line.symbol, shares, price, on)])
