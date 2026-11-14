"""drawdown - THE LADDER'S RESAMPLED DRAWDOWNS (Monte Carlo; they measure, and never pass).

The judged trades' pounds, after every cost, are drawn again with replacement, as many as were
judged, RESAMPLES times, seeded by the trial's name. Each draw's deepest fall from a high is
taken as a part of the capital; the median and the 95th percentile are kept.
"""

from __future__ import annotations

import random
from collections.abc import Sequence
from itertools import accumulate

from desk.command import CAPITAL
from lab.rung import Priced

RESAMPLES = 1000


def judge(trades: Sequence[Priced], name: str) -> dict[str, float]:
    """The median and 95th percentile of the deepest fall of RESAMPLES draws of the trades."""
    if not trades:
        raise ValueError(f"{name}: no judged trade to draw a drawdown from")
    pounds = [float(t.gross - t.costs.total) for t in trades]
    rng = random.Random(name)  # noqa: S311 - a repeatable draw, not a secret
    falls = sorted(_fall(rng.choices(pounds, k=len(pounds))) for _ in range(RESAMPLES))
    return {
        "median": falls[RESAMPLES // 2] / float(CAPITAL),
        "p95": falls[RESAMPLES * 95 // 100] / float(CAPITAL),
    }


def _fall(draw: Sequence[float]) -> float:
    """The deepest fall of the running total from a high."""
    worth = [0.0, *accumulate(draw)]
    high, deepest = 0.0, 0.0
    for now in worth:
        high = max(high, now)
        deepest = max(deepest, high - now)
    return deepest
