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
say so in as many words, one trial alone: its bar is nothing whatever its spread. Or both
come from ONE CLUSTERED SET (L14, `trials.clusters`), handed to `judge_set`: the looks the set
truly took, their spread measured, and the pick's luck inside its own cluster added to the bar.

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


def judge(gains: Sequence[Decimal], trials: int, spread: float) -> Answer:
    """The rung's answer on the gains of a trial picked from `trials`, their Sharpes' variance
    `spread`."""
    bar(trials, spread)  #: the two counts are refused before anything is answered
    return _answer(gains, lambda _: bar(trials, spread))


def judge_set(gains: Sequence[Decimal], cell: Cell, looks: Clustered) -> Answer:
    """The rung's answer on the gains of the cell's trial, picked from one clustered set: the
    bar its looks set at their measured spread, raised by the trial's stand above its own
    cluster (`lab/trials.py`), as the deflated rung reads the same set."""
    trades = len(gains)
    looks.spread(max(trades, 1))  #: refused first: more looks than one and no spread measured
    looks.above(cell, 0.0, 1)  #: refused first: a trial this set was not clustered from
    return _answer(
        gains, lambda one: bar(looks.trials, looks.spread(trades)) + looks.above(cell, one, trades)
    )


def _answer(gains: Sequence[Decimal], raised: Callable[[float], float]) -> Answer:
    """FAULT on no gain, THIN under MIN_TRADES, else the bands on the chance above the bar."""
    if not gains:
        return Answer.FAULT
    if len(gains) < MIN_TRADES:
        return Answer.THIN
    return believe(_chance(gains, raised))


def _chance(gains: Sequence[Decimal], raised: Callable[[float], float]) -> float:
    """The deflated Sharpe of the gains against the bar `raised` sets on their Sharpe."""
    one, values = sharpe(gains), [float(gain) for gain in gains]
    return deflate(one, raised(one), len(values), *shape(values))
