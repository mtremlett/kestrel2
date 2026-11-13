"""store - THE ONE PRICE STORE AND ITS ONE WRITER. Bars are cleaned once, on entry; a line
that cannot be made clean is parked with a reason and a date, and the others carry on.

The store is rebuilt from the archive on every prepare, so a parked line comes back out by
itself on the first day its bars are clean. One file per line, written whole, then swapped
in, so a reader never sees half a write."""

from __future__ import annotations

import csv
from collections.abc import Mapping, Sequence
from dataclasses import astuple, dataclass
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from desk import venues
from desk.lines import Line

#: A close this many times the last one, or this fraction of it, is not a market move: it
#: is a wrong unit (pence among pounds is 100) or a split the archive did not adjust.
JUMP = Decimal("1.6")
COLUMNS = ("day", "open", "high", "low", "close", "volume")


@dataclass(frozen=True)
class Bar:
    day: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int


@dataclass(frozen=True)
class Parked:
    symbol: str
    reason: str
    day: date


def _once(bars: Sequence[Bar], faults: list[str]) -> list[Bar]:
    """One bar per date. A date given twice the same keeps one; given twice differently,
    neither, because the store cannot know which is true."""
    by_day: dict[date, list[Bar]] = {}
    for bar in bars:
        by_day.setdefault(bar.day, []).append(bar)
    once = []
    for day, given in sorted(by_day.items()):
        if len(set(given)) > 1:
            faults.append(f"{day} given {len(given)} times, differently; none kept")
            continue
        if len(given) > 1:
            faults.append(f"{day} given {len(given)} times")
        once.append(given[0])
    return once


def _unsound(bar: Bar, open_days: set[date]) -> str | None:
    """Why a bar cannot be true on its own, or None."""
    if bar.day not in open_days:
        return f"{bar.day} is not a session that has closed"
    if min(bar.open, bar.high, bar.low, bar.close) <= 0 or bar.volume < 0:
        return f"{bar.day} has a price or volume that cannot be"
    if not bar.low <= min(bar.open, bar.close) <= max(bar.open, bar.close) <= bar.high:
        return f"{bar.day} has an open or close outside its high and low"
    return None


def _clean(line: Line, bars: Sequence[Bar], day: date) -> tuple[list[Bar], list[str]]:
    faults: list[str] = []
    first = min((b.day for b in bars), default=day)
    expected = venues.sessions(line.venue, first, day - timedelta(1))
    open_days, kept = set(expected), list[Bar]()
    for bar in _once(bars, faults):
        why = _unsound(bar, open_days)
        if why is None and kept and not 1 / JUMP < bar.close / kept[-1].close < JUMP:
            why = f"{bar.day} closes at {bar.close} after {kept[-1].close}: a wrong unit or split"
        if why is None:
            kept.append(bar)
        else:
            faults.append(why)
    held = {b.day for b in kept}
    missing = [d for d in expected if d not in held]
    if not kept:
        faults.append("no clean bar: every session missing")
    elif missing:
        faults.append(f"{len(missing)} sessions missing, the first {missing[0]}")
    return kept, faults


def _write(path: Path, bars: Sequence[Bar]) -> None:
    part = path.with_suffix(".part")
    with part.open("w", newline="", encoding="utf-8") as out:
        writer = csv.writer(out)
        writer.writerow(COLUMNS)
        writer.writerows(astuple(bar) for bar in bars)
    part.replace(path)


def prepare(root: Path, archive: Mapping[Line, Sequence[Bar]], day: date) -> tuple[Parked, ...]:
    """Clean the archive's bars into the store at root, ready to trade on day."""
    root.mkdir(parents=True, exist_ok=True)
    parked = []
    for line, bars in archive.items():
        kept, faults = _clean(line, bars, day)
        _write(root / f"{line.symbol}.csv", kept)
        if faults:
            parked.append(Parked(line.symbol, "; ".join(faults), day))
    return tuple(parked)


def read(root: Path, symbol: str) -> tuple[Bar, ...]:
    """Every clean bar the store holds for one line, oldest first."""
    with (root / f"{symbol}.csv").open(newline="", encoding="utf-8") as stored:
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
