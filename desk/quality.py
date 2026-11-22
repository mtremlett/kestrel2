"""quality - THE DATA QUALITY MONITOR (R-RUNNER-217, his ruling of 16 November 2026), first steps:
the daily timeframe, then the rollups. Every line's daily bars are audited against its venue's
calendar (a session with no bar is a gap; a fault is whatever the store's own checks find), each
gap is backfilled by desk/backfill.py (the broker, then the archive), the line is audited again,
and one line is printed: green, or what stays red and why. The coarser timeframes the store
can build (1h, 4h, 1wk) are rolled up from the finer bars it holds, and a built bar that differs
from a pulled one is a red fault. Exit 0 only when green."""

from __future__ import annotations

import os
import shutil
import sys
from collections.abc import Iterable
from datetime import UTC, date, datetime, time, timedelta
from functools import partial
from pathlib import Path

from desk import backfill, bars, coverage, history_write, keeper, venues
from desk.bars import Source
from desk.lines import LINES, Line
from desk.spans import EPOCH, FIVE
from desk.store import Bar
from desk.store import _clean as cleaned


def _missing(line: Line, held: tuple[Bar, ...], today: date) -> list[date]:
    """The sessions from the first held bar to yesterday on which the line holds none."""
    days = {bar.day for bar in held}
    first = min(days, default=today)
    return [d for d in venues.sessions(line.venue, first, today - timedelta(1)) if d not in days]


def _through(line: Line, now: datetime) -> date:
    """The day before which the store's checks hold sessions closed: today once the venue's
    session of today has closed (its auction ended) by now, else the day after it is excluded."""
    today = now.date()
    traded = venues.sessions(line.venue, today, today) == (today,)
    return (
        today + timedelta(1) if traded and venues.hours(line.venue, today).auction <= now else today
    )


def audit(path: Path, line: Line, now: datetime) -> list[str]:
    """What is red about one line's daily bars as of now: its gaps, then each un-noted fault
    the store's checks find on a day that is not itself a gap. A session closed by now counts."""
    today, held = now.date(), backfill._held(path, line)
    if not held:
        return [f"{line.symbol}: holds no daily bar"]
    gaps = _missing(line, held, today)
    found = [
        f
        for f in cleaned(line, held, _through(line, now), today)[1]
        if not f.noted and f.day not in gaps
    ]
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
    return history_write.roll(path, line, now), history_write.clashes(path, line, now)


