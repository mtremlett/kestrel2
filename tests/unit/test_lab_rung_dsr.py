"""The deflated Sharpe (rung 7, R-RUNNER-135), proven alone: the paper's own worked case, a
planted edge, pure noise at the stated rate and no more, a power curve, two broken copies, and
the old audit's defects (LAD-09, LAD-03, LAD-08) kept as cases that must fail."""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from decimal import Decimal
from functools import cache

import numpy as np
import pytest

from lab import rung_dsr
from lab.deflated import FAIL, PASS
from lab.rung import MIN_TRADES, Answer
from lab.rung_sample import band

Judge = Callable[[Sequence[Decimal], int, float], Answer]
CELLS, TRIALS, TRADES = 500, 100, 60
#: THE POWER CURVE, recorded: of CELLS sets of TRIALS trials, one with this true Sharpe a trade
#: planted among noise, those whose pick passes against the whole set
POWER = {0.3: 33, 0.5: 208, 0.8: 492}


@cache
def _picks(edge: float) -> tuple[tuple[tuple[Decimal, ...], float], ...]:
    """CELLS sets of TRIALS trials of TRADES bell gains, all noise but the first of each set,
    whose true Sharpe a trade is `edge`: each set's best trial, and the spread of its Sharpes."""
    rng, picks = np.random.default_rng(round(edge * 10)), []
    for _ in range(CELLS):
        gains = rng.standard_normal((TRIALS, TRADES))
        gains[0] += edge
        sharpes = gains.mean(axis=1) / gains.std(axis=1, ddof=1)
        best = tuple(map(Decimal, gains[sharpes.argmax()].tolist()))
        picks.append((best, float(sharpes.var(ddof=1))))
    return tuple(picks)


def _passes(judge: Judge, edge: float, trials: int = TRIALS) -> int:
    """How many of the picks pass, each judged against `trials` and its own set's spread."""
    return sum(judge(gains, trials, spread) is Answer.PASS for gains, spread in _picks(edge))


def _edge(judge: Judge) -> bool:
    """A planted edge passes: a true Sharpe of 1 a trade among a hundred trials, 499 in 500."""
    return _passes(judge, 1.0) > 0.99 * CELLS


def _noise(judge: Judge) -> bool:
    """Pure noise passes at about the stated rate judged alone, and its pick of a hundred,
    judged against the hundred, no more often: each inside the exact binomial band."""
    rng = np.random.default_rng(7)
    alone = (tuple(map(Decimal, rng.standard_normal(TRADES).tolist())) for _ in range(CELLS))
    low, high = band(CELLS, rung_dsr.RATE)
    passed = sum(judge(gains, 1, 0.0) is Answer.PASS for gains in alone)  #: 56 of 500
    return low <= passed <= high and _passes(judge, 0.0) <= high  #: the picks: 4 of 500


def _power(judge: Judge) -> bool:
    return [_passes(judge, edge) for edge in POWER] == list(POWER.values())


def test_the_deflated_sharpe_is_bailey_and_lopez_de_prados_own_worked_case() -> None:
    """Bailey and Lopez de Prado, "The Deflated Sharpe Ratio: Correcting for Selection Bias,
    Backtest Overfitting, and Non-Normality", Journal of Portfolio Management 40(5), 2014, the
    numerical example. The best of N = 100 trials has a yearly Sharpe of 2.5 on T = 1,250 daily
    returns of skew -3 and kurtosis 10; the trials' yearly Sharpes have a variance of 1/2. A
    day, at 250 to the year: a Sharpe of 2.5 / sqrt(250) and a variance of 1 / 500. The paper:
    luck's best is 0.1132 a day and the deflated Sharpe 0.9004; found among 46 trials, 0.9505."""
    sharpe = 2.5 / math.sqrt(250)
    assert rung_dsr.bar(100, 1 / 500) == pytest.approx(0.1132, abs=5e-5)
    assert rung_dsr.deflated(sharpe, 1250, -3, 10, 100, 1 / 500) == pytest.approx(0.9004, abs=5e-5)
    assert rung_dsr.deflated(sharpe, 1250, -3, 10, 46, 1 / 500) == pytest.approx(0.9505, abs=5e-5)
    #: by hand: 32 gains of 2% and 8 losses of 3%. Mean 1%; about it the squares average
    #: 0.0004, the cubes -0.000012, the fourth powers 0.00000052: skew -1.5, kurtosis 3.25.
    #: The deviation on 39 is 0.02 * sqrt(40 / 39), so the Sharpe is a half * sqrt(39 / 40)
    gains = [Decimal("0.02")] * 32 + [Decimal("-0.03")] * 8
    assert rung_dsr.sharpe(gains) == pytest.approx(0.5 * math.sqrt(39 / 40))
    assert rung_dsr.chance(gains, 9, 0.01) == pytest.approx(
        rung_dsr.deflated(0.5 * math.sqrt(39 / 40), 40, -1.5, 3.25, 9, 0.01)
    )
    assert math.isclose(rung_dsr.RATE, 0.10) and rung_dsr.bar(1, 0.0) == 0, "one trial: no bar"


