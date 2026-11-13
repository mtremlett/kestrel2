"""luck - THE LADDER'S LUCK RUNG: a winner is believed only when its chance, multiplied by
every trial it was picked from, is still small.

Try enough strategies on enough lines and some pass the first rung (`lab/rung.py`) with no
edge at all: at its bar, about one trial in forty. So the first rung's verdicts are judged
again as one set. Each verdict's chance is the chance of an average that many standard errors
up, or further, from trades with no edge (Student's t on its trades). That chance times the
number of trials is its corrected chance, and a verdict passes this rung when it passed the
first and its corrected chance is at most FAMILY. Then, if no trial in the set has an edge
and each trial's own chance is true, the chance that even one passes is at most FAMILY,
however the trials lean on one another (Bonferroni's bound: five rules on one line share its
history, and it still holds). A trial's own chance is true only for trades that are separate
bets with gains spread roughly like a bell: many small wins and a rare large loss, on few
trades, read as far less chance than they are, and the bound does not cover that.

Every trial counts, whatever became of it: a loser, a trial with too few trades, and one that
gave no verdict at all (a cell that failed, a candidate dropped), which the caller must
count aloud. Each corrected verdict records the count it was corrected for.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

from lab.rung import Verdict

#: One combined 5% test across the set (LAD-08): of twenty sets with no edge in any trial,
#: about one will still hand over a winner.
FAMILY = 0.05


@dataclass(frozen=True)
class Corrected:
    verdict: Verdict
    trials: int  #: every trial the verdict was picked from, itself included
    chance: float  #: of its standard errors or more from no edge; 1 with under two trades
    corrected: float  #: the chance times the trials, at most 1
    passed: bool


def correct(verdicts: Sequence[Verdict], unjudged: int) -> tuple[Corrected, ...]:
    """Every verdict corrected for the whole set: the verdicts given, and the trials tried
    that left no verdict, which count as much as any."""
    if unjudged < 0:
        raise ValueError(f"{unjudged} trials without a verdict: a count cannot be under nothing")
    trials = len(verdicts) + unjudged
    return tuple(_corrected(verdict, trials) for verdict in verdicts)


def _corrected(verdict: Verdict, trials: int) -> Corrected:
    chance = 1.0 if verdict.t is None else tail(float(verdict.t), len(verdict.trades) - 1)
    corrected = min(1.0, chance * trials)
    return Corrected(verdict, trials, chance, corrected, verdict.passed and corrected <= FAMILY)


def tail(t: float, freedom: int) -> float:
    """The chance that Student's t, at these degrees of freedom, is t or more. Writing the
    variable as the root of the freedom times the tangent of an angle turns the tail into the
    integral of the cosine to the power freedom - 1, from t's angle to a right angle: smooth
    and bounded, taken by Simpson's rule in steps far finer than the curve's width."""
    start = math.atan(t / math.sqrt(freedom))
    steps = 2 * math.ceil(100 * math.sqrt(freedom))
    width = (math.pi / 2 - start) / steps
    area = sum(
        (1 if n in (0, steps) else 4 if n % 2 else 2) * math.cos(start + n * width) ** (freedom - 1)
        for n in range(steps + 1)
    )
    scale = math.exp(math.lgamma((freedom + 1) / 2) - math.lgamma(freedom / 2)) / math.sqrt(math.pi)
    return scale * area * width / 3