SHORT = (
    "1m",
    "2m",
    FIVE,
    "10m",
    "15m",
    "30m",
    "1h",
    "4h",
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
            how = f", rollable from {base}" if base else ", no source holds them yet"
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


BASIS = {  #: sources whose prices are one adjustment basis; any other source is its own
    bars.Source.IBKR: "IBKR",
    bars.Source.IBKR_DAILY: "IBKR",
    bars.Source.BACKFILL: "archive",
    bars.Source.ARCHIVE: "archive",
}


def basis(path: Path, line: Line) -> list[str]:
    """Red when the line's daily series is kept from more than one adjustment basis (a rule
    reading across a basis change sees a false jump); the bases are named, IBKR's first."""
    try:
        held = bars.sources(path, line, bars.DAILY)
    except LookupError:  # the store never held this line's daily bars: no basis to mix
        return []
    named = {BASIS.get(source, source.value) for source in held}
    if len(named) < 2:
        return []
    return [f"{line.symbol}: daily series mixes bases: {', '.join(sorted(named))}"]


def covered(path: Path, lines: list[Line], now: datetime) -> tuple[str, bool]:
    """The desk's coverage score said in words, and whether the parked share is within its cap."""
    held = {}
    for line in lines:
        try:
            held[line.symbol] = len(bars.daily(path, line))
        except LookupError:  # the store never held this line's daily bars: no sessions
            held[line.symbol] = 0
    parked = keeper.parked_live(path, lines, now)
    score = coverage.desk_score(coverage.measure(held, parked))
    return f"coverage {score:.2f}", coverage.parked_within_cap(held, parked)


FREE_FLOOR = 0.10  # the share of its drive the store's folder must leave free (OPS-07)


def disk(home: Path) -> list[str]:
    """Red when the drive holding the store has less than FREE_FLOOR of itself free."""
    usage = shutil.disk_usage(home)
    share = usage.free / usage.total
    if share >= FREE_FLOOR:
        return []
    return [f"disk: {share:.0%} free on the drive of {home.name}, floor {FREE_FLOOR:.0%}"]


def monitor(
    path: Path, lines: Iterable[Line], broker: backfill.Ask, archived: backfill.Ask, now: datetime
) -> str:
    """Audit, backfill every gap, audit again: the one line saying green, or what stays red."""
    every, today = list(lines), now.date()
    asks: backfill.Asks = (
        *backfill.ordered(broker, archived),
        (Source.ROLLUP_5M, partial(bars.rolled_day, path)),
    )
    wrote, named = backfill.fill(path, gaps(path, every, today), asks, today)
    built = [rolled(path, line, today) for line in every]
    red = [why for line in every for why in audit(path, line, now)]
    red += [why for _, faults in built for why in faults]
    red += [why for line in every for why in thin(path, line, today)]
    red += [why for line in every for why in volumes(path, line, today)]
    red += [why for line in every for why in basis(path, line)]
    red += disk(path.parent)
    score, within = covered(path, every, now)
    if not within:
        red.append(f"parked lines exceed {coverage.PARKED_CAP:.0%} of the lines")
    said = f"{len(wrote)} bars backfilled, {sum(n for n, _ in built)} rolled up, {score}"
    if not red:
        return f"quality: green, {len(every)} lines, {said}"
    return f"quality: RED, {said}; {'; '.join(red)}; unfilled {len(named)}"


GOLDEN = ("SPY", "QQQ", "VUAG", "IITU")  #: always green, or the table says why (his 22 Nov)
OFFERED = {"VUAG": ("1m", "15m", "30m", "4h")}  #: spans a line's venue never supplies: not a gap
HOVER_SPANS = ("5m", "15m", "30m", "1h", "4h", "daily", "1wk", "1m")  #: every span, as stored
REMIND = timedelta(minutes=30)  #: while red, one reminder this often


def _last_session(line: Line, now: datetime) -> date:
    """The last session of the line's venue that had ended by now."""
    for back in range(10):
        day = now.date() - timedelta(back)
        if venues.sessions(line.venue, day, day) and venues.hours(line.venue, day).auction <= now:
            return day
    raise LookupError(f"{line.venue}: no session ended in the ten days to {now}")


def cell(path: Path, line: Line, span: str, now: datetime) -> str | None:
    """None when the line's newest bar of one span is of its venue's last ended session (a
    week's: of that week or the one before); else why: the span holds no bar, or how far behind."""
    name = FIVE if span == "5m" else span
    try:
        got = bars.newest(path, line, name)
    except LookupError:  # the store never held this span for the line: a gap, said in words
        got = None
    if got is None:
        return "holds no bar"
    due = _last_session(line, now)
    at = date.fromordinal(got[0]) if name == "daily" else (EPOCH + timedelta(seconds=got[0])).date()
    if name == "1wk":
        due -= timedelta(due.weekday() + 7)
    return None if at >= due else f"newest {at}, last session {due}"


def hover(path: Path, lines: Iterable[Line], now: datetime) -> tuple[str, bool]:
    """Every line x span judged against the venue's last ended session: the one line saying the
    share fresh, the faults (held but behind), the gaps (no bar) and the worst cell, and whether
    it is green: every golden line fresh at every span its venue supplies."""
    cells = [
        (f"{line.symbol}/{span}", line, cell(path, line, span, now))
        for line in lines
        for span in HOVER_SPANS
        if span not in OFFERED.get(line.symbol, ())
    ]
    bad = [(name, line, why) for name, line, why in cells if why]
    gap = sum(why == "holds no bar" for _, _, why in bad)
    worst = (bad[0][0] + ": " + bad[0][2]) if bad else "none"
    share = 100 * (len(cells) - len(bad)) // max(len(cells), 1)
    said = f"data quality: {share}% fresh, {len(bad) - gap} faults, {gap} gaps, worst {worst}"
    return said, not any(line.symbol in GOLDEN for _, line, _ in bad)


def alarm(
    since: datetime | None, sent: datetime | None, green: bool, why: str, now: datetime
) -> tuple[datetime | None, datetime | None, str | None]:
    """The alarm that tells only of change, from when red began and when it last spoke: the first
    red names why, a reminder follows every REMIND while red, the first green says how long it was
    red and falls silent. It returns the new (since, sent) and the message to send, if any."""
    if green:
        told = (
            None
            if since is None
            else f"back to green, red for {(now - since) // timedelta(minutes=1)} minutes"
        )
        return None, None, told
    if since is None or sent is None:
        return now, now, f"data quality RED: {why}"
    if now - sent >= REMIND:
        return since, now, f"data quality still RED: {why}"
    return since, sent, None


if __name__ == "__main__":
    home, now = Path(os.environ["KESTREL2_DATA"]), datetime.now(UTC)
    if sys.argv[1:] == ["hover"]:
        said, ok = hover(home / keeper.HOT, LINES, now)
        sys.stdout.write(f"{said}\n")
        sys.exit(0 if ok else 1)
    said = monitor(home / keeper.HOT, LINES, backfill._broker(home, now), backfill._archive, now)
    sys.stdout.write(f"{said}\n")
    sys.exit(0 if " green," in said else 1)
