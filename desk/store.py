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

#: Two neighbouring bars whose prices sit further apart than this factor (a fall of 37.5%,
#: a rise of 60%) are not taken as a market move: a wrong unit (pence among pounds is 100),
#: a bad print, or a split of 2-for-1 or more that the archive did not adjust. A smaller
#: wrong factor - a 3-for-2 split, pounds read as dollars - cannot be told from a real move
#: by price alone, and passes.
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


def _unsound(line: Line, bar: Bar, open_days: set[date]) -> str | None:
    """Why a bar cannot be true on its own, or None."""
    prices = (bar.open, bar.high, bar.low, bar.close)
    if bar.day not in open_days:
        return f"{bar.day} is not a closed session on the {line.venue} calendar"
    if not all(p.is_finite() and p > 0 for p in prices) or bar.volume < 0:
        return f"{bar.day} has a price or volume that cannot be"
    if not bar.low <= min(bar.open, bar.close) <= max(bar.open, bar.close) <= bar.high:
        return f"{bar.day} has an open or close outside its high and low"
    return None


def _agree(line: Line, before: Bar, after: Bar) -> bool:
    """Two neighbouring bars could both be true: each one's whole range lies within a
    market's move of the other's close, or the line records this very close as a real move."""

    def near(bar: Bar, close: Decimal) -> bool:
        return close / JUMP <= bar.low and bar.high <= close * JUMP

    confirmed = dict(line.real_moves).get(after.day)
    if confirmed is not None:
        return after.close == confirmed and near(after, after.close)
    return near(after, before.close) and near(before, after.close)


def _stray(at: int, links: Sequence[bool]) -> bool:
    """A bar out of line with every neighbour, where links[n] says bars n and n+1 agree. A bar
    at either end is a stray only if its one neighbour agrees with the bar beyond it; with two
    bars there is no telling which is wrong, so neither is."""
    left = links[at - 1] if at > 0 else None
    right = links[at] if at < len(links) else None
    if left is None or right is None:
        own, beyond = (right, links[1:2]) if left is None else (left, links[-2:-1])
        return own is False and list(beyond) == [True]
    return not left and not right


def _priced(line: Line, sound: Sequence[Bar], faults: list[str]) -> list[Bar]:
    """Drop a lone bar out of line with its neighbours; keep a lasting step in the price, but
    as a fault, until the line records it as a real move."""
    links = [_agree(line, a, b) for a, b in zip(sound, sound[1:], strict=False)]
    kept: list[Bar] = []
    for at, bar in enumerate(sound):
        if _stray(at, links):
            faults.append(f"{bar.day} is out of line with the days either side: a wrong unit")
            continue
        if kept and not _agree(line, kept[-1], bar):
            faults.append(
                f"{bar.day} moved from {kept[-1].close} to {bar.close}: a split the archive "
                "did not adjust, or a real move the line does not record"
            )
        kept.append(bar)
    return kept


def _clean(line: Line, bars: Sequence[Bar], day: date) -> tuple[list[Bar], list[str]]:
    """The bars of one line that can be true, and every fault found on the way."""
    faults: list[str] = []
    first = min((b.day for b in bars if b.day.year in venues.KNOWN), default=day)
    expected = venues.sessions(line.venue, first, day - timedelta(1))
    open_days, sound = set(expected), []
    for bar in _once(bars, faults):
        why = _unsound(line, bar, open_days)
        if why is None:
            sound.append(bar)
        else:
            faults.append(why)
    kept = _priced(line, sound, faults)
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
    """Every bar the store kept for one line, oldest first. A parked line keeps the bars that
    can be true, but does not trade."""
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
