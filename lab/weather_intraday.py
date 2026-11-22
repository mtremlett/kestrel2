"""weather_intraday - THE MARKET WEATHER on intraday bars (REG-01), first layer: each bar's trend
state, named from the session's closes known at that bar's close and never from a later one.

A bar is `up` when its close is above the mean of the session's last WINDOW closes, itself
included, `down` when it is at or below it, and `warming` until WINDOW closes of THE SESSION
have been seen: a label is never guessed from less, and yesterday's closes are never borrowed.
A session is one UTC calendar day of bars. Labels are keyed by the bar's start, one plain word
each, as `lab/regime.py` asks. The daily twin is `lab/weather.py`.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal

from desk.rollup import Candle
from lab.weather import DOWN, UP, WARMING

#: The trend's look-back in bars of the session.
WINDOW = 20


def trend(bars: Sequence[Candle]) -> dict[datetime, str]:
    """Each bar's start under its trend state, oldest bar first, by that bar's close and the
    WINDOW closes of its session up to it."""
    starts = [bar.start for bar in bars]
    if len(set(starts)) != len(starts) or starts != sorted(starts):
        raise ValueError("bars must be one per start, oldest first, to be named in order")
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
