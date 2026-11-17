"""fast_bands - the fast engine's firing of the spec book's Bollinger-band blocks, on whole
arrays and sure of every comparison (a close call raises `TooClose`), kept apart from
`lab.fast` (which has no room)."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from lab.grid import Bools, Prices, _late, _sure, _windows

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
