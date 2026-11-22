"""rung_dsr - THE LADDER'S SEVENTH RUNG: the deflated Sharpe, with the number of trials and
their spread. Is the trial's true Sharpe above the best that luck alone gives among every trial
it was picked from?

Bailey and Lopez de Prado, "The Deflated Sharpe Ratio" (Journal of Portfolio Management, 2014).
Pick the best of many trials with no edge and its Sharpe stands well above nothing: by about the
root of the SPREAD of the trials' Sharpes (their variance) times a factor that grows with their
NUMBER. That is the `bar`. The deflated Sharpe (`chance`) is the chance that the trial's true
Sharpe is above the bar, given how many trades it stands on and their shape: many small wins and
a rare large loss make a Sharpe less sure than a bell does (LAD-03). The formula and its bands
are `lab/deflated.py`'s, read from there, the bands' answer (`believe`) too.

THE ANSWER is on the bands fixed before any result: PASS at nine chances in ten or more, FAIL
under an even chance (luck is the likelier story), DOUBT between, neither won nor lost (LAD-08).

THE TWO COUNTS ARE THE CALLER'S, AND NEITHER HAS A DEFAULT. `trials` is every trial the one
judged was picked from, itself among them. `spread` is the variance of those trials' Sharpes,
each a Sharpe A TRADE as `sharpe` gives it: a spread in a year's units against a Sharpe a trade
sets a bar no edge could reach. A count under one, a spread that is no number, or more than one
trial with no spread measured, is refused loudly (LAD-09). To deflate by nothing a caller must
say so in as many words, one trial alone: its bar is nothing whatever its spread.
ONE CLUSTERED SET (L14) gives both at once (`judge_set`): its looks are the trials, the
variance of their measured Sharpes at the trial's trades the spread, and the trial's stand
above its own cluster is added to the bar, so the rung answers as `lab/deflated.py`'s `read`
does on the same set (`trials.Clustered`).

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
from collections.abc import Callable, Sequence
from decimal import Decimal, localcontext

from desk.strategy import ARITHMETIC
from lab.cell import Cell
from lab.deflated import PASS, believe, best_by_luck, deflate, per_trade, shape
from lab.rung import MIN_TRADES, Answer, standard_errors
from lab.trials import Clustered

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


def sharpe(gains: Sequence[Decimal]) -> float:
    """The Sharpe a trade: the mean gain over the first rung's own deviation of the gains."""
    with localcontext(ARITHMETIC):
        errors = standard_errors(gains)
    if errors is None:
        raise ValueError(f"{len(gains)} gains: a Sharpe needs two")
    return per_trade(float(errors), len(gains))


def chance(gains: Sequence[Decimal], trials: int, spread: float) -> float:
    """The deflated Sharpe of these gains, the skew and kurtosis their plain moments."""
    return _chance(gains, lambda _: bar(trials, spread))


def _chance(gains: Sequence[Decimal], bar_of: Callable[[float], float]) -> float:
    """The deflated Sharpe of these gains against the bar set for their Sharpe a trade."""
    values, one = [float(gain) for gain in gains], sharpe(gains)
    return deflate(one, bar_of(one), len(values), *shape(values))


def judge(gains: Sequence[Decimal], trials: int, spread: float) -> Answer:
    """The rung's answer on the gains of a trial picked from `trials`, their Sharpes' variance
    `spread`."""
    bar(trials, spread)  #: the two counts are refused before anything is answered
    if not gains:
        return Answer.FAULT
    if len(gains) < MIN_TRADES:
        return Answer.THIN
    return believe(chance(gains, trials, spread))


def chance_set(gains: Sequence[Decimal], looks: Clustered, cell: Cell) -> float:
    """The deflated Sharpe of the cell's trial picked from one clustered set: its looks and
    their measured spread at its trades set the bar, with its stand above its own cluster."""
    trades = len(gains)
    lifted = bar(looks.trials, looks.spread(trades))
    return _chance(gains, lambda one: lifted + looks.above(cell, one, trades))


def judge_set(gains: Sequence[Decimal], looks: Clustered, cell: Cell) -> Answer:
    """The rung's answer on the gains of the cell's trial, picked from one clustered set; a
    set with no spread, or one the cell's trial is not in, refused before anything is answered."""
    bar(looks.trials, looks.spread(MIN_TRADES))
    looks.above(cell, 0.0, MIN_TRADES)
    if not gains:
        return Answer.FAULT
    if len(gains) < MIN_TRADES:
        return Answer.THIN
    return believe(chance_set(gains, looks, cell))
