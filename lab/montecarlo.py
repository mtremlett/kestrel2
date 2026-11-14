"""montecarlo - THE LADDER'S MONTE CARLO RUNG: how bad could the same trades have run?

A trial's trades, each as its return on the equity it was taken with, are drawn again with
replacement PATHS times, as many to a path as the trial made, and each path is compounded.
What comes back is the spread of the drawdowns and of the returns those paths make. It
measures and never gates: no verdict reads it. The draw is seeded, so a trial run again is
resampled the same; a faster draw (a GPU) may stand behind `resample` only if it gives the
same answer.
"""

from __future__ import annotations

import random
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

PATHS = 1000
QUANTILES = (Decimal("0.05"), Decimal("0.5"), Decimal("0.95"))  #: the cuts reported


@dataclass(frozen=True)
class Spread:
    """A measure's value at each cut of QUANTILES, lowest cut first."""

    low: Decimal
    median: Decimal
    high: Decimal


@dataclass(frozen=True)
class Resampled:
    """The drawdowns (a fraction of the peak, never negative) and the total returns of the paths."""

    paths: int
    drawdown: Spread
    returns: Spread


def resample(trades: Sequence[Decimal], seed: int, paths: int = PATHS) -> Resampled:
    """The spread of drawdowns and returns over `paths` resamplings of the trades' returns."""
    if not trades:
        raise ValueError("montecarlo: no trades to resample")
    if paths < 1:
        raise ValueError(f"montecarlo: paths must be at least 1, got {paths}")
    if any(t <= -1 for t in trades):
        raise ValueError("montecarlo: a trade's return of -100% or worse leaves no equity")
    rng = random.Random(seed)  # noqa: S311 - a repeatable draw, not a secret
    drawdowns: list[Decimal] = []
    returns: list[Decimal] = []
    for _ in range(paths):
        drawdown, total = _path(rng.choices(trades, k=len(trades)))
        drawdowns.append(drawdown)
        returns.append(total)
    return Resampled(paths, _spread(drawdowns), _spread(returns))


def _path(drawn: Sequence[Decimal]) -> tuple[Decimal, Decimal]:
    """The deepest fall from a peak, and the total return, of one compounded path."""
    equity = peak = Decimal(1)
    deepest = Decimal(0)
    for t in drawn:
        equity *= 1 + t
        peak = max(peak, equity)
        deepest = max(deepest, 1 - equity / peak)
    return deepest, equity - 1


def _spread(values: list[Decimal]) -> Spread:
    ordered = sorted(values)
    low, median, high = (ordered[int(q * (len(ordered) - 1))] for q in QUANTILES)
    return Spread(low, median, high)
