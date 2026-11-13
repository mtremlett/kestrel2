"""batch - THE LADDER'S BATCH SERVICE: many cells run in turn, each outcome kept as it
finishes, so a bad cell is recorded and the rest carry on, and a restart takes up where the
last run stopped. A result is kept by its key, the code and every bar it read, so a cell is
run again only when one of them has changed.

The journal holds one JSON line per finished cell, appended and forced to disk before the
next cell starts, its line named by symbol and venue, since one symbol can be two companies.
A line a stop cut short is a cell that never finished: it is cut off and
the cell run again. A cell's bars are read on every run, to find its key; only a record
under that key counts as done, so one under other code or other bars does not. A failed
cell is run again, as what failed it may lie outside that code or in data since mended. An
outcome is written only where it differs from the cell's last line, so the last line of a
cell is always its outcome now: a cell that fails the same way every pass of a week does not
grow its journal, and one whose record is found again after a failure has it written again.
A run is refused when the
code on disk is no longer the code the process loaded, since its records would claim code it
is not running: each batch runs in a fresh process, and one process at a time works on a
journal.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from desk import store
from desk.lines import Line
from desk.store import Bar
from lab import cell
from lab.cell import Cell, Key, Record, Trade


@dataclass(frozen=True)
class Failed:
    cell: Cell
    code: str  #: the code version that failed on it
    error: str  #: the exception's type and message


Outcome = Record | Failed
Bars = Callable[[Line], Sequence[Bar]]  #: a line's bars, oldest first
#: what the journal's records hold (bars in the window, trades), by cell, code and data
Kept = dict[tuple[str, ...], tuple[int, tuple[Trade, ...]]]


def stored(root: Path) -> Bars:
    """Each line's bars as the research store at root keeps them: in its venue's folder."""
    return lambda line: store.read(root / line.venue, line.symbol)


def run(cells: Sequence[Cell], bars: Bars, journal: Path) -> tuple[Outcome, ...]:
    """Every cell's outcome, in order; a record the journal holds under its key is not rerun."""
    if cell.code_version() != cell.LOADED:
        raise RuntimeError("the code on disk has changed since this process loaded it")
    kept, last, whole = _resume(journal)
    outcomes: list[Outcome] = []
    with journal.open("ab") as out:
        out.truncate(whole)
        for todo in cells:
            outcome = _one(todo, bars, kept)
            new = _dump(outcome)
            if last.get(tuple(row(todo))) != new:
                out.write(json.dumps(new).encode() + b"\n")
                out.flush()
                os.fsync(out.fileno())
                last[tuple(row(todo))] = new
            if isinstance(outcome, Record):
                kept[_id(outcome.key)] = (outcome.bars, outcome.trades)
            outcomes.append(outcome)
    return tuple(outcomes)


def _one(todo: Cell, bars: Bars, kept: Kept) -> Outcome:
    try:
        line = bars(todo.line)
        key = cell.key(todo, line)
        found = kept.get(_id(key))
        return cell.run(todo, line) if found is None else Record(key, *found)
    except Exception as error:  # noqa: BLE001 - a bad cell is recorded with its error; the rest run
        return Failed(todo, cell.LOADED, f"{type(error).__name__}: {error}")


def _whole(journal: Path) -> bytes:
    """The journal up to a line a stop cut short; nothing where there is none yet."""
    text = journal.read_bytes() if journal.exists() else b""
    return text[: text.rfind(b"\n") + 1]


def rows(journal: Path) -> list[dict[str, Any]]:
    """Every outcome the journal holds, oldest first: a record, or a failure and its error."""
    return [json.loads(line) for line in _whole(journal).splitlines()]


def _resume(journal: Path) -> tuple[Kept, dict[tuple[str, ...], dict[str, Any]], int]:
    """The journal's records by key, each cell's last outcome there, and the journal's length
    up to a line a stop cut short."""
    whole = _whole(journal)
    kept = [json.loads(line) for line in whole.splitlines()]
    found = {(*r["cell"], r["code"], r["data"]): _load(r) for r in kept if "error" not in r}
    return found, {tuple(r["cell"]): r for r in kept}, len(whole)


def _id(key: Key) -> tuple[str, ...]:
    return (*row(key.cell), key.code, key.data)


def _dump(outcome: Outcome) -> dict[str, Any]:
    if isinstance(outcome, Failed):
        return {"cell": row(outcome.cell), "code": outcome.code, "error": outcome.error}
    key, trades = outcome.key, [[_day(t.bought), _day(t.sold)] for t in outcome.trades]
    return {
        "cell": row(key.cell),
        "code": key.code,
        "data": key.data,
        "bars": outcome.bars,
        "trades": trades,
    }


def _load(row: dict[str, Any]) -> tuple[int, tuple[Trade, ...]]:
    return int(row["bars"]), tuple(Trade(_date(b), s and _date(s)) for b, s in row["trades"])


def row(todo: Cell) -> list[str]:
    """A cell as the journal names it: its strategy, its line by symbol and venue, its window."""
    line, window = todo.line, [todo.start.isoformat(), todo.end.isoformat()]
    return [todo.strategy, line.symbol, line.venue, *window]


def _day(day: date | None) -> str | None:
    return None if day is None else day.isoformat()


_date = date.fromisoformat
