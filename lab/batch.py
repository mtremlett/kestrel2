"""batch - THE LADDER'S BATCH SERVICE: many cells run in turn, each outcome kept as it
finishes, so a bad cell is recorded and the rest carry on, and a restart takes up where the
last run stopped.

The journal holds one JSON line per finished cell, appended and forced to disk before the
next cell starts. A line a stop cut short is a cell that never finished: it is cut off and
the cell run again. Only records under the code this process runs (`cell.LOADED`) count as
done; a failed cell is run again, as what failed it may lie outside that code or in data
since mended. A run is refused when the code on disk is no longer the code the process
loaded, since its records would claim code it is not running: each batch runs in a fresh
process, and one process at a time works on a journal.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from desk.store import Bar
from lab import cell
from lab.cell import Cell, Key, Record, Trade


@dataclass(frozen=True)
class Failed:
    cell: Cell
    code: str  #: the code version that failed on it
    error: str  #: the exception's type and message


Outcome = Record | Failed
Bars = Callable[[str], Sequence[Bar]]  #: a line's bars by its symbol, oldest first


def run(cells: Sequence[Cell], bars: Bars, journal: Path) -> tuple[Outcome, ...]:
    """Every cell's outcome, in order; a cell the journal holds a record of is not rerun."""
    if cell.code_version() != cell.LOADED:
        raise RuntimeError("the code on disk has changed since this process loaded it")
    done, whole = _resume(journal)
    with journal.open("ab") as out:
        out.truncate(whole)
        for todo in cells:
            if todo not in done:
                done[todo] = _one(todo, bars)
                out.write(json.dumps(_dump(done[todo])).encode() + b"\n")
                out.flush()
                os.fsync(out.fileno())
    return tuple(done[todo] for todo in cells)


def _one(todo: Cell, bars: Bars) -> Outcome:
    try:
        return cell.run(todo, bars(todo.symbol))
    except Exception as error:  # noqa: BLE001 - a bad cell is recorded with its error; the rest run
        return Failed(todo, cell.LOADED, f"{type(error).__name__}: {error}")


def _resume(journal: Path) -> tuple[dict[Cell, Outcome], int]:
    """The journal's records under this code, and its length up to a line a stop cut short."""
    text = journal.read_bytes() if journal.exists() else b""
    whole = text[: text.rfind(b"\n") + 1]
    rows = (json.loads(line) for line in whole.splitlines())
    kept = (_load(row) for row in rows if row["code"] == cell.LOADED and "error" not in row)
    return {record.key.cell: record for record in kept}, len(whole)


def _dump(outcome: Outcome) -> dict[str, Any]:
    if isinstance(outcome, Failed):
        return {"cell": _row(outcome.cell), "code": outcome.code, "error": outcome.error}
    key, trades = outcome.key, [[_day(t.bought), _day(t.sold)] for t in outcome.trades]
    return {
        "cell": _row(key.cell),
        "code": key.code,
        "data": key.data,
        "bars": outcome.bars,
        "trades": trades,
    }


def _load(row: dict[str, Any]) -> Record:
    name, symbol, start, end = row["cell"]
    found = Cell(name, symbol, _date(start), _date(end))
    trades = tuple(Trade(_date(b), s and _date(s)) for b, s in row["trades"])
    return Record(Key(found, row["code"], row["data"]), row["bars"], trades)


def _row(todo: Cell) -> list[str]:
    return [todo.strategy, todo.symbol, todo.start.isoformat(), todo.end.isoformat()]


def _day(day: date | None) -> str | None:
    return None if day is None else day.isoformat()


_date = date.fromisoformat
