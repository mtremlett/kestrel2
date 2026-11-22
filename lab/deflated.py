"""deflated - THE LUCK TEST FIXED BEFORE ANY RESULT: the deflated Sharpe and its bands, the
yearly Sharpe too good to be true, and the one rule that turns the named rungs into a verdict.

Everything here is a constant or a rule with no knob: the bands, the 5%, the flag and the
list of rungs are written down before any strategy is run: a bar is set by a rule fixed
beforehand, never by a look at the result.

THE DEFLATED SHARPE (Bailey and Lopez de Prado, 2014). A trial's Sharpe is its mean gain a
trade over the spread of its gains. Pick the best of many trials with no edge and its Sharpe
is well above nothing by luck alone: by about the spread of the trials' Sharpes times a
factor that grows with their number (`best_by_luck`). The deflated Sharpe is the chance
that the trial's true Sharpe is above that bar, given how many trades it stands on and their
shape: many small wins and a rare large loss make a Sharpe less sure than a bell does, which
the luck rung's own chance (`lab/luck.py`) cannot see. At PASS or more the trial is believed;
under FAIL, luck is the likelier story; between them it is in doubt, neither won nor lost.

Judged as separate looks, the bar is fixed by two counts alone. The number of trials is
every trial, as on the luck
rung. The spread is the one a Sharpe with no edge has by its trades alone, one over the
trades less one, the trial's own trades standing for every trial's: so no trial's bar moves
with the company it is judged in, and the trials that can pass (thirty trades or more, the
first rung's least) are not far from it. The trials are taken as separate looks, as many
as a set can hold. The Sharpe is on the first rung's own deviation; the skew and the kurtosis
are the plain moments of the gains.

ONE CLUSTERED SET (L14). Where the set's trials have been clustered by how their returns move
together (`trials.clusters`), `read` takes both counts from the clusters instead: the number
of trials is the looks the set truly took, and the spread is the one measured among those
looks' Sharpes, at the trial's own trades. To that the bar adds the luck of the pick inside
the trial's own cluster: whatever its Sharpe a trade stands above its cluster's restated to a
trade, so a trial is judged no better than its cluster. Fifty copies of one strategy then
set the bar of one trial, and
fifty strangers that of fifty. The luck rung's count is every trial, as before. That bar is
fixed by rule and not by number: it is measured on the set's own returns, the trial's among
them, and where the looks' true Sharpes differ it can stand above the bar of as many separate
looks. Whether the set is clustered is said by the caller in so many words, never left out.

THE YEARLY SHARPE. Canon B6: a daily Sharpe above 2 is a red flag, not a win. It is worked
here from the trades: the Sharpe a trade times the root of the trades a year over the
trial's window, which is what daily accounts come to over a year when one trade's gain tells
nothing of the next. Above FLAG the trial is in doubt however it scored: such a result is
far more often a fault in the test (a peek ahead, a cost left out) than an edge.

THE ONE RULE. Each rung in NAMED gives its answer (`rung.Answer`); the verdict is the least
of them, and `rule` refuses a set of answers that is not exactly the named rungs, so none can
be left out after its answer is seen. Four are read here from the trial's trades (OWN); the
folds (`lab/folds.py`) and the market (`lab/market.py`) are read where they are run, and a
trial short of any one has no verdict. A later rung joins by being named here.

ONE CORRECTION, NOT TWO (L18, decision b). The luck rung multiplies a trial's chance by every
trial ever entered (3,435 a rule against about 1,017 judged), asking a t of 4.6 no line has
reached, and the deflated Sharpe corrects the same pick for luck again. Charged twice, a real
edge cannot pass. So the deflated Sharpe, on the set's clustered looks, is the gate; the luck
rung is read and reported (OWN) and is no rung of the rule (NAMED), so it bounds no verdict.

FAILING FAIRLY (LAD-06). Every rung here reads the one trial's trades, so where the first
rung found too few of them, or none, no rung has anything more to judge: each gives the
first rung's own answer, not enough evidence or a fault in the test, and none a fail. Such
a trial still counts among the trials every other is corrected for.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from statistics import NormalDist, fmean

from lab import luck
from lab.luck import Corrected
from lab.rung import Answer, Verdict
from lab.trials import Clustered

#: The bands of the deflated Sharpe (LAD-03): believed at nine chances in ten that the true
#: Sharpe beats luck's best; failed under an even chance; in doubt between.
PASS = 0.90
FAIL = 0.50
#: The yearly Sharpe above which a result is flagged (canon B6).
FLAG = 2.0
#: The rungs the one rule reads (LAD-09), each trial judged on every one.
NAMED = ("first", "deflated", "yearly", "folds", "market", "shuffle")
#: The rungs read here from the trial's trades: the luck rung reported, the rest in NAMED.
OWN = ("first", "luck", "deflated", "yearly")

_NORMAL = NormalDist()
_EULER = 0.5772156649015329
_YEAR = 365.25


def rule(rungs: Mapping[str, Answer]) -> Answer:
    """The one verdict rule: the least answer among the named rungs, every one of them."""
    if set(rungs) != set(NAMED):
        raise ValueError(f"the rule reads {NAMED}, every one and no other: given {sorted(rungs)}")
    return min(rungs.values())


@dataclass(frozen=True)
class Deflated:
    luck: Corrected  #: the luck rung's corrected verdict: the trial, its count, its chance
    sharpe: float | None  #: the mean gain a trade over the gains' spread; None under two trades
    yearly: float | None  #: the Sharpe a year over the trial's window
    bar: float | None  #: the best Sharpe luck alone gives among the trials, at its trades
    deflated: float  #: the chance the true Sharpe is above the bar; 0 without a Sharpe

    @property
    def rungs(self) -> dict[str, Answer]:
        """The answer on this trial of each named rung read here (OWN)."""
        first = self.luck.verdict.answer
        if first in (Answer.FAULT, Answer.THIN):
            return dict.fromkeys(OWN, first)
        flagged = self.yearly is not None and self.yearly > FLAG
        return {
            "first": first,
            "luck": Answer.PASS if self.luck.passed else Answer.FAIL,
            "deflated": believe(self.deflated),
            "yearly": Answer.DOUBT if flagged else Answer.PASS,
        }

    @property
    def least(self) -> Answer:
        """The least of the named rungs read here: a bound on the verdict, never the verdict;
        the luck rung, reported only, bounds nothing."""
        return min(answer for name, answer in self.rungs.items() if name in NAMED)


def judge(verdicts: Sequence[Verdict], unjudged: int) -> tuple[Deflated, ...]:
    """Every verdict judged on the rungs read here, as one set: the verdicts given, and the
    trials tried that left no verdict, which count as much as any."""
    return read(luck.correct(verdicts, unjudged), None)


def read(corrected: Sequence[Corrected], looks: Clustered | None) -> tuple[Deflated, ...]:
    """Verdicts already corrected for their count, judged on the rungs read here: the door for
    a count the register of trials keeps from batch to batch (`trials.correct`). Given the
    same set clustered, the deflated Sharpe's bar is set by its looks, their measured spread
    and the trial's stand above its own cluster; given None, by every trial as a separate look."""
    if looks is not None and (odd := {one.trials for one in corrected} - {looks.held}):
        raise ValueError(
            f"verdicts corrected for {sorted(odd)} trials, read against a clustered set of "
            f"{looks.held}: not the one set"
        )
    return tuple(_deflated(one, looks) for one in corrected)


