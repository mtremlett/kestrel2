"""rollup - THE ONE BUILDER OF THE COARSER TIMEFRAMES from the finest bars a store holds (his
ruling of 16 November 2026). Intraday: 1m bars become 2m, 5m, 10m, 15m, 30m, 1h and 4h bars,
each aligned to its venue's session open (desk/venues.py), none across a session break, none
written part-built. Open is the first bar's, high the greatest, low the least, close the last,
volume the sum; each bar is marked rollup:<from>. Pure: data in, data out."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
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
    for candle in sorted(candles, key=lambda c: c.start):
        if candle.start.tzinfo is None:
            raise ValueError(f"{candle.start} has no time zone: the calendar cannot place it")
        day = candle.start.astimezone(UTC).date()
        if venues.sessions(venue, day, day) != (day,):
            continue
        hours = venues.hours(venue, day)
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
