"""grid - THE FAST GRID ENGINE: each of the five strategies' position after every bar of a
line, worked out on whole arrays at once, for the ladder's many cells.

It is a second implementation of the desk's rules (`desk/strategy.py`), so it is kept only
while a parity test shows it holds what the desk holds after every bar (canon B2). The desk
works in exact decimals; this works in floating point, which is fast and not exact. So it
never guesses. Prices are turned into whole numbers of the line's smallest step; sums of
those are exact while they stay under 2**53, and a tie there is a true tie. Anything else
is trusted only when it is clear by a wide margin, and a comparison closer than that is
refused with `TooClose`: the desk's own engine must decide that cell.

Each rule gives two answers for every bar: would it enter if out, would it stay if in.
None of the five's indicators depends on its position, so both are worked out for every
bar at once and the position follows from them.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
from numpy.typing import NDArray

from desk.store import Bar

Floats = NDArray[np.float64]
Bools = NDArray[np.bool_]

#: Floating point holds every whole number below this exactly.
EXACT = 2.0**53
#: The largest multiple of one price a sum here forms: four times a 200-day sum, twice.
LINEAR = 1600
#: A comparison of rounded numbers is trusted when its sides differ by more than this part
#: of their size. Rounding moves them by about one part in 10**13 at the very most.
MARGIN = 1e-9


class TooClose(Exception):
    """Floating point cannot call it: the desk's own engine must decide."""


@dataclass(frozen=True)
class Prices:
    """A line's bars as arrays, oldest first, in whole numbers of its smallest step."""

    high: Floats
    low: Floats
    close: Floats
    whole: bool  #: every price, and every sum of them a rule forms, is held exactly


