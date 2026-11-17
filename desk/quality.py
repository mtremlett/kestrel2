"""quality - THE DATA QUALITY MONITOR (R-RUNNER-217, his ruling of 16 November 2026), first steps:
the daily timeframe, then the rollups. Every line's daily bars are audited against its venue's
calendar (a session with no bar is a gap; a fault is whatever the store's own checks find), each
gap is backfilled by desk/backfill.py (the broker, then the archive), the line is audited again,
and one line is printed: green, or what stays red and why. The coarser timeframes the store
can build (1h, 4h, 1wk) are rolled up from the finer bars it holds, and a built bar that differs
from a pulled one is a red fault. Exit 0 only when green."""

from __future__ import annotations

import os
import sys
from collections.abc import Iterable
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path

from desk import backfill, history_write, keeper, venues
from desk.lines import LINES, Line
from desk.store import Bar
from desk.store import _clean as cleaned


def _missing(line: Line, held: tuple[Bar, ...], today: date) -> list[date]:
    """The sessions from the first held bar to yesterday on which the line holds none."""
    days = {bar.day for bar in held}
    first = min(days, default=today)
    return [d for d in venues.sessions(line.venue, first, today - timedelta(1)) if d not in days]


def audit(path: Path, line: Line, today: date) -> list[str]:
    """What is red about one line's daily bars as of today: its gaps, then each un-noted fault
    the store's checks find on a day that is not itself a gap."""
    held = backfill._held(path, line)
    if not held:
        return [f"{line.symbol}: holds no daily bar"]
    gaps = _missing(line, held, today)
    found = [f for f in cleaned(line, held, today, today)[1] if not f.noted and f.day not in gaps]
    red = [f"{line.symbol}: {len(gaps)} sessions missing, the first {gaps[0]}"] if gaps else []
    return red + [f"{line.symbol}: {f.what}" for f in found]


def gaps(path: Path, lines: Iterable[Line], today: date) -> list[tuple[Line, date]]:
    """Every gap of every line, for the filler."""
    return [
        (line, day) for line in lines for day in _missing(line, backfill._held(path, line), today)
    ]


def rolled(path: Path, line: Line, today: date) -> tuple[int, list[str]]:
    """The line's coarser bars built from its finer ones, and how many landed, with the faults
    where a built bar differs from one held. A line holding no finer bars has nothing to build."""
    now = datetime.combine(today, time(), UTC)
    try:
        landed = history_write.roll(path, line, now)
    except LookupError:  # the store never held this line's 30-minute bars: no rollup to make
        return 0, []
    return landed, history_write.clashes(path, line, now)


def monitor(
    path: Path, lines: Iterable[Line], broker: backfill.Ask, archived: backfill.Ask, today: date
) -> str:
    """Audit, backfill every gap, audit again: the one line saying green, or what stays red."""
    every = list(lines)
    wrote, named = backfill.fill(path, gaps(path, every, today), broker, archived, today)
    built = [rolled(path, line, today) for line in every]
    red = [why for line in every for why in audit(path, line, today)]
    red += [why for _, faults in built for why in faults]
    said = f"{len(wrote)} bars backfilled, {sum(n for n, _ in built)} rolled up"
    if not red:
        return f"quality: green, {len(every)} lines, {said}"
    return f"quality: RED, {said}; {'; '.join(red)}; unfilled {len(named)}"


if __name__ == "__main__":
    home, now = Path(os.environ["KESTREL2_DATA"]), datetime.now(UTC)
    said = monitor(
        home / keeper.HOT, LINES, backfill._broker(home, now), backfill._archive, now.date()
    )
    sys.stdout.write(f"{said}\n")
    sys.exit(0 if " green," in said else 1)