@pytest.mark.parametrize("proof", [_edge, _noise, _power])
def test_the_rung_passes_each_proof(proof: Callable[[Judge], bool]) -> None:
    assert proof(rung_dsr.judge)


def test_a_broken_copy_is_caught() -> None:
    """Two plausible mistakes: the count of trials forgotten, so the pick of a hundred is
    judged as one alone; and the spread left in a year's units against a Sharpe a trade."""

    def no_count(gains: Sequence[Decimal], _trials: int, _spread: float) -> Answer:
        return rung_dsr.judge(gains, 1, 0.0)

    def yearly_spread(gains: Sequence[Decimal], trials: int, spread: float) -> Answer:
        return rung_dsr.judge(gains, trials, 250 * spread)

    assert _edge(no_count) and not _noise(no_count) and not _power(no_count)
    assert _passes(no_count, 0.0) > 0.99 * CELLS, "luck's best of a hundred, passed nearly always"
    assert not _edge(yearly_spread) and not _power(yearly_spread), "no edge could ever pass"


def test_the_old_audits_defects_must_fail() -> None:
    wins = [Decimal(1) + Decimal(n) / 100 for n in range(MIN_TRADES - 1)]
    assert rung_dsr.judge(wins, 1, 0.0) is Answer.THIN  # LAD-09: too few trades, never a pass
    assert rung_dsr.judge([], 1, 0.0) is Answer.FAULT  # LAD-09: no trade says nothing of the rule
    with pytest.raises(ValueError, match="no spread"):
        rung_dsr.judge([Decimal(1)] * MIN_TRADES, 1, 0.0)  # LAD-09: gains with no spread refused
    # LAD-09: the deflating is never skipped: no count, or a set with no spread, is refused
    for trials, spread in ((0, 0.01), (100, 0.0), (100, math.nan), (100, -0.01), (1, math.inf)):
        with pytest.raises(ValueError, match="trials"):
            rung_dsr.judge(wins, trials, spread)
    # LAD-03: many small wins and a rare large loss pass as a bell, and are in doubt here
    lopsided = [Decimal("0.01")] * 57 + [Decimal("-0.10")] * 3
    as_a_bell = rung_dsr.deflated(rung_dsr.sharpe(lopsided), len(lopsided), 0, 3, 1, 0.0)
    assert as_a_bell >= PASS > rung_dsr.chance(lopsided, 1, 0.0) > FAIL
    assert rung_dsr.judge(lopsided, 1, 0.0) is Answer.DOUBT
    # LAD-08: the pick of a hundred trials of noise passes alone, and not against its hundred
    picked, spread = _picks(0.0)[0]
    assert rung_dsr.judge(picked, 1, 0.0) is Answer.PASS, "judged as if it were the only trial"
    assert rung_dsr.judge(picked, TRIALS, spread) is Answer.DOUBT, "at luck's best: in doubt"
    assert rung_dsr.judge(picked, 100 * TRIALS, spread) is Answer.FAIL, "under it: luck likelier"
    assert rung_dsr.judge([-g for g in picked], 1, 0.0) is Answer.FAIL  # LAD-08: a loss is a fail