def prices(bars: Sequence[Bar]) -> Prices:
    """The bars' highs, lows and closes as arrays, each price told apart from every other."""
    ratios = [
        [value.as_integer_ratio() for value in column]
        for column in ([b.high for b in bars], [b.low for b in bars], [b.close for b in bars])
    ]
    step = math.lcm(*(bottom for column in ratios for _, bottom in column))
    steps = [[top * (step // bottom) for top, bottom in column] for column in ratios]
    table = np.array(steps, dtype=np.float64).reshape(3, len(bars))
    distinct = {number for column in steps for number in column}
    if len(distinct) != len(set(table.ravel().tolist())):
        raise TooClose("two prices too close for floating point to tell apart")
    whole = max(distinct, default=0) * LINEAR < EXACT
    return Prices(table[0], table[1], table[2], whole)


def _sure(p: Prices, margin: Floats, size: Floats, largest: Floats | float = 0.0) -> Floats:
    """The margin, once its sign can be trusted everywhere: it is clear of nothing by a
    wide margin of its size, or it is a whole number worked out exactly (the prices are
    whole and `largest`, the largest number the comparison formed, is under 2**53)."""
    doubt = np.abs(margin) < MARGIN * size
    if p.whole:
        doubt &= np.asarray(largest) >= EXACT
    if doubt.any():
        raise TooClose("a comparison too close for floating point to call")
    return margin


def _windows(values: Floats, size: int) -> Floats:
    """Row n holds the `size` values that end at bar n + size - 1."""
    if len(values) < size:
        return np.empty((0, size))
    return sliding_window_view(values, size)


def _late(first: int, values: Bools, total: int) -> Bools:
    """The values, which start at bar `first`, over all the bars: false before them."""
    out = np.zeros(total, dtype=np.bool_)
    out[first:] = values
    return out


def _wilder(values: Floats, size: int) -> Floats:
    """Wilder's smoothing, from the bar that completes its first `size` values on."""
    if len(values) < size:
        return np.empty(0)
    out = [float(values[:size].sum()) / size]
    for value in values[size:].tolist():
        out.append((out[-1] * (size - 1) + value) / size)
    return np.array(out)


def _rsi2(p: Prices) -> tuple[Bools, Bools]:
    close, total = p.close, len(p.close)
    long, short = _windows(close, 200).sum(axis=1), _windows(close, 5).sum(axis=1)
    above = _sure(p, 200 * close[199:] - long, 200 * close[199:] + long) > 0
    stay = _sure(p, short - 5 * close[4:], short + 5 * close[4:]) >= 0
    change = np.diff(close)
    #: both start at bar 2; from bar 199 on is all a buy can read
    gain = _wilder(np.maximum(change, 0), 2)[197:]
    loss = _wilder(np.maximum(-change, 0), 2)[197:]
    #: an RSI under 5 is a loss over 19 times the gain; with no loss at all it is 100
    low = _sure(p, loss - 19 * gain, loss + 19 * gain, np.inf) > 0
    return _late(199, above & low, total), _late(4, stay, total)


def _bollinger(p: Prices) -> tuple[Bools, Bools]:
    window = _windows(p.close, 20)
    close, total = window[:, -1], window.sum(axis=1)
    under = total - 20 * close  #: 20 times how far the close is under the average
    stay = _sure(p, under, total + 20 * close) >= 0
    #: under the lower band: 20 x under squared exceeds 4 x the squares about the average
    left = 20 * under * np.abs(under)
    right = 4 * ((20 * window - total[:, None]) ** 2).sum(axis=1)
    reach = np.sqrt(np.abs(left)) + np.sqrt(right)
    enter = _sure(p, left - right, total * reach, np.abs(left) + right) > 0
    return _late(19, enter, len(p.close)), _late(19, stay, len(p.close))


def _breakout(p: Prices) -> tuple[Bools, Bools]:
    #: a price against a price is exact: `prices` told every one apart
    top = _windows(p.high, 20).max(axis=1)[:-1]  #: the 20 highs before each bar from 20
    floor = _windows(p.low, 10).min(axis=1)[:-1]  #: the 10 lows before each bar from 10
    total = len(p.close)
    return _late(20, p.close[20:] > top, total), _late(10, p.close[10:] >= floor, total)


def _trend(p: Prices) -> tuple[Bools, Bools]:
    slow = _windows(p.close, 200).sum(axis=1)
    fast = _windows(p.close, 50).sum(axis=1)[150:]
    above = _sure(p, 4 * fast - slow, 4 * fast + slow) > 0
    crossed = above.copy()
    crossed[:1] = False  #: a cross before both averages existed is not one it saw
    crossed[1:] &= ~above[:-1]
    return _late(199, crossed, len(p.close)), _late(199, above, len(p.close))


def _carried(band: Floats, close: Floats) -> Floats:
    """The upper band as it is carried: no higher than the day before's while the close
    before was under that."""
    out, closes = band.tolist(), close.tolist()
    for n in range(1, len(out)):
        if closes[n - 1] < out[n - 1]:
            out[n] = min(out[n], out[n - 1])
    return np.array(out)


def _supertrend(p: Prices) -> tuple[Bools, Bools]:
    high, low, close, total = p.high, p.low, p.close, len(p.close)
    spread = high - low
    gap = np.maximum(np.abs(high[1:] - close[:-1]), np.abs(low[1:] - close[:-1]))
    spread[1:] = np.maximum(spread[1:], gap)
    width, middle = _wilder(spread, 10), (high[9:] + low[9:]) / 2  #: both from bar 9
    upper = _carried(middle + 3 * width, close[9:])
    lower = -_carried(3 * width - middle, -close[9:])
    for band in (upper, lower):  #: whether each was carried, a close against its own day's
        _sure(p, close[9:-1] - band[:-1], close[9:-1] + np.abs(band[:-1]), np.inf)
    after = close[10:]  #: each close against the bands of the day before
    enter = _sure(p, after - upper[:-1], after + np.abs(upper[:-1]), np.inf) > 0
    stay = _sure(p, after - lower[:-1], after + np.abs(lower[:-1]), np.inf) >= 0
    return _late(10, enter, total), _late(10, stay, total)


#: The desk's five, by its names: for every bar, would it enter if out, would it stay if in.
RULES: Mapping[str, Callable[[Prices], tuple[Bools, Bools]]] = {
    "rsi2_pullback": _rsi2,
    "bollinger_pullback": _bollinger,
    "breakout_20_10": _breakout,
    "trend_50_200": _trend,
    "supertrend_10_3": _supertrend,
}


def held(name: str, p: Prices) -> Bools:
    """Whether the strategy is in the market after each bar. It starts out. A bar on which
    it would both enter and stay, or neither, settles it whatever it held; one on which it
    would only stay leaves it as it was; one on which it would only enter turns it over."""
    enter, stay = RULES[name](p)
    turns = np.cumsum(enter & ~stay)
    settled = np.maximum.accumulate(np.where(enter == stay, np.arange(len(enter)), -1))
    was: Bools = enter[settled] & (settled >= 0)  #: what the last settling bar left it
    turned: Bools = (turns - np.where(settled < 0, 0, turns[settled])) % 2 == 1
    return was ^ turned
