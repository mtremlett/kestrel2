"""rollup - THE ONE BUILDER OF THE COARSER TIMEFRAMES from the finest bars a store holds (his
ruling of 16 November 2026). Intraday: 1m bars become 2m, 5m, 10m, 15m, 30m, 1h and 4h bars,
each aligned to its venue's session open (desk/venues.py), none across a session break, none
written part-built. Open is the first bar's, high the greatest, low the least, close the last,
volume the sum; each bar is marked rollup:<from>. Pure: data in, data out."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal

from desk import venues

#: The coarser intraday timeframes and their length in minutes.
MINUTES = {"2m": 2, "5m": 5, "10m": 10, "15m": 15, "30m": 30, "1h": 60, "4h": 240}


@dataclass(frozen=True)
class Candle:
    """One intraday bar of a line, its source named."""

    start: datetime  #: when the bar begins, timezone-aware UTC
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    source: str  #: ibkr, yf, stooq, or rollup:<from timeframe>


def _built(group: list[Candle], start: datetime, source: str) -> Candle:
    """One coarser bar from the finer bars of its interval, in time order."""
    return Candle(
        start,
        group[0].open,
        max(c.high for c in group),
        min(c.low for c in group),
        group[-1].close,
        sum(c.volume for c in group),
        source,
    )


def rollup(venue: str, candles: list[Candle], timeframe: str, base: str = "1m") -> list[Candle]:
    """The venue's candles of the finer timeframe base, as bars of timeframe: only those
    whose whole interval lies in one session and is held bar by bar; a gap leaves it out."""
    length, step = MINUTES[timeframe], MINUTES.get(base, 1)
    if length % step or length <= step:
        raise ValueError(f"{timeframe} bars cannot be built from {base} bars")
    groups: dict[datetime, list[Candle]] = {}
    held: dict[date, venues.Hours | None] = {}  # the calendar, asked once per day
    for candle in sorted(candles, key=lambda c: c.start):
        if candle.start.tzinfo is None:
            raise ValueError(f"{candle.start} has no time zone: the calendar cannot place it")
        day = candle.start.astimezone(UTC).date()
        if day not in held:
            held[day] = (
                venues.hours(venue, day) if venues.sessions(venue, day, day) == (day,) else None
            )
        hours = held[day]
        if hours is None:
            continue
        into = (candle.start - hours.open) // timedelta(minutes=length)
        start = hours.open + into * timedelta(minutes=length)
        if candle.start >= hours.open and start + timedelta(minutes=length) <= hours.close:
            groups.setdefault(start, []).append(candle)
    full = length // step
    return [
        _built(group, start, f"rollup:{base}")
        for start, group in sorted(groups.items())
        if [c.start for c in group] == [start + timedelta(minutes=step * i) for i in range(full)]
    ]


def weekly(venue: str, candles: list[Candle]) -> list[Candle]:
    """The venue's daily candles (one per session, start on the session's date) as weekly bars,
    each starting on its Monday: only a week whose every session is held is written."""
    weeks: dict[date, dict[date, Candle]] = {}
    for candle in sorted(candles, key=lambda c: c.start):
        if candle.start.tzinfo is None:
            raise ValueError(f"{candle.start} has no time zone: the calendar cannot place it")
        day = candle.start.astimezone(UTC).date()
        monday = day - timedelta(days=day.weekday())
        weeks.setdefault(monday, {})[day] = candle
    return [
        _built(list(held.values()), datetime.combine(monday, time(), UTC), "rollup:1d")
        for monday, held in sorted(weeks.items())
        if tuple(held) == venues.sessions(venue, monday, monday + timedelta(days=6))
    ]


def merged(
    pulled: list[Candle], built: list[Candle]
) -> tuple[list[Candle], list[tuple[Candle, Candle]]]:
    """The bars to keep, in time order, and the faults: a pulled bar wins over a built one of the
    same start, and where the two differ in any price or the volume the pair (pulled, built)
    is a recorded fault; a built bar with no pulled twin is kept."""
    kept = {c.start: c for c in built}
    faults = []
    for bar in pulled:
        twin = kept.get(bar.start)
        if twin is not None and (bar.open, bar.high, bar.low, bar.close, bar.volume) != (
            twin.open,
            twin.high,
            twin.low,
            twin.close,
            twin.volume,
        ):
            faults.append((bar, twin))
        kept[bar.start] = bar
    return [kept[start] for start in sorted(kept)], faults
