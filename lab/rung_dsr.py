"""rung_dsr - THE LADDER'S SEVENTH RUNG: the deflated Sharpe, with the number of trials and
their spread. Is the trial's true Sharpe above the best that luck alone gives among every trial
it was picked from?

Bailey and Lopez de Prado, "The Deflated Sharpe Ratio" (Journal of Portfolio Management, 2014).
Pick the best of many trials with no edge and its Sharpe stands well above nothing: by about the
root of the SPREAD of the trials' Sharpes (their variance) times a factor that grows with their
NUMBER. That is the `bar`. The deflated Sharpe (`chance`) is the chance that the trial's true
Sharpe is above the bar, given how many trades it stands on and their shape: many small wins and
a rare large loss make a Sharpe less sure than a bell does (LAD-03). The formula and its bands
are `lab/deflated.py`'s, read from there. The shape of the gains (their skew and kurtosis) is
worked here, for any trial's gains and any set's spread; that module works its own for the
ladder's one reading, at a spread of its own, until it reads this one.

THE ANSWER is on the bands fixed before any result: PASS at nine chances in ten or more, FAIL
under an even chance (luck is the likelier story), DOUBT between, neither won nor lost (LAD-08).

THE TWO COUNTS ARE THE CALLER'S, AND NEITHER HAS A DEFAULT. `trials` is every trial the one
judged was picked from, itself among them. `spread` is the variance of those trials' Sharpes,
each a Sharpe A TRADE as `sharpe` gives it: a spread in a year's units against a Sharpe a trade
sets a bar no edge could reach. A count under one, a spread that is no number, or more than one
trial with no spread measured, is refused loudly (LAD-09). To deflate by nothing a caller must
say so in as many words, one trial alone: its bar is nothing whatever its spread.

ITS STATED RATE (RATE) is one in ten, AND IT IS THE RATE OF BELL GAINS. A trial whose true
Sharpe is exactly the bar passes about that often, so bell noise judged alone (a bar of
nothing) does; and the pick of a hundred trials of bell noise, judged against the hundred and
their spread, about one time in a hundred.

IT IS NOT THE RATE OF LOPSIDED GAINS AS SAMPLED. Among noise of many small wins and a rare
large loss, a trial that happened to meet no loss shows a high Sharpe and nothing lopsided;
the pick of a set is nearly always such a one, and the bar, which takes the set's Sharpes for a
bell's, lies far under it. The tests record it: at one loss in twenty, nineteen times a win,
on sixty trades, nearly every pick of a hundred passes. No sample holds the loss that has not
come yet: that loss is the first rung's to plant (G2). So THE GAINS TO HAND IN ARE
`Verdict.gains`, the planted loss among them, and the set's spread is measured on the same;
with it planted, no pick of that noise passed. No rule passes the ladder by this rung alone.

FAILING FAIRLY (LAD-06). No gain at all is a FAULT in the test; under MIN_TRADES it is THIN, never
a fail and never a pass; gains with no spread are refused loudly (`rung.standard_errors`).
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from decimal import Decimal, localcontext
from statistics import fmean

from desk.strategy import ARITHMETIC
from lab.deflated import FAIL, PASS, best_by_luck, deflate
from lab.rung import MIN_TRADES, Answer, standard_errors

#: About what a trial of bell gains with no more than luck's best passes at.
RATE = 1 - PASS


def bar(trials: int, spread: float) -> float:
    """The Sharpe to expect of the best of so many trials with no edge, their Sharpes spread
    by this variance; nothing for one trial alone."""
    if trials < 1 or not 0 <= spread < math.inf or (trials > 1 and not spread):
        raise ValueError(
            f"{trials} trials, their Sharpes spread by {spread}: nothing to deflate by"
        )
    return best_by_luck(spread, trials)


def deflated(
    sharpe: float, trades: int, skew: float, kurtosis: float, trials: int, spread: float
) -> float:
    """The paper's figure: the chance that a Sharpe a trade, measured on so many trades of this
    skew and kurtosis (a bell's are 0 and 3), is truly above luck's best among the trials."""
    return deflate(sharpe, bar(trials, spread), trades, skew, kurtosis)


def sharpe(gains: Sequence[Decimal]) -> float:
    """The Sharpe a trade: the mean gain over the first rung's own deviation of the gains."""
    with localcontext(ARITHMETIC):
        errors = standard_errors(gains)
    if errors is None:
        raise ValueError(f"{len(gains)} gains: a Sharpe needs two")
    return float(errors) / math.sqrt(len(gains))


def chance(gains: Sequence[Decimal], trials: int, spread: float) -> float:
    """The deflated Sharpe of these gains, the skew and kurtosis their plain moments."""
    measured, values = sharpe(gains), [float(gain) for gain in gains]
    mean = fmean(values)
    second, third, fourth = (fmean((v - mean) ** power for v in values) for power in (2, 3, 4))
    return deflated(measured, len(values), third / second**1.5, fourth / second**2, trials, spread)


def judge(gains: Sequence[Decimal], trials: int, spread: float) -> Answer:
    """The rung's answer on the gains of a trial picked from `trials`, their Sharpes' variance
    `spread`."""
    bar(trials, spread)  #: the two counts are refused before anything is answered
    if not gains:
        return Answer.FAULT
    if len(gains) < MIN_TRADES:
        return Answer.THIN
    believed = chance(gains, trials, spread)
    if believed >= PASS:
        return Answer.PASS
    return Answer.DOUBT if believed >= FAIL else Answer.FAIL
