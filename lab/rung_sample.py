"""rung_sample - THE FIRST RUNG'S STATED RATE: how often a cell with no edge may pass the rung
of sample size (`lab/rung.py`: at least MIN_TRADES effective trades, each its own bet, and
their mean T_PASS standard errors above nothing), and the band that many noise cells must fall in.

STATED is fixed when this module loads, from the rung's own two numbers: the chance that
Student's t on MIN_TRADES trades reaches T_PASS (`luck.tail`). More trades pass noise less
often, so it is the most a no-edge cell may pass at: a rung altered afterwards (a bar
lowered, a minimum dropped) drifts from it and falls out of `band`. `band` is the exact
binomial interval of passes among so many independent noise cells, in which a sound rung lands
all but once in a thousand runs.
"""

from __future__ import annotations

from math import comb

from lab import luck, rung

#: The most a cell with no edge passes at, by the rung as built.
STATED = luck.tail(float(rung.T_PASS), rung.MIN_TRADES - 1)
#: The band holds all but this share of runs of a sound rung, split between its two ends.
MISS = 0.001


def band(cells: int, rate: float = STATED, miss: float = MISS) -> tuple[int, int]:
    """The fewest and most passes among this many independent cells that each pass at `rate`,
    leaving no more than half of `miss` beyond either end (the exact binomial)."""
    if cells < 1 or not 0 < rate < 1 or not 0 < miss < 1:
        raise ValueError(f"a band of {cells} cells at {rate}, missing {miss}: out of range")
    below = 0.0
    low = high = cells
    for k in range(cells + 1):
        below += comb(cells, k) * rate**k * (1 - rate) ** (cells - k)
        if below > miss / 2 and low == cells:
            low = k
        if below >= 1 - miss / 2:
            high = k
            break
    return low, high