def best_by_luck(spread: float, trials: int) -> float:
    """The Sharpe to expect of the best of so many trials with no edge, their Sharpes spread
    by this variance: nothing for one trial alone."""
    if trials == 1:
        return 0.0
    best = (1 - _EULER) * _NORMAL.inv_cdf(1 / trials)
    return -math.sqrt(spread) * (best + _EULER * _NORMAL.inv_cdf(1 / (trials * math.e)))


def per_trade(t: float, trades: int) -> float:
    """The Sharpe a trade: the first rung's standard errors (its t) over the root of the trades."""
    return t / math.sqrt(trades)


def believe(chance: float) -> Answer:
    """The answer on a deflated Sharpe's chance, on the bands fixed beforehand."""
    return Answer.PASS if chance >= PASS else Answer.DOUBT if chance >= FAIL else Answer.FAIL


def shape(values: Sequence[float]) -> tuple[float, float]:
    """The skew and kurtosis of values from their plain moments (a bell's are 0 and 3)."""
    mean = fmean(values)
    second, third, fourth = (fmean((v - mean) ** power for v in values) for power in (2, 3, 4))
    return third / second**1.5, fourth / second**2


def deflate(sharpe: float, bar: float, trades: int, skew: float, kurtosis: float) -> float:
    """The chance that the true Sharpe is above the bar, for a Sharpe measured on so many
    trades whose gains have this skew and kurtosis (a bell's are 0 and 3)."""
    wobble = 1 - skew * sharpe + (kurtosis - 1) / 4 * sharpe**2
    if wobble <= 0:
        raise ValueError(f"a Sharpe of {sharpe}, skew {skew}, kurtosis {kurtosis}: no error left")
    return _NORMAL.cdf((sharpe - bar) * math.sqrt((trades - 1) / wobble))


def _deflated(corrected: Corrected, looks: Clustered | None) -> Deflated:
    verdict = corrected.verdict
    if verdict.t is None:
        return Deflated(corrected, None, None, None, 0.0)
    gains = [float(gain) for gain in verdict.gains]
    sharpe = per_trade(float(verdict.t), len(gains))
    if looks is None:
        bar = best_by_luck(1 / (len(gains) - 1), corrected.trials)
    else:
        bar = best_by_luck(looks.spread(len(gains)), looks.trials)
        bar += looks.above(verdict.key.cell, sharpe, len(gains))
    chance = deflate(sharpe, bar, len(gains), *shape(gains))
    window = verdict.key.cell
    years = (window.end - window.start).days / _YEAR
    return Deflated(corrected, sharpe, sharpe * math.sqrt(len(gains) / years), bar, chance)
