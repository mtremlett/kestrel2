"""shelf - THE STORE'S FILES: one line's bars and its fault list, each written whole and then
swapped in, so a reader never sees half a write, and read back exactly. It holds no rule."""

from __future__ import annotations

import csv
from collections.abc import Iterable, Sequence
from dataclasses import astuple, dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

from desk.lines import Line

COLUMNS = ("day", "open", "high", "low", "close", "volume")
#: Where a line's older bars wait, in a folder of their own under the store's: the archive gives
#: some lines a day or two, and the store is rebuilt from it on every prepare, so bars brought
#: from elsewhere would be lost. They are joined to the archive's, which wins on any day it gives.
HISTORY = "history"


@dataclass(frozen=True)
class Bar:
    """One session's prices and volume for one line."""

    day: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int


def write(path: Path, header: Sequence[str], rows: Iterable[Sequence[object]]) -> None:
    """A table written whole beside its place, then swapped in."""
    part = path.with_suffix(".part")
    with part.open("w", newline="", encoding="utf-8") as out:
        writer = csv.writer(out)
        writer.writerow(header)
        writer.writerows(rows)
    part.replace(path)


def load(path: Path) -> tuple[Bar, ...]:
    """The bars of one stored file, exactly as written."""
    with path.open(newline="", encoding="utf-8") as stored:
        return tuple(
            Bar(
                date.fromisoformat(row["day"]),
                Decimal(row["open"]),
                Decimal(row["high"]),
                Decimal(row["low"]),
                Decimal(row["close"]),
                int(row["volume"]),
            )
            for row in csv.DictReader(stored)
        )


def shelve(root: Path, line: Line, bars: Iterable[Bar]) -> None:
    """A line's older bars, kept for every prepare to join to the archive's, replacing any
    shelved before. They are cleaned as the archive's are, with it, on each prepare."""
    (root / HISTORY).mkdir(parents=True, exist_ok=True)
    write(root / HISTORY / f"{line.symbol}.csv", COLUMNS, (astuple(bar) for bar in bars))


def read(root: Path, symbol: str) -> tuple[Bar, ...]:
    """Every bar the store kept for one line, oldest first. A parked line keeps the bars that
    can be true, but does not trade."""
    return load(root / f"{symbol}.csv")


def faults(root: Path, symbol: str) -> tuple[str, ...]:
    """Every fault found in a line's bars on the last prepare, the old ones that no longer
    park it included."""
    with (root / f"{symbol}.faults.csv").open(newline="", encoding="utf-8") as stored:
        return tuple(row["fault"] for row in csv.DictReader(stored))
