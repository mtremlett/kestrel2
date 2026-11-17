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
from lab.fast_bands import (
    Params,
    close_over_band_after_squeeze,
    percent_b_over,
    percent_b_under_run,
)
from lab.grid import (
    DESK,
    MARGIN,
    Bools,
    Floats,
    Prices,
    TooClose,
    _late,
    _sure,
    _wilder,
    _windows,
    prices,
)
from lab.spec import Spec

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


def _at_or_below_average(p: Prices, params: Params) -> Bools:
    n = int(params["n"])
    return _late(n - 1, _against_average(p, n) <= 0, len(p.close))


def _over_rising_average(p: Prices, params: Params) -> Bools:
    """The close over its `n`-bar average, which is over what it was `ago` bars before: the
    sums of `n` closes compare as the averages do."""
    n, ago = int(params["n"]), int(params["ago"])
    total = _windows(p.close, n).sum(axis=1)
    now, before = total[ago:], total[: len(total) - ago]
    rising = _sure(p, now - before, now + before, 2.0 * n * _top(p)) > 0
    return _late(n - 1 + ago, rising & (_against_average(p, n)[ago:] > 0), len(p.close))


def _big_moves(p: Prices, params: Params) -> Bools:
    """Whether a move of more than `pct` per cent lies among the last `n` changes of the close:
    `20 * |close - before| - 3 * before` is over nothing for 15 per cent, in whole numbers."""
    n, pct = int(params["n"]), int(params["pct"])
    change, before = np.abs(np.diff(p.close)), p.close[:-1]
    margin = _sure(p, 100 * change - pct * before, 100 * change + pct * before, 100 * _top(p))
    seen = np.concatenate(([0], np.cumsum(margin > 0)))  #: big moves among the first k changes
    first = np.maximum(np.arange(1, len(p.close)) - n, 0)  #: the oldest change of each bar's n
    big = np.zeros(len(p.close), dtype=np.bool_)
    big[1:] = seen[1:] - seen[first] > 0
    return big


def _rising_score(p: Prices, params: Params) -> Bools:
    """The last `n` closes score over nothing (the sign of the regression's covariance, which
    is the sign of its slope) with no big move among the last `n` changes. A window whose
    closes are all one price scores nothing; one whose covariance is lost in rounding is
    refused."""
    n = int(params["n"])
    logs = _windows(np.log(p.close), n)
    centred = logs - logs.mean(axis=1, keepdims=True)
    spread = np.sqrt((centred**2).sum(axis=1))
    rank = np.arange(n) - (n - 1) / 2
    cov = centred @ rank
    flat = _windows(p.close, n).max(axis=1) == _windows(p.close, n).min(axis=1)
    reach = np.sqrt((rank**2).sum()) * spread
    if (~flat & ((spread < 1e-9) | (np.abs(cov) < MARGIN * reach))).any():
        raise TooClose("a regression too flat for floating point to call")
    rising = np.zeros(len(p.close), dtype=np.bool_)
    rising[n - 1 :] = ~flat & (cov > 0)
    return rising & ~_big_moves(p, params)


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


def _keltner(p: Prices, params: Params, upper: bool) -> Bools:
    """Close over the upper band or under the lower, the band the average typical price (high,
    low and close over three) plus or minus the average range of the last `n` bars: with sums,
    `3n * close - typical - 3 * range` (upper) or `typical - 3n * close - 3 * range` is over 0."""
    n = int(params["n"])
    typical = _windows(p.high + p.low + p.close, n).sum(axis=1)
    spread, close = _windows(p.high - p.low, n).sum(axis=1), p.close[n - 1 :]
    side = 3 * n * close - typical if upper else typical - 3 * n * close
    margin = _sure(p, side - 3 * spread, 3 * n * close + typical + 3 * spread, 9.0 * n * _top(p))
    return _late(n - 1, margin > 0, len(p.close))


def _over_keltner_band(p: Prices, params: Params) -> Bools:
    return _keltner(p, params, upper=True)


def _under_keltner_band(p: Prices, params: Params) -> Bools:
    return _keltner(p, params, upper=False)


def _rsi_under(p: Prices, params: Params) -> Bools:
    """Wilder's `n`-bar RSI of the close under `pct`: a gain over a loss of less than `pct` over
    `100 - pct`, so `pct * loss - (100 - pct) * gain` is over 0; with no loss the RSI is 100. A
    change is a close less a close, so it is only as sure as the closes so far are."""
    n, pct = int(params["n"]), int(params["pct"])
    change = np.diff(p.close)
    gain, loss = _wilder(np.maximum(change, 0), n), _wilder(np.maximum(-change, 0), n)
    low = loss > 0
    low[low] = _sure(p, (pct * loss - (100 - pct) * gain)[low], p.largest[n:][low], np.inf) > 0
    return _late(n, low, len(p.close))


