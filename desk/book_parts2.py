"""book_parts2 - THE LEDGER FILE: the fills the desk has recorded, read and added to under the
broker's ids, the found ones apart, and the stop levels it rested. desk.book builds on it and gives
these to its callers under the same names."""

from __future__ import annotations

import csv
from collections.abc import Iterable
from datetime import date
from decimal import Decimal
from operator import attrgetter
from pathlib import Path

from desk.book_parts import Rows, add, keep, read_once
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
    return read_once(path, _APART)[0] if path.exists() else ()


def found(root: Path) -> tuple[Fill, ...]:
    """THE FILLS FOUND, not traded: on the account under an order id that is not the desk's own."""
    path = root / LEDGER
    return read_once(path, _APART)[1] if path.exists() else ()


#: the ledger read: the desk's fills, the found, and every row by its fill (_revision), as kept
Apart = tuple[tuple[Fill, ...], tuple[Fill, ...], dict[str, Fill]]


def _told_apart(kept: Apart, rows: list[list[str]]) -> Apart:
    """The ledger's rows told apart once for every ask (read_once): the desk's, and the found;
    a fill added (book_parts.add) is told apart alone, as the ledger keeps one row an execution."""
    new = _fills(rows)
    apart = {fill.execution_id for fill in new if is_foreign(fill.order_id)}
    ours = tuple(f for f in new if f.execution_id not in apart)
    named = {**kept[2], **{_revision(f.execution_id)[0]: f for f in new}}
    return (*kept[0], *ours), (*kept[1], *(f for f in new if is_foreign(f.order_id))), named


def _ledger(root: Path) -> dict[str, Fill]:
    """The ledger by fill (_revision), each at the version kept; read again only once it changed."""
    path = root / LEDGER
    return read_once(path, _APART)[2] if path.exists() else {}


def _body(rows: list[list[str]]) -> list[list[str]]:
    if rows[:1] != [list(COLUMNS)]:
        raise ValueError("not the desk's ledger")
    return rows[1:]


def _fills(rows: list[list[str]]) -> tuple[Fill, ...]:
    """The ledger's rows, every row a fill."""
    return tuple(
        Fill(e, o, y, int(q), Decimal(p), date.fromisoformat(d)) for e, o, y, q, p, d in rows
    )


_APART = Rows(lambda rows: _told_apart(((), (), {}), _body(rows)), _told_apart)


def _revision(execution_id: str) -> tuple[str, int]:
    """An execution id as its fill and version: a correction changes the last part (.01 to .02)."""
    fill, _, last = execution_id.rpartition(".")
    return (fill, int(last)) if last.isdecimal() and fill else (execution_id, 0)


def _record(root: Path, new: Iterable[Fill]) -> None:
    """Add the fills not in the ledger; a corrected fill replaces its earlier version. Fills of
    their own only are added at its end (book_parts.add), so the ledger read is grown by them."""
    kept = _ledger(root)
    held = {fill.execution_id for fill in kept.values()}
    fresh = [fill for fill in new if fill.execution_id not in held]
    named = [_revision(fill.execution_id)[0] for fill in fresh]
    if not fresh:
        return
    alone = len(set(named)) == len(named) and not kept.keys() & set(named)
    if alone and add(root / LEDGER, COLUMNS, map(_row, fresh)):
        return
    latest = dict(kept)
    for fill in fresh:
        name = _revision(fill.execution_id)[0]
        latest[name] = max(latest.get(name, fill), fill, key=lambda f: _revision(f.execution_id)[1])
    if tuple(latest.values()) != tuple(kept.values()):
        keep(root / LEDGER, [COLUMNS, *map(_row, latest.values())])


_row = attrgetter(*COLUMNS)  #: a fill as the ledger keeps it: its fields, never deep-copied


def adopt(root: Path, line: Line, shares: int, price: Decimal, on: date) -> None:
    """Write a stranger's shares into the ledger as bought on the day at price (the line's last
    close, the broker having given none) under an order of the stranger's own, so the book is
    the broker's and a sale of them can be sent."""
    order_id = f"{on:%Y%m%d}-stranger-{line.symbol}"
    _record(root, [Fill(f"stranger-{on}-{line.symbol}", order_id, line.symbol, shares, price, on)])
