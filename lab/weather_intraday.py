"""weather_intraday - THE MARKET WEATHER on intraday bars (REG-01), layers: each bar's
trend, opening-range and range-expansion states, named from the session's bars known at that bar's
close and never from a later one.

A bar is `up` when its close is above the mean of the session's last WINDOW closes, itself
included, `down` when it is at or below it, and `warming` until WINDOW closes of THE SESSION
have been seen: a label is never guessed from less, and yesterday's closes are never borrowed.
A session is one UTC calendar day of bars. Labels are keyed by the bar's start, one plain word
each, as `lab/regime.py` asks. The daily twin is `lab/weather.py`.

Opening range: the session's first OPENING bars of time (30 minutes from its first bar) are
`forming`; after that a bar is `above` the range when its close is over the range's high,
`below` when under its low, else `inside`. Range expansion: a bar is `wide` when its high-low
exceeds EXPANSION times the mean high-low of the session's EARLIER bars, `narrow` otherwise,
`warming` until MIN_BARS earlier bars of the session exist. Volatility: the deviation of the
session's returns to date against the earlier sessions' at the same time of day, in thirds.
No layer feeds any verdict.
"""

from __future__ import annotations

import statistics
from collections.abc import Sequence
from datetime import datetime, time, timedelta
from decimal import Decimal

from desk.rollup import Candle
from lab.weather import DOWN, UP, WARMING

#: The trend's look-back in bars of the session.
WINDOW = 20
#: The opening range's length, from the session's first bar.
OPENING = timedelta(minutes=30)
#: Earlier bars of the session needed before a bar's expansion is named.
MIN_BARS = 5
#: A bar is wide when its range exceeds this multiple of the session's mean bar range so far.
EXPANSION = 2
FORMING, INSIDE, ABOVE, BELOW = "forming", "inside", "above", "below"
WIDE, NARROW = "wide", "narrow"


def trend(bars: Sequence[Candle]) -> dict[datetime, str]:
    """Each bar's start under its trend state, oldest bar first, by that bar's close and the
    WINDOW closes of its session up to it."""
    _check_order(bars)
    named: dict[datetime, str] = {}
    closes: list[Decimal] = []
    session = None
    for bar in bars:
        if bar.start.date() != session:
            session, closes = bar.start.date(), []
        closes.append(bar.close)
        recent = closes[-WINDOW:]
        if len(recent) < WINDOW:
            named[bar.start] = WARMING
        else:
            named[bar.start] = UP if bar.close * WINDOW > sum(recent) else DOWN
    return named


def _check_order(bars: Sequence[Candle]) -> None:
    """Refuse bars that are not one per start, oldest first."""
    starts = [bar.start for bar in bars]
    if len(set(starts)) != len(starts) or starts != sorted(starts):
        raise ValueError("bars must be one per start, oldest first, to be named in order")


def opening_range(bars: Sequence[Candle]) -> dict[datetime, str]:
    """Each bar's start under its state against its session's opening range."""
    _check_order(bars)
    named: dict[datetime, str] = {}
    session = None
    open_end, high, low = datetime.min, Decimal(0), Decimal(0)
    for bar in bars:
        if bar.start.date() != session:
            session, open_end, high, low = bar.start.date(), bar.start + OPENING, bar.high, bar.low
        if bar.start < open_end:
            high, low = max(high, bar.high), min(low, bar.low)
            named[bar.start] = FORMING
        else:
            named[bar.start] = ABOVE if bar.close > high else BELOW if bar.close < low else INSIDE
    return named


def expansion(bars: Sequence[Candle]) -> dict[datetime, str]:
    """Each bar's start under `wide`, `narrow` or `warming`, by its range against the mean
    range of the session's earlier bars."""
    _check_order(bars)
    named: dict[datetime, str] = {}
    ranges: list[Decimal] = []
    session = None
    for bar in bars:
        if bar.start.date() != session:
            session, ranges = bar.start.date(), []
        size = bar.high - bar.low
        if len(ranges) < MIN_BARS:
            named[bar.start] = WARMING
        else:
            named[bar.start] = WIDE if size * len(ranges) > EXPANSION * sum(ranges) else NARROW
        ranges.append(size)
    return named


#: Earlier sessions holding a value at the same time of day before a volatility is named.
MIN_SESSIONS = 5
#: Returns of the session needed before its own volatility exists.
MIN_RETURNS = 2
QUIET, NORMAL, WILD = "quiet", "normal", "wild"


def volatility(bars: Sequence[Candle]) -> dict[datetime, str]:
    """Each bar's start under `quiet`, `normal` or `wild`: the deviation of its session's
    bar-to-bar returns up to it, ranked in thirds against the same measure at the same time
    of day in the earlier sessions; `warming` until MIN_SESSIONS of them are held."""
    _check_order(bars)
    named: dict[datetime, str] = {}
    held: dict[time, list[Decimal]] = {}
    session, closes = None, []
    today: list[tuple[time, Decimal]] = []
    for bar in bars:
        if bar.start.date() != session:
            for at, vol in today:
                held.setdefault(at, []).append(vol)
            session, closes, today = bar.start.date(), [], []
        closes.append(bar.close)
        returns = [closes[n] / closes[n - 1] - 1 for n in range(1, len(closes))]
        earlier = held.get(bar.start.time(), [])
        if len(returns) < MIN_RETURNS or len(earlier) < MIN_SESSIONS:
            named[bar.start] = WARMING
            if len(returns) >= MIN_RETURNS:
                today.append((bar.start.time(), Decimal(statistics.pstdev(returns))))
            continue
        vol = Decimal(statistics.pstdev(returns))
        today.append((bar.start.time(), vol))
        below = sum(1 for v in earlier if v < vol) * 3
        named[bar.start] = (
            QUIET if below < len(earlier) else NORMAL if below < 2 * len(earlier) else WILD
        )
    return named
