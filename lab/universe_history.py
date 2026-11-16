"""universe_history - THE RESEARCH BARS IN THE HISTORY DATABASE (R-RUNNER-221, 16 November 2026).
Research's daily bars were CSV files in grid/store, filled from Yahoo; the ladder's pound per
dollar a table of closes beside its results. Here both enter market_history.db through the one
writer, each bar keeping its source: a bar the store's shelf also holds (the Stooq matrices'
fill of a missing day) under Source.MATRIX_DAILY, every other under Source.ARCHIVE (Yahoo).
The bars were cleaned by the store when the CSV was written, so they are not judged again. Only
days the database holds no bar for are written, so a second run adds nothing and a bar already
in is never restated. A session with no bar is named, for quality-backfill, never invented.
`python -m lab.universe history` imports the whole research list and the pound."""

from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from desk import bars, store, venues
from desk.bars import Source
from desk.lines import POUND, Line
from desk.store import Bar


def _fill(path: Path, line: Line, source: Source, given: Iterable[Bar]) -> int:
    """The given bars on days the database holds none for, kept under the source; how many."""
    try:
        held = {bar.day for bar in bars.daily(path, line)}
    except (LookupError, FileNotFoundError):  # a line never written holds nothing
        held = set()
    new = [bar for bar in given if bar.day not in held]
    if not new:
        return 0
    with bars.writing(path, source) as opened:
        return opened.days(line, new)


def enter(root: Path, path: Path, line: Line) -> int:
    """The line's bars in the research store at root into the database at path: those the
    store's shelf holds as Stooq's, the rest as Yahoo's. A line with no file enters nothing."""
    folder = root / line.venue
    if not (folder / f"{line.symbol}.csv").is_file():
        return 0
    kept = store.read(folder, line.symbol)
    shelf = folder / store.HISTORY
    stooq = (
        set(store.read(shelf, line.symbol)) if (shelf / f"{line.symbol}.csv").is_file() else set()
    )
    return _fill(path, line, Source.ARCHIVE, (b for b in kept if b not in stooq)) + _fill(
        path, line, Source.MATRIX_DAILY, (b for b in kept if b in stooq)
    )


def enter_pound(table: Path, path: Path) -> int:
    """The ladder's table of the pound's daily closes (one [day, close] a line) into the
    database as its own series, a bar of one price and no volume."""
    rows = map(json.loads, table.read_text(encoding="utf-8").splitlines())
    closes = [(date.fromisoformat(day), Decimal(close)) for day, close in rows]
    return _fill(path, POUND, Source.ARCHIVE, (Bar(d, c, c, c, c, 0) for d, c in closes))


def missing(path: Path, line: Line, until: date) -> tuple[date, ...]:
    """The sessions from the line's first bar to before `until` that the database holds no bar
    for; none for a line it holds nothing of."""
    try:
        held = {bar.day for bar in bars.daily(path, line)}
    except (LookupError, FileNotFoundError):
        return ()
    if not held:
        return ()
    return tuple(
        d for d in venues.sessions(line.venue, min(held), until - timedelta(1)) if d not in held
    )


def run(
    root: Path, path: Path, table: Path, lines: Iterable[Line], named: Iterable[Line], day: date
) -> str:
    """Every line, then the pound, imported; one line saying the bars added and, for the named
    lines (the yardsticks), the sessions missing before day."""
    added = sum(enter(root, path, line) for line in lines)
    pounds = enter_pound(table, path)
    gaps = "".join(
        f"; {line.symbol} has no bar on {', '.join(map(str, lost))}"
        for line in named
        if (lost := missing(path, line, day))
    )
    return f"research history: {added} bars added, {pounds} pound days added{gaps}"
