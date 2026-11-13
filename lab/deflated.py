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
The number of trials is every trial, as on the luck rung; their spread is taken from those
that have a Sharpe, losers with the rest. The trials are taken as separate looks: trials
that lean on one another make the bar higher than it need be, never lower.

THE YEARLY SHARPE. Canon B6: a daily Sharpe above 2 is a red flag, not a win. It is worked
here from the trades: the Sharpe a trade times the root of the trades a year over the
trial's window, which is what daily accounts come to over a year when one trade's gain tells
nothing of the next. Above FLAG the trial is in doubt however it scored: such a result is
far more often a fault in the test (a peek ahead, a cost left out) than an edge.

THE ONE RULE. Each rung in NAMED answers pass, doubt or fail; the verdict is the worst of
them, and `rule` refuses a set of answers that is not exactly the named rungs, so none can
be left out after its answer is seen. A later rung joins by being named here.
"""

from __future__ import annotations

import enum
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from statistics import NormalDist, fmean, variance

from lab import luck
from lab.luck import Corrected
from lab.rung import Verdict

#: The bands of the deflated Sharpe (LAD-03): believed at nine chances in ten that the true
#: Sharpe beats luck's best; failed under an even chance; in doubt between.
PASS = 0.90
FAIL = 0.50
#: The yearly Sharpe above which a result is flagged (canon B6).
FLAG = 2.0
#: The rungs the one rule reads (LAD-09), each trial judged on every one.
NAMED = ("first", "luck", "deflated", "yearly")

_NORMAL = NormalDist()
_EULER = 0.5772156649015329
_YEAR = 365.25


class Answer(enum.IntEnum):
    """A rung's answer, and the rule's; the worst is the least."""

    FAIL = 0
    DOUBT = 1  #: neither a win nor a loss: not promoted, and not thrown away
    PASS = 2


def rule(rungs: Mapping[str, Answer]) -> Answer:
    """The one verdict rule: the worst answer among the named rungs, every one of them."""
    if set(rungs) != set(NAMED):
        raise ValueError(f"the rule reads {NAMED}, every one and no other: given {sorted(rungs)}")
    return min(rungs.values())


@dataclass(frozen=True)
class Deflated:
    luck: Corrected  #: the luck rung's corrected verdict: the trial, its count, its chance
    sharpe: float | None  #: the mean gain a trade over the gains' spread; None under two trades
    yearly: float | None  #: the Sharpe a year over the trial's window
    bar: float  #: the best Sharpe a trade that luck alone would give among the trials
    deflated: float  #: the chance the true Sharpe is above the bar; 0 without a Sharpe

    @property
    def rungs(self) -> dict[str, Answer]:
        """Each named rung's answer on this trial."""
        believed = Answer.PASS if self.deflated >= PASS else Answer(self.deflated >= FAIL)
        flagged = self.yearly is not None and self.yearly > FLAG
        return {
            "first": Answer.PASS if self.luck.verdict.passed else Answer.FAIL,
            "luck": Answer.PASS if self.luck.passed else Answer.FAIL,
            "deflated": believed,
            "yearly": Answer.DOUBT if flagged else Answer.PASS,
        }

    @property
    def answer(self) -> Answer:
        return rule(self.rungs)


def judge(verdicts: Sequence[Verdict], unjudged: int) -> tuple[Deflated, ...]:
    """Every verdict judged on every named rung, as one set: the verdicts given, and the
    trials tried that left no verdict, which count as much as any."""
    corrected = luck.correct(verdicts, unjudged)
    sharpes = [_sharpe(verdict) for verdict in verdicts]
    known = [sharpe for sharpe in sharpes if sharpe is not None]
    trials = len(verdicts) + unjudged
    if trials > 1 and len(known) < 2:
        raise ValueError(
            f"{trials} trials and {len(known)} with a Sharpe: the spread of the trials' Sharpes "
            "cannot be known from under two, so luck's best among them cannot be either"
        )
    bar = best_by_luck(variance(known), trials) if trials > 1 else 0.0
    return tuple(_deflated(c, s, bar) for c, s in zip(corrected, sharpes, strict=True))


def best_by_luck(spread: float, trials: int) -> float:
    """The Sharpe to expect of the best of so many trials with no edge, their Sharpes spread
    by this variance: nothing for one trial alone."""
    if trials == 1:
        return 0.0
    best = (1 - _EULER) * _NORMAL.inv_cdf(1 - 1 / trials)
    return math.sqrt(spread) * (best + _EULER * _NORMAL.inv_cdf(1 - 1 / (trials * math.e)))


def deflate(sharpe: float, bar: float, trades: int, skew: float, kurtosis: float) -> float:
    """The chance that the true Sharpe is above the bar, for a Sharpe measured on so many
    trades whose gains have this skew and kurtosis (a bell's are 0 and 3)."""
    wobble = 1 - skew * sharpe + (kurtosis - 1) / 4 * sharpe**2
    if wobble <= 0:
        raise ValueError(f"a Sharpe of {sharpe} on {trades} trades: gains of two values only")
    return _NORMAL.cdf((sharpe - bar) * math.sqrt((trades - 1) / wobble))


def _sharpe(verdict: Verdict) -> float | None:
    """The first rung's standard errors are the Sharpe times the root of the trades."""
    return None if verdict.t is None else float(verdict.t) / math.sqrt(len(verdict.trades))


def _deflated(corrected: Corrected, sharpe: float | None, bar: float) -> Deflated:
    verdict = corrected.verdict
    if sharpe is None:
        return Deflated(corrected, None, None, bar, 0.0)
    gains = [float(priced.gain) for priced in verdict.trades]
    mean = fmean(gains)
    second, third, fourth = (fmean((g - mean) ** power for g in gains) for power in (2, 3, 4))
    chance = deflate(sharpe, bar, len(gains), third / second**1.5, fourth / second**2)
    window = verdict.key.cell
    years = (window.end - window.start).days / _YEAR
    return Deflated(corrected, sharpe, sharpe * math.sqrt(len(gains) / years), bar, chance)
