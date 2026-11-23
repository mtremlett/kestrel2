"""fast_bands - the fast engine's firing of the spec book's Bollinger-band blocks, on whole
arrays and sure of every comparison (a close call raises `TooClose`), kept apart from
`lab.fast` (which has no room)."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal, localcontext

import numpy as np

from desk.strategy import ARITHMETIC, _Window
from lab.grid import MARGIN, Bools, Floats, Prices, TooClose, _late, _sure, _windows

Params = Mapping[str, int | Decimal]


def _past_band(p: Prices, params: Params, under: bool) -> Bools:
    """%b of the last `n` closes under `pct` (the close under the average by more than
    (50 - pct) / 25 deviations) or over it (above by more than (pct - 50) / 25), from bar
    n - 1: with `u` = the sum of the n closes less n times this one, the close's side is the
    sign of `u`, and 625 * n * u^2 over (50 - pct)^2 times the squares about the sum is the
    deviations. A flat window has no bands and fires nothing."""
    n, pct = int(params["n"]), int(params["pct"])
    window = _windows(p.close, n)
    total, close = window.sum(axis=1), window[:, -1]
    u = total - n * close
    side = _sure(p, u if under else -u, total + n * close) > 0
    left = 625 * n * u * u
    right = (50 - pct) ** 2 * ((n * window - total[:, None]) ** 2).sum(axis=1)
    return side & (_sure(p, left - right, left + right, left + right) > 0)


def percent_b_over(p: Prices, params: Params) -> Bools:
    """Whether %b of the last `n` closes is over `pct`, bar by bar."""
    return _late(int(params["n"]) - 1, _past_band(p, params, under=False), len(p.close))


def percent_b_under_run(p: Prices, params: Params) -> Bools:
    """Whether %b has been under `pct` on `run` bars in a row, this one the last."""
    n, run = int(params["n"]), int(params["run"])
    days = _windows(_past_band(p, params, under=True).astype(float), run).min(axis=1) > 0
    return _late(n + run - 2, days, len(p.close))


def _desk_width(closes: Floats) -> Decimal:
    """The band width of these closes (whole numbers of a place, so the desk's own working of
    them in 28 digits is the same up to a power of ten) as the desk's window works it out."""
    with localcontext(ARITHMETIC):
        window = _Window(len(closes))
        for close in closes:
            window.add(Decimal(int(close)))
        return 4 * window.deviation() / window.mean()


def _squeezed(p: Prices, n: int, look: int) -> Bools:
    """Whether the band width (4 deviations over the average, which is `4 * sqrt(S) / (sqrt(n) *
    total)` with `S` the squares about the sum) is the lowest of the last `look` widths, ties
    included, from bar n + look - 2. Where another width lies within a margin of this one,
    floating point cannot call it, and the desk's own window works those `look` widths out
    (whole prices only); a flat window is exactly nothing, and a tie of nothings is sure."""
    window = _windows(p.close, n)
    total = window.sum(axis=1)
    squares = ((n * window - total[:, None]) ** 2).sum(axis=1)
    width = 4 * np.sqrt(squares) / (np.sqrt(n) * total)
    last, widths = width[look - 1 :], _windows(width, look)
    squeezed = last <= widths.min(axis=1)
    near = (np.abs(widths - last[:, None]) <= MARGIN * last[:, None]).sum(axis=1) > 1
    for row in np.nonzero(near & ~((last == 0) & p.whole))[0]:
        if not p.whole:
            raise TooClose("two band widths too close for floating point to call")
        wins = [_desk_width(p.close[row + m : row + m + n]) for m in range(look)]
        squeezed[row] = wins[-1] <= min(wins)
    return _late(n + look - 2, squeezed, len(p.close))


def close_over_band_after_squeeze(p: Prices, params: Params) -> Bools:
    """Whether the close is over the upper band (2 deviations over the `n`-bar average) the
    bar after the bands were at their narrowest of the last `look` bars."""
    n, look = int(params["n"]), int(params["look"])
    over = _late(n - 1, _past_band(p, {"n": n, "pct": 100}, under=False), len(p.close))
    fires = np.zeros(len(p.close), dtype=np.bool_)
    fires[1:] = over[1:] & _squeezed(p, n, look)[:-1]
    return fires
