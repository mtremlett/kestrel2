"""reference - THE REFERENCE SERIES: a line's daily bars from before the calendar begins,
studied and never traded (R-PAPER-16). They wait in a folder of their own under the store's,
which no trading read looks in, so a reference series cannot be read as a traded line.

The calendar knows no session before 2010, so these bars cannot be checked against one:
each is checked on its own, as the store checks every bar, and a weekend bar is refused."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import astuple
from pathlib import Path

from desk import store
from desk.lines import Line
from desk.store import Bar, Fault

FOLDER = "reference"


def keep(root: Path, line: Line, bars: Sequence[Bar]) -> tuple[Fault, ...]:
    """Clean a line's bars into the reference folder of the store at root, as traded: one
    bar a day, each sound alone. Those that cannot be true are left out and listed."""
    faults: list[Fault] = []
    weekdays = {bar.day for bar in bars if bar.day.weekday() < 5}
    sound = []
    for bar in store._once(bars, faults):  # noqa: SLF001  # the store's own cleaning, not copied
        entered = store._entered(line, bar, weekdays)  # noqa: SLF001  # the store's own cleaning, not copied
        if isinstance(entered, str):
            faults.append(Fault(bar.day, entered))
        else:
            sound.append(entered)
    (root / FOLDER).mkdir(parents=True, exist_ok=True)
    store._write(root / FOLDER / f"{line.symbol}.csv", store.COLUMNS, map(astuple, sound))  # noqa: SLF001  # the store's own cleaning, not copied
    return tuple(faults)


def read(root: Path, symbol: str) -> tuple[Bar, ...]:
    """Every bar kept for a reference series, oldest first."""
    return store._load(root / FOLDER / f"{symbol}.csv")  # noqa: SLF001  # the store's own cleaning, not copied
