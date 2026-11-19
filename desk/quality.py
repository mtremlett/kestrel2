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

from desk import backfill, bars, history_write, keeper, venues
from desk.lines import LINES, Line
from desk.spans import EPOCH, FIVE
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


SHORT = (
    "1m",
    "2m",
    FIVE,
    "10m",
    "15m",
    "30m",
)  #: the intraday timeframes audited for thin sessions


def _starts(path: Path, line: Line, span: str, until: datetime) -> list[datetime]:
    """When the line's bars of one short span start, as held; a span never held has none."""
    try:
        if span == FIVE:
            return [b.start for b in bars.five(path, line, EPOCH, until)]
        return [b.start for b in bars.timed(path, line, span, EPOCH, until)]
    except LookupError:  # the store never held this span for the line: nothing to be short of
        return []


def thin(path: Path, line: Line, today: date) -> list[str]:
    """For each short timeframe, the sessions between the first and the last bar held on which
    the line holds none, each named red; where a finer span holds bars on all of them the
    line says it is rollable from that span, else that no source holds them yet."""
    until, red = datetime.combine(today, time(), UTC), []
    finer: dict[str, set[date]] = {}
    for span in SHORT:
        days = {start.date() for start in _starts(path, line, span, until)}
        short = (
            [d for d in venues.sessions(line.venue, min(days), max(days)) if d not in days]
            if days
            else []
        )
        if short:
            base = next((f for f, held in finer.items() if set(short) <= held), None)
            how = f", rollable from {base}" if base else ""
            first = f"{len(short)} sessions with no {span} bar, the first {short[0]}"
            red.append(f"{line.symbol}: {first}{how}")
        if days:
            finer[span] = days
    return red


VOLUME_TOLERANCE = 0.5  #: a day's five-minute volume may exceed the daily bar's by this share


def volumes(path: Path, line: Line, today: date) -> list[str]:
    """The days on which the summed five-minute volume exceeds the daily bar's by more than the
    tolerance (a second feed counted twice). Five-minute bars short of the daily volume are a
    thin session, not a volume fault."""
    total: dict[date, int] = {}
    try:
        fives = bars.five(path, line, EPOCH, datetime.combine(today, time(), UTC))
    except LookupError:  # the store never held five-minute bars for the line: nothing to sum
        return []
    for five in fives:
        total[five.start.date()] = total.get(five.start.date(), 0) + five.volume
    daily = {held.day: held.volume for held in backfill._held(path, line)}
    off = sorted(
        d for d, v in total.items() if d in daily and v > daily[d] * (1 + VOLUME_TOLERANCE)
    )
    if not off:
        return []
    return [
        f"{line.symbol}: {len(off)} days with five-minute volume over the daily, first {off[0]}"
    ]


def monitor(
    path: Path, lines: Iterable[Line], broker: backfill.Ask, archived: backfill.Ask, today: date
) -> str:
    """Audit, backfill every gap, audit again: the one line saying green, or what stays red."""
    every = list(lines)
    wrote, named = backfill.fill(path, gaps(path, every, today), broker, archived, today)
    built = [rolled(path, line, today) for line in every]
    red = [why for line in every for why in audit(path, line, today)]
    red += [why for _, faults in built for why in faults]
    red += [why for line in every for why in thin(path, line, today)]
    red += [why for line in every for why in volumes(path, line, today)]
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
