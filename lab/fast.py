"""fast - THE FAST ENGINE FOR SPEC ROWS: a row's position after every bar of a line, its blocks
worked out on whole arrays and shared between rows, held to the desk's own engine trade for
trade (canon B2: a second implementation must match the engine, or be removed).

`lab.spec.SpecRule` is the engine's reading of a row, bar by bar in exact decimals. This reads
the same row in floating point, which is fast and not exact, so as `lab.grid` does it never
guesses: prices are whole numbers of the line's last decimal place, and a comparison closer
than floating point can call raises `TooClose`, the desk's own engine then deciding.

A line's `Shared` holds its prices and every block's firing once per block and setting, so a
thousand rows on one ticker work each indicator out once. Only the position, which depends on
what it held, is walked bar by bar, over booleans.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from decimal import Decimal

import numpy as np

from desk.store import Bar
from lab.grid import DESK, Bools, Floats, Prices, TooClose, _late, _sure, _windows, prices
from lab.spec import Spec

Params = Mapping[str, int | Decimal]
Fire = Callable[[Prices, Params], Bools]


def _top(p: Prices) -> float:
    """The largest price of the line, as a number of its last decimal place."""
    return float(p.largest[-1]) if p.largest.size else 0.0


def _highest_high(p: Prices, params: Params) -> Bools:
    n = int(params["n"])
    ceiling = _windows(p.high, n).max(axis=1)[:-1]  #: the n highs before each bar from n
    return _late(n, p.close[n:] > ceiling, len(p.close))


def _lowest_low(p: Prices, params: Params) -> Bools:
    n = int(params["n"])
    floor = _windows(p.low, n).min(axis=1)[:-1]  #: the n lows before each bar from n
    return _late(n, p.close[n:] < floor, len(p.close))


def _against_average(p: Prices, n: int) -> Floats:
    """n times each close from bar n - 1 on, less the sum of the n closes ending there: its
    sign is the close's side of its average, this bar's close included."""
    total, close = _windows(p.close, n).sum(axis=1), p.close[n - 1 :]
    return _sure(p, n * close - total, n * close + total, 2.0 * n * _top(p))


def _above_average(p: Prices, params: Params) -> Bools:
    n = int(params["n"])
    return _late(n - 1, _against_average(p, n) > 0, len(p.close))


def _below_average(p: Prices, params: Params) -> Bools:
    n = int(params["n"])
    return _late(n - 1, _against_average(p, n) < 0, len(p.close))


def _lower_run(p: Prices, params: Params) -> Bools:
    n = int(params["n"])
    lower = np.zeros(len(p.close))  #: 1.0 on a bar with a lower high and a lower low
    lower[1:] = (p.high[1:] < p.high[:-1]) & (p.low[1:] < p.low[:-1])
    return _late(n - 1, _windows(lower, n).min(axis=1) > 0, len(p.close))


def _range_edge(p: Prices, params: Params, from_top: bool) -> Bools:
    """Close within `pct` per cent of the range of the last `n` bars, from its top or bottom:
    `pct * range - 100 * gap` is not negative, and the range is not nothing."""
    n, pct = int(params["n"]), int(params["pct"])
    top, bottom = _windows(p.high, n).max(axis=1), _windows(p.low, n).min(axis=1)
    close = p.close[n - 1 :]
    gap = top - close if from_top else close - bottom
    margin = _sure(
        p, pct * (top - bottom) - 100 * gap, pct * (top - bottom) + 100 * gap, 200 * _top(p)
    )
    return _late(n - 1, (margin >= 0) & (top > bottom), len(p.close))


def _near_range_high(p: Prices, params: Params) -> Bools:
    return _range_edge(p, params, from_top=True)


def _near_range_low(p: Prices, params: Params) -> Bools:
    return _range_edge(p, params, from_top=False)


def _channel(p: Prices, params: Params) -> tuple[int, Floats, Floats]:
    """The n of the params, and the highest high and lowest low of the n bars before each bar."""
    n = int(params["n"])
    return n, _windows(p.high, n).max(axis=1)[:-1], _windows(p.low, n).min(axis=1)[:-1]


def _at_range_low(p: Prices, params: Params) -> Bools:
    """Close at or under the channel's low, the channel a range: 20 * (high - low) is at most
    high + low (a tenth of the midpoint), i.e. 21 * low - 19 * high is not negative."""
    n, high, low = _channel(p, params)
    ranged = _sure(p, 21 * low - 19 * high, 21 * low + 19 * high, 40 * _top(p)) >= 0
    return _late(n, ranged & (p.close[n:] <= low), len(p.close))


def _at_midpoint(p: Prices, params: Params) -> Bools:
    n, high, low = _channel(p, params)
    over = _sure(p, 2 * p.close[n:] - high - low, high + low + 2 * p.close[n:], 4 * _top(p)) >= 0
    return _late(n, over, len(p.close))


def _under_close_ago(p: Prices, params: Params) -> Bools:
    return _late(n := int(params["n"]), p.close[n:] < p.close[:-n], len(p.close))


def _always(p: Prices, params: Params) -> Bools:  # noqa: ARG001 - the one interface of every block
    return np.ones(len(p.close), dtype=np.bool_)


def _never(p: Prices, params: Params) -> Bools:  # noqa: ARG001 - the one interface of every block
    return np.zeros(len(p.close), dtype=np.bool_)


#: The firing of each block of `lab.blocks.BLOCKS` that needs no position, by its name. The
#: trailing and time stops depend on the position, so the walk below works them out.
FIRES: Mapping[str, Fire] = {
    "highest_high": _highest_high,
    "lowest_low": _lowest_low,
    "close_below_average": _below_average,
    "close_over_average": _above_average,
    "lower_run": _lower_run,
    "close_at_range_low": _at_range_low,
    "close_at_midpoint": _at_midpoint,
    "close_under_close_ago": _under_close_ago,
    "close_near_range_low": _near_range_low,
    "close_near_range_high": _near_range_high,
    "close_above_average": _above_average,
    "no_exit": _never,
    "no_stop": _never,
    "no_filter": _always,
}


class Shared:
    """One line's prices and the firing of every block on them, each worked out once."""

    def __init__(self, bars: Sequence[Bar]) -> None:
        self.prices = prices(bars)
        self._fired: dict[tuple[str, tuple[tuple[str, int | Decimal], ...]], Bools] = {}

    def fires(self, block: str, params: Params) -> Bools:
        """Whether the block, with these settings, fires on each bar."""
        key = (block, tuple(sorted(params.items())))
        if key not in self._fired:
            self._fired[key] = FIRES[block](self.prices, params)
        return self._fired[key]


