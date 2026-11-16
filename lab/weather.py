"""weather - THE MARKET WEATHER (REG-01), first layer: each session's trend state, named from
the closes known at that session's close and never from a later one (canon B3).

A day is `up` when its close is above the mean of the last WINDOW closes, itself included,
`down` when it is at or below it, and `warming` until WINDOW closes have been seen: a label
is never guessed from less. The label of day T reads bars up to T only, so cutting the history
after T changes none of the labels up to T (the future-blind test in
`tests/unit/test_lab_weather.py`). The names are one plain word each, as `lab/regime.py` asks.

Only this layer is built. Realised volatility, drawdown depth and breadth are added one at a
time, each only on an out-of-sample win against this trend alone, with the trial count
recorded (canon B6); until then trend alone is the baseline they must beat.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from decimal import Decimal

from desk.store import Bar

#: The trend's look-back in sessions: the long average the desk's published rules also use.
WINDOW = 200
UP, DOWN, WARMING = "up", "down", "warming"


def trend(bars: Sequence[Bar]) -> dict[date, str]:
    """Each bar's day under its trend state, oldest bar first, by that day's close and the
    WINDOW closes up to it."""
    days = [bar.day for bar in bars]
    if len(set(days)) != len(days) or days != sorted(days):
        raise ValueError("bars must be one per day, oldest first, to be named in order")
    closes = [bar.close for bar in bars]
    named: dict[date, str] = {}
    total = Decimal(0)
    for n, close in enumerate(closes):
        total += close
        if n >= WINDOW:
            total -= closes[n - WINDOW]
        if n + 1 < WINDOW:
            named[days[n]] = WARMING
        else:
            named[days[n]] = UP if close * WINDOW > total else DOWN
    return named
