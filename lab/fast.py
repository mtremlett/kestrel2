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
from lab.fast_sequential import buy_countdown, sell_setup
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
from lab.spec import Spec, SpecRule

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


def _turtle_soup(p: Prices, params: Params) -> Bools:
    """A low under the n lows before, the lowest of them at least `gap` bars old, the close
    back above it: whole prices compare exactly."""
    n, gap = int(params["n"]), int(params["gap"])
    before = _windows(p.low, n)[:-1]  #: the n lows before each bar from n
    older = before.min(axis=1)
    newest = n - 1 - np.argmin(before[:, ::-1], axis=1)  #: where its latest day sits
    fired = (p.low[n:] < older) & (older < p.close[n:]) & (n - newest >= gap)
    return _late(n, fired, len(p.close))


#: Every block of the fast engine that reads prices alone, by name.
FIRES: Mapping[str, Fire] = {
    **_PARTS,
    "ratio_over_average": _PARTS["close_over_average"],  #: on ratio bars
    "trend_template": _trend_template,
    "turtle_soup": _turtle_soup,
    "td_buy_countdown": buy_countdown,
    "td_sell_setup": sell_setup,
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
        self.bars = bars
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


def _walk(
    p: Prices, wish: Bools, leave: Bools, pct: Decimal | None, days: int = 0, floor: bool = False
) -> Bools:
    """The position after each bar: out to start; out, it buys on a bar that wishes it; in, it
    sells on a bar that leaves or, given `pct`, on a close at or under the highest close since
    it was first seen held, less that per cent. That test, `close <= peak * (1 - pct / 100)`,
    is made on whole numbers as `close * a <= peak * b`, and its closeness checked. Given
    `days`, it also sells on the `days`-th held bar. Given `floor`, it sells on a close under the
    low of the bar it bought on."""
    top, bottom = (pct or Decimal(0)).as_integer_ratio()
    a = 100 * bottom
    b, close, low = a - top, p.close.tolist(), p.low.tolist()
    if _top(p) * a >= DESK:
        raise TooClose("prices too long for the desk's own stop to be exact")
    out, holding, peak, kept, level = [], False, None, 0, 0.0
    sides: list[tuple[float, float]] = []
    for n, (buy, sell) in enumerate(zip(wish.tolist(), leave.tolist(), strict=True)):
        if not holding:
            peak, holding, kept, level = None, buy, 0, low[n]
        else:
            kept += 1
            peak = close[n] if peak is None else max(peak, close[n])
            holding = not sell and kept != days and not (floor and close[n] < level)
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
    if {"darvas_box", "darvas_stop"} & {spec.entry, spec.stop}:
        rule, holding, out = SpecRule(spec), False, []  # the boxes depend on the position held
        for bar in shared.bars:
            holding = rule.step(bar, holding)
            out.append(holding)
        return np.array(out, dtype=np.bool_)
    walked = spec.stop in {"trailing_stop", "time_stop", "under_entry_low"}  #: held in the walk
    places = ("entry", "exit", "filter") if walked else ("entry", "exit", "filter", "stop")
    fire = {place: shared.fires(getattr(spec, place), spec.params[place]) for place in places}
    stop = Decimal(spec.params["stop"]["pct"]) if spec.stop == "trailing_stop" else None
    days = int(spec.params["stop"]["n"]) if spec.stop == "time_stop" else 0
    floor = spec.stop == "under_entry_low"
    leave = fire["exit"] if walked else fire["exit"] | fire["stop"]  # the desk sells on either
    return _walk(shared.prices, fire["entry"] & fire["filter"], leave, stop, days, floor)
