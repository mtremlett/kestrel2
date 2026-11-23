"""history_bars - THE LADDER'S BARS FROM THE HISTORY DATABASE (R-RUNNER-222, 16 November 2026).
Every set of the ladder (EPON, leveraged, first) reads its daily bars, its lines and the pound
per dollar from market_history.db alone, where `lab/universe_history.py` put them: no
grid/store folder, no market_live.db. A line the database lacks is named, never guessed."""

from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from contextlib import closing
from datetime import date
from decimal import Decimal
from functools import lru_cache
from pathlib import Path

from desk import bars
from desk.lines import Line
from desk.store import Bar
from lab import ladder, universe
from lab.batch import Bars

FACTS = "SELECT at, value FROM fact WHERE kind = 'macro' AND subject = ? ORDER BY at"
HELD = "SELECT venue, symbol FROM held WHERE span = ?"


def database(home: Path) -> Path:
    """The store's short database in the data folder; the long one, market_history.db, is
    beside it, and is the only one read here."""
    return home / bars.LIVE


def lines(home: Path) -> tuple[Line, ...]:
    """The research list's lines the history database holds daily bars for, in the list's order."""
    file = bars.files(database(home))[bars.DAILY]
    if not file.is_file():
        raise FileNotFoundError(f"{file}: no history database to take the ladder's lines from")
    with closing(sqlite3.connect(file)) as held:
        kept = set(held.execute(HELD, (bars.DAILY,)).fetchall())
    return tuple(line for line in universe.UNIVERSE if (line.venue, line.symbol) in kept)


def reader(home: Path) -> Bars:
    """Each line's daily bars to the window's end, as a worker makes them for itself; a line
    the database lacks raises LookupError naming it."""
    path = database(home)

    def read(line: Line) -> Sequence[Bar]:
        return [bar for bar in bars.daily(path, line) if bar.day <= ladder.END]

    return lru_cache(maxsize=4)(read)


def facts(home: Path, series: str) -> dict[date, Decimal]:
    """One macro series' observations from the history database's facts, by day. Read only; a
    database without facts, or a day holding two values, raises naming the series."""
    file = bars.files(database(home))[bars.DAILY]
    if not file.is_file():
        raise FileNotFoundError(f"{file}: no history database to take {series} from")
    with closing(sqlite3.connect(f"{file.as_uri()}?mode=ro", uri=True)) as held:
        rows = held.execute(FACTS, (series,)).fetchall()
    found = {date.fromisoformat(at): Decimal(value) for at, value in rows}
    if len(found) != len(rows):
        raise ValueError(f"{series}: a day holds two values in the history database")
    return found


def pounds(home: Path) -> dict[date, Decimal]:
    """Pounds per dollar for each day, by the ladder's one rule, from the pound's closes in the
    history database; a database without the pound raises LookupError naming it."""
    path = database(home)
    return ladder.rates(
        lambda pound, before: [b for b in bars.daily(path, pound) if b.day < before]
    )
