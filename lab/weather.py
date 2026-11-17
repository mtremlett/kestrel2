"""weather - THE MARKET WEATHER (REG-01), first layer: each session's trend state, named from
the closes known at that session's close and never from a later one (canon B3).

A day is `up` when its close is above the mean of the last WINDOW closes, itself included,
`down` when it is at or below it, and `warming` until WINDOW closes have been seen: a label
is never guessed from less. The label of day T reads bars up to T only, so cutting the history
after T changes none of the labels up to T (the future-blind test in
`tests/unit/test_lab_weather.py`). The names are one plain word each, as `lab/regime.py` asks.

The trend is the baseline. Realised volatility is built below but wired into no verdict;
drawdown depth and breadth come one at a time, each only on an out-of-sample win against
trend alone, with the trial count recorded (canon B6).
"""

from __future__ import annotations

import statistics
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


#: The volatility layer: the look-back for realised volatility, and the history it is ranked in.
VOL_WINDOW, VOL_RANK = 20, 252
CALM, STORMY = "calm", "stormy"


def volatility(bars: Sequence[Bar]) -> dict[date, str]:
    """Each bar's day as `stormy` when the standard deviation of the last VOL_WINDOW daily
    returns is above the median of the VOL_RANK values before it, else `calm`; `warming`
    until that many earlier values exist. Day T reads closes up to T only (canon B3). Built
    but wired into no verdict until it wins out of sample against trend alone (canon B6)."""
    trend(bars)  # the one check that bars are one per day, oldest first
    closes = [bar.close for bar in bars]
    returns = [closes[n] / closes[n - 1] - 1 for n in range(1, len(closes))]
    vols = [
        Decimal(statistics.pstdev(returns[n - VOL_WINDOW : n]))
        for n in range(VOL_WINDOW, len(returns) + 1)
    ]
    named: dict[date, str] = {}
    for n, bar in enumerate(bars):
        i = n - VOL_WINDOW  # this day's volatility is vols[i], from the returns up to it
        if i < VOL_RANK:
            named[bar.day] = WARMING
        else:
            named[bar.day] = STORMY if vols[i] > statistics.median(vols[i - VOL_RANK : i]) else CALM
    return named
