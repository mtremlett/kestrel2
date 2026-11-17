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
from lab.fast_bands import Params
from lab.fast_parts import DATED, Fire, _top
from lab.fast_parts import FIRES as _PARTS
from lab.grid import (
    DESK,
    EXACT,
    Bools,
    Floats,
    Prices,
    TooClose,
    _late,
    _sure,
    _windows,
    prices,
)
from lab.spec import Spec

__all__ = ["DATED", "FIRES", "Params", "Shared", "held"]  #: the blocks live in lab.fast_parts


def _trend_template(p: Prices, params: Params) -> Bools:  # noqa: ARG001 - no settings
    """Minervini's Trend Template on whole numbers, from the 252nd bar: every comparison of
    averages is made on their sums (150 * sum50 against 50 * sum150, and so on), each a
    margin whose sign is checked sure."""
    first, total = 251, len(p.close)
    out = np.zeros(total, dtype=np.bool_)
    if total <= first:
        return out
    sums = {n: _windows(p.close, n).sum(axis=1) for n in (50, 150, 200)}
    s50, s150, s200 = (sums[n][first - n + 1 :] for n in (50, 150, 200))
    s200_ago = sums[200][first - 220 : total - 220]  #: the 200-day sums 21 bars before
    close = p.close[first:]
    bound = 30000.0 * _top(p)

    def sure(margin: Floats, one: Floats, other: Floats) -> Floats:
        return _sure(p, margin, np.abs(one) + np.abs(other), bound)

    held = (
        (sure(150 * close - s150, 150 * close, s150) > 0)
        & (sure(200 * s150 - 150 * s200, 200 * s150, 150 * s200) > 0)
        & (sure(3 * s50 - s150, 3 * s50, s150) > 0)
        & (sure(50 * close - s50, 50 * close, s50) > 0)
        & (sure(s200 - s200_ago, s200, s200_ago) > 0)
    )
    low, high = _windows(p.low, 252).min(axis=1), _windows(p.high, 252).max(axis=1)
    held &= sure(10 * close - 13 * low, 10 * close, 13 * low) >= 0
    held &= sure(4 * close - 3 * high, 4 * close, 3 * high) >= 0
    out[first:] = held
    return out


def _sequential(p: Prices) -> tuple[Bools, Bools]:
    """TD Sequential on whole numbers, as `lab.block_demark` keeps it: the bars that are a
    countdown's thirteenth, and those that end nine closes in a row over the close four back."""
    close, low = p.close.tolist(), p.low.tolist()
    bought, sells = np.zeros(len(close), dtype=np.bool_), np.zeros(len(close), dtype=np.bool_)
    down = up = 0
    count: int | None = None
    for n in range(len(close)):
        if n >= 4:
            down = down + 1 if close[n] < close[n - 4] else 0
            up = up + 1 if close[n] > close[n - 4] else 0
        sells[n] = up == 9
        if sells[n]:
            count = None
        elif down == 9:
            count = 0
        elif count is not None and n >= 2 and close[n] <= low[n - 2]:
            count += 1
        bought[n] = count == 13
        count = None if bought[n] else count
    return bought, sells


#: Every block of the fast engine that reads prices alone, by name.
FIRES: Mapping[str, Fire] = {
    **_PARTS,
    "trend_template": _trend_template,
    "demark_countdown": lambda p, params: _sequential(p)[0],  # noqa: ARG005 - no settings
    "demark_sell_setup": lambda p, params: _sequential(p)[1],  # noqa: ARG005 - no settings
}


def _highest_high_on_volume(p: Prices, volumes: Floats, params: Params) -> Bools:
    """A new high, the volume at least `pct` per cent of the average of the n before: worked on
    whole numbers (volume * n * 100 against pct * their sum), so it is exact."""
    n, pct = int(params["n"]), int(params["pct"])
    if 500 * n * float(volumes.max(initial=0)) >= EXACT:
        raise TooClose("volumes too long for the sums to be exact")
    total = _windows(volumes, n).sum(axis=1)[:-1]  #: the n volumes before each bar from n
    heavy = 100 * n * volumes[n:] >= pct * total
    return FIRES["highest_high"](p, params) & _late(n, heavy, len(p.close))


#: The blocks that need the bars' volumes as well as their prices, by name.
VOLUMED: Mapping[str, Callable[[Prices, Floats, Params], Bools]] = {
    "highest_high_on_volume": _highest_high_on_volume,
}


class Shared:
    """One line's prices and the firing of every block on them, each worked out once."""

    def __init__(self, bars: Sequence[Bar]) -> None:
        self.prices = prices(bars)
        self._months = np.array([b.day.year * 12 + b.day.month for b in bars])
        self._volumes = np.array([b.volume for b in bars], dtype=np.float64)
        self._fired: dict[tuple[str, tuple[tuple[str, int | Decimal], ...]], Bools] = {}

    def fires(self, block: str, params: Params) -> Bools:
        """Whether the block, with these settings, fires on each bar."""
        key = (block, tuple(sorted(params.items())))
        if key not in self._fired:
            if block in DATED:
                self._fired[key] = DATED[block](self.prices, self._months, params)
            elif block in VOLUMED:
                self._fired[key] = VOLUMED[block](self.prices, self._volumes, params)
            else:
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
