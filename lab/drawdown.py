"""drawdown - THE LADDER'S RESAMPLED DRAWDOWNS (Monte Carlo; they measure, and never pass).

The judged trades' pounds, after every cost, are drawn again with replacement, as many as were
judged, RESAMPLES times, from the trial's name so that a trial run again is drawn the same.
Each draw's deepest fall from a high is taken, as a part of the desk's capital. What is kept
is the median of those falls and the 95th percentile: the fall of a middling order of the
same trades, and of one in twenty. The loss that judges them is the money lane's to set.
"""

from __future__ import annotations

import random
from collections.abc import Sequence
from itertools import accumulate

from desk.command import CAPITAL
from lab.rung import Priced

RESAMPLES = 1000


def judge(trades: Sequence[Priced], name: str) -> dict[str, float]:
    """The median and the 95th percentile of the deepest fall of RESAMPLES draws of the trades,
    each a part of the capital; nothing is kept for a trial that judged no trade."""
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
    """The deepest fall of the running total from a high, the start counted as one."""
    worth = [0.0, *accumulate(draw)]
    high, deepest = 0.0, 0.0
    for now in worth:
        high = max(high, now)
        deepest = max(deepest, high - now)
    return deepest
