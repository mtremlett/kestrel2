"""deflated - THE LUCK TEST FIXED BEFORE ANY RESULT: the deflated Sharpe and its bands, the
yearly Sharpe too good to be true, and the one rule that turns the named rungs into a verdict.

Everything here is a constant or a rule with no knob: the bands, the 5%, the flag and the
list of rungs are written down before any strategy is run, so no result can move its own bar.

THE DEFLATED SHARPE (Bailey and Lopez de Prado, 2014). A trial's Sharpe is its mean gain a
trade over the spread of its gains. Pick the best of many trials with no edge and its Sharpe
is well above nothing by luck alone: by about the spread of the trials' Sharpes times a
factor that grows with their number (`best_by_luck`). The deflated Sharpe is the chance
that the trial's true Sharpe is above that bar, given how many trades it stands on and their
shape: many small wins and a rare large loss make a Sharpe less sure than a bell does, which
the luck rung's own chance (`lab/luck.py`) cannot see. At PASS or more the trial is believed;
under FAIL, luck is the likelier story; between them it is in doubt, neither won nor lost.

The bar is fixed by two counts alone. The number of trials is every trial, as on the luck
rung. The spread is the one a Sharpe with no edge has by its trades alone, one over the
trades less one, the trial's own trades standing for every trial's: so no trial's bar moves
with the company it is judged in, and the trials that can pass (thirty trades or more, the
first rung's least) are not far from it. The trials are taken as separate looks, which sets
the bar highest. The Sharpe is on the first rung's own deviation; the skew and the kurtosis
are the plain moments of the gains.

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

#: The bands of the deflated Sharpe (LAD-03): believed at nine chances in ten that the true
#: Sharpe beats luck's best; failed under an even chance; in doubt between.
PASS = 0.90
FAIL = 0.50
#: The yearly Sharpe above which a result is flagged (canon B6).
FLAG = 2.0
#: The rungs the one rule reads (LAD-09), each trial judged on every one; the first four here.
NAMED = ("first", "luck", "deflated", "yearly", "folds", "market", "shuffle")
OWN = NAMED[:4]

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
        doubted = Answer.DOUBT if self.deflated >= FAIL else Answer.FAIL
        flagged = self.yearly is not None and self.yearly > FLAG
        return {
            "first": first,
            "luck": Answer.PASS if self.luck.passed else Answer.FAIL,
            "deflated": Answer.PASS if self.deflated >= PASS else doubted,
            "yearly": Answer.DOUBT if flagged else Answer.PASS,
        }

    @property
    def least(self) -> Answer:
        """The least of the rungs read here: a bound on the verdict, never the verdict."""
        return min(self.rungs.values())


def judge(verdicts: Sequence[Verdict], unjudged: int) -> tuple[Deflated, ...]:
    """Every verdict judged on the rungs read here, as one set: the verdicts given, and the
    trials tried that left no verdict, which count as much as any."""
    return read(luck.correct(verdicts, unjudged))


def read(corrected: Sequence[Corrected]) -> tuple[Deflated, ...]:
    """Verdicts already corrected for their count, judged on the rungs read here: the door for
    a count the register of trials keeps from batch to batch (`trials.correct`)."""
    return tuple(_deflated(one) for one in corrected)


def best_by_luck(spread: float, trials: int) -> float:
    """The Sharpe to expect of the best of so many trials with no edge, their Sharpes spread
    by this variance: nothing for one trial alone."""
    if trials == 1:
        return 0.0
    best = (1 - _EULER) * _NORMAL.inv_cdf(1 / trials)
    return -math.sqrt(spread) * (best + _EULER * _NORMAL.inv_cdf(1 / (trials * math.e)))


def deflate(sharpe: float, bar: float, trades: int, skew: float, kurtosis: float) -> float:
    """The chance that the true Sharpe is above the bar, for a Sharpe measured on so many
    trades whose gains have this skew and kurtosis (a bell's are 0 and 3)."""
    wobble = 1 - skew * sharpe + (kurtosis - 1) / 4 * sharpe**2
    if wobble <= 0:
        raise ValueError(f"a Sharpe of {sharpe}, skew {skew}, kurtosis {kurtosis}: no error left")
    return _NORMAL.cdf((sharpe - bar) * math.sqrt((trades - 1) / wobble))


def _deflated(corrected: Corrected) -> Deflated:
    verdict = corrected.verdict
    if verdict.t is None:
        return Deflated(corrected, None, None, None, 0.0)
    gains = [float(priced.gain) for priced in verdict.trades]
    #: the first rung's standard errors are the Sharpe times the root of the trades
    sharpe = float(verdict.t) / math.sqrt(len(gains))
    bar = best_by_luck(1 / (len(gains) - 1), corrected.trials)
    mean = fmean(gains)
    second, third, fourth = (fmean((g - mean) ** power for g in gains) for power in (2, 3, 4))
    chance = deflate(sharpe, bar, len(gains), third / second**1.5, fourth / second**2)
    window = verdict.key.cell
    years = (window.end - window.start).days / _YEAR
    return Deflated(corrected, sharpe, sharpe * math.sqrt(len(gains) / years), bar, chance)