def _walk(p: Prices, wish: Bools, leave: Bools, pct: Decimal | None, days: int = 0) -> Bools:
    """The position after each bar: out to start; out, it buys on a bar that wishes it; in, it
    sells on a bar that leaves or, given `pct`, on a close at or under the highest close since
    it was first seen held, less that per cent. That test, `close <= peak * (1 - pct / 100)`,
    is made on whole numbers as `close * a <= peak * b`, and its closeness checked. Given
    `days`, it also sells on the `days`-th held bar."""
    top, bottom = (pct or Decimal(0)).as_integer_ratio()
    a = 100 * bottom
    b, close = a - top, p.close.tolist()
    if _top(p) * a >= DESK:
        raise TooClose("prices too long for the desk's own stop to be exact")
    out, holding, peak, kept = [], False, None, 0
    sides: list[tuple[float, float]] = []
    for n, (buy, sell) in enumerate(zip(wish.tolist(), leave.tolist(), strict=True)):
        if not holding:
            peak, holding, kept = None, buy, 0
        else:
            kept += 1
            peak = close[n] if peak is None else max(peak, close[n])
            holding = not sell and kept != days
            if pct is not None:
                sides.append((close[n] * a, peak * b))
                holding = holding and close[n] * a > peak * b
        out.append(holding)
    if sides:
        left, right = np.array(sides).T
        _sure(p, left - right, left + right, _top(p) * a)
    return np.array(out, dtype=np.bool_)


def held(spec: Spec, shared: Shared) -> Bools:
    """Whether the spec's rule is in the market after each bar of the line, as `SpecRule`
    holds it, or `TooClose` when floating point cannot be sure."""
    fire = {
        place: shared.fires(getattr(spec, place), spec.params[place])
        for place in ("entry", "exit", "filter")
    }
    stop = Decimal(spec.params["stop"]["pct"]) if spec.stop == "trailing_stop" else None
    days = int(spec.params["stop"]["n"]) if spec.stop == "time_stop" else 0
    return _walk(shared.prices, fire["entry"] & fire["filter"], fire["exit"], stop, days)