def _under_close_ago(p: Prices, params: Params) -> Bools:
    return _late(n := int(params["n"]), p.close[n:] < p.close[:-n], len(p.close))


def _month_ends(p: Prices, months: Floats, params: Params, over: bool) -> Bools:
    """On each month's first bar, whether the month before closed over the average of its last
    `n` month-end closes (or, not `over`, did not): `n * close - sum` is over 0, from the `n`-th
    month end on; a month end before that is not over."""
    n = int(params["n"])
    first = np.flatnonzero(months[1:] != months[:-1]) + 1
    ends = p.close[first - 1]
    sums, last = _windows(ends, n).sum(axis=1), ends[n - 1 :]
    above = np.zeros(len(first), dtype=np.bool_)
    above[n - 1 :] = _sure(p, n * last - sums, n * last + sums, 2.0 * n * _top(p)) > 0
    out = np.zeros(len(p.close), dtype=np.bool_)
    out[first] = above if over else ~above
    return out


def _over_month_end_average(p: Prices, months: Floats, params: Params) -> Bools:
    return _month_ends(p, months, params, over=True)


def _under_month_end_average(p: Prices, months: Floats, params: Params) -> Bools:
    return _month_ends(p, months, params, over=False)


def _ema(values: Floats, n: int) -> Floats:
    """The exponential average, from the bar that completes its first `n` values on: seeded
    with their plain average, then each value weighted two parts in `n + 1`."""
    if len(values) < n:
        return np.empty(0)
    out = [float(values[:n].sum()) / n]
    for value in values[n:].tolist():
        out.append(out[-1] + (value - out[-1]) * 2 / (n + 1))
    return np.array(out)


def _over_emas(p: Prices, params: Params) -> Bools:
    """A close over both exponential averages, from the bar that seeds the slower. The averages
    are worked in floating point, so a close near either is only as sure as it is clear."""
    n, slow = int(params["n"]), int(params["slow"])
    first, close = max(n, slow), p.close[max(n, slow) - 1 :]
    both = np.ones(len(close), dtype=np.bool_)
    for size in (n, slow):
        mean = _ema(p.close, size)[first - size :]
        both &= _sure(p, close - mean, close + mean, np.inf) > 0
    return _late(first - 1, both, len(p.close))


def _under_ema(p: Prices, params: Params) -> Bools:
    n = int(params["n"])
    close, mean = p.close[n - 1 :], _ema(p.close, n)
    return _late(n - 1, _sure(p, mean - close, close + mean, np.inf) > 0, len(p.close))


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
    "close_over_rising_average": _over_rising_average,
    "lower_run": _lower_run,
    "close_at_range_low": _at_range_low,
    "close_at_midpoint": _at_midpoint,
    "close_over_keltner_band": _over_keltner_band,
    "close_under_keltner_band": _under_keltner_band,
    "rsi_under": _rsi_under,
    "close_over_band_after_squeeze": close_over_band_after_squeeze,
    "percent_b_over": percent_b_over,
    "percent_b_under_run": percent_b_under_run,
    "close_under_close_ago": _under_close_ago,
    "close_near_range_low": _near_range_low,
    "close_near_range_high": _near_range_high,
    "close_above_average": _above_average,
    "close_at_or_under_average": _at_or_below_average,
    "big_move": _big_moves,
    "rising_score": _rising_score,
    "close_over_emas": _over_emas,
    "close_under_ema": _under_ema,
    "no_exit": _never,
    "no_stop": _never,
    "no_filter": _always,
}


#: The blocks that need the bars' months as well as their prices, by name.
DATED: Mapping[str, Callable[[Prices, Floats, Params], Bools]] = {
    "month_end_over_average": _over_month_end_average,
    "month_end_not_over_average": _under_month_end_average,
}


class Shared:
    """One line's prices and the firing of every block on them, each worked out once."""

    def __init__(self, bars: Sequence[Bar]) -> None:
        self.prices = prices(bars)
        self._months = np.array([b.day.year * 12 + b.day.month for b in bars])
        self._fired: dict[tuple[str, tuple[tuple[str, int | Decimal], ...]], Bools] = {}

    def fires(self, block: str, params: Params) -> Bools:
        """Whether the block, with these settings, fires on each bar."""
        key = (block, tuple(sorted(params.items())))
        if key not in self._fired:
            self._fired[key] = (
                DATED[block](self.prices, self._months, params)
                if block in DATED
                else FIRES[block](self.prices, params)
            )
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
