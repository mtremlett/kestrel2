"""The deflated Sharpe (rung 7, R-RUNNER-135), proven alone: the paper's own worked case, a
planted edge, pure noise at the stated rate and no more, a power curve, three broken copies,
the old audit's defects (LAD-09, LAD-03, LAD-08) kept as cases that must fail, and the lopsided
noise its rate does not cover."""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from decimal import Decimal
from functools import cache

import numpy as np
import pytest
from numpy.typing import NDArray

from lab import rung_dsr
from lab.deflated import FAIL, PASS, deflate
from lab.rung import MIN_TRADES, Answer
from lab.rung_sample import band

Judge = Callable[[Sequence[Decimal], int, float], Answer]
Pick = tuple[tuple[Decimal, ...], float]
CELLS, TRIALS, TRADES = 500, 100, 60
#: the module's "about one time in a hundred" for the pick of a hundred trials of bell noise
PICKED = 0.01
#: THE POWER CURVE, recorded: of CELLS sets of TRIALS trials, one with this true Sharpe a trade
#: planted among noise, those whose pick passes against the whole set
POWER = {0.3: 33, 0.5: 208, 0.8: 492}


def _pick(gains: NDArray[np.float64]) -> Pick:
    """A set's best trial, each row a trial's gains, and the spread of the set's Sharpes."""
    sharpes = gains.mean(axis=1) / gains.std(axis=1, ddof=1)
    return tuple(map(Decimal, gains[sharpes.argmax()].tolist())), float(sharpes.var(ddof=1))


@cache
def _picks(edge: float) -> tuple[Pick, ...]:
    """The picks of CELLS sets of TRIALS trials of TRADES bell gains, all noise but the first
    of each set, whose true Sharpe a trade is `edge`."""
    rng, picks = np.random.default_rng(round(edge * 10)), []
    for _ in range(CELLS):
        gains = rng.standard_normal((TRIALS, TRADES))
        gains[0] += edge
        picks.append(_pick(gains))
    return tuple(picks)


def _passes(judge: Judge, edge: float, trials: int = TRIALS) -> int:
    """How many of the picks pass, each judged against `trials` and its own set's spread."""
    return sum(judge(gains, trials, spread) is Answer.PASS for gains, spread in _picks(edge))


def _edge(judge: Judge) -> bool:
    """A planted edge passes: a true Sharpe of 1 a trade among a hundred trials, 499 in 500."""
    return _passes(judge, 1.0) > 0.99 * CELLS


def _noise(judge: Judge) -> bool:
    """Pure noise judged alone passes at about the stated rate, inside its exact binomial band
    (56 of 500); and its pick of a hundred, judged against the hundred, no more than about one
    time in a hundred, under that rate's band (4 of 500, where 14 are the most)."""
    rng = np.random.default_rng(7)
    alone = (tuple(map(Decimal, rng.standard_normal(TRADES).tolist())) for _ in range(CELLS))
    low, high = band(CELLS, rung_dsr.RATE)
    passed = sum(judge(gains, 1, 0.0) is Answer.PASS for gains in alone)
    return low <= passed <= high and _passes(judge, 0.0) <= band(CELLS, PICKED)[1]


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
    for trials, paper in ((100, 0.9004), (46, 0.9505)):
        bar = rung_dsr.bar(trials, 1 / 500)
        assert deflate(sharpe, bar, 1250, -3, 10) == pytest.approx(paper, abs=5e-5)
    #: by hand: 32 gains of 2% and 8 losses of 3%. Mean 1%; about it the squares average
    #: 0.0004, the cubes -0.000012, the fourth powers 0.00000052: skew -1.5, kurtosis 3.25.
    #: The deviation on 39 is 0.02 * sqrt(40 / 39), so the Sharpe is a half * sqrt(39 / 40)
    gains = [Decimal("0.02")] * 32 + [Decimal("-0.03")] * 8
    assert rung_dsr.sharpe(gains) == pytest.approx(0.5 * math.sqrt(39 / 40))
    assert rung_dsr.chance(gains, 9, 0.01) == pytest.approx(
        deflate(0.5 * math.sqrt(39 / 40), rung_dsr.bar(9, 0.01), 40, -1.5, 3.25)
    )
    assert math.isclose(rung_dsr.RATE, 0.10) and rung_dsr.bar(1, 0.0) == 0, "one trial: no bar"


@pytest.mark.parametrize("proof", [_edge, _noise, _power])
def test_the_rung_passes_each_proof(proof: Callable[[Judge], bool]) -> None:
    assert proof(rung_dsr.judge)


def test_a_broken_copy_is_caught() -> None:
    """Three plausible mistakes: the count of trials forgotten, so the pick of a hundred is
    judged as one alone; the spread left in a year's units against a Sharpe a trade; and the
    bar set by the spread itself, its root forgotten."""

    def no_count(gains: Sequence[Decimal], _trials: int, _spread: float) -> Answer:
        return rung_dsr.judge(gains, 1, 0.0)

    def yearly_spread(gains: Sequence[Decimal], trials: int, spread: float) -> Answer:
        return rung_dsr.judge(gains, trials, 250 * spread)

    def no_root(gains: Sequence[Decimal], trials: int, spread: float) -> Answer:
        return rung_dsr.judge(gains, trials, spread**2)

    assert _edge(no_count) and not _noise(no_count) and not _power(no_count)
    assert _edge(no_root) and not _noise(no_root) and not _power(no_root)
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
    as_a_bell = deflate(rung_dsr.sharpe(lopsided), 0.0, len(lopsided), 0, 3)
    assert as_a_bell >= PASS > rung_dsr.chance(lopsided, 1, 0.0) > FAIL
    assert rung_dsr.judge(lopsided, 1, 0.0) is Answer.DOUBT
    # LAD-08: the pick of a hundred trials of noise passes alone, and not against its hundred
    picked, spread = _picks(0.0)[0]
    assert rung_dsr.judge(picked, 1, 0.0) is Answer.PASS, "judged as if it were the only trial"
    assert rung_dsr.judge(picked, TRIALS, spread) is Answer.DOUBT, "a chance of 0.79: in doubt"
    assert rung_dsr.judge(picked, 100 * TRIALS, spread) is Answer.FAIL, "under it: luck likelier"
    assert rung_dsr.judge([-g for g in picked], 1, 0.0) is Answer.FAIL  # LAD-08: a loss is a fail


def test_the_rate_is_of_bell_gains_and_lopsided_noise_needs_the_first_rungs_planted_loss() -> None:
    """Noise with a mean of nothing: small wins, and one trade in twenty a loss nineteen times
    the size. As sampled, the pick of a hundred trials is nearly always one that met few losses
    or none, and it passes. With the one more loss the first rung plants (G2) among every
    trial's gains, as `Verdict.gains` holds them, none of a hundred picks passes."""
    rng, sets, passed = np.random.default_rng(1), 100, [0, 0]
    for _ in range(sets):
        lost = rng.random((TRIALS, TRADES)) < 1 / 20
        gains = np.where(lost, -0.19, rng.normal(0.01, 0.005, (TRIALS, TRADES)))
        for planted, seen in enumerate((gains, np.c_[gains, np.full(TRIALS, -0.19)])):
            best, spread = _pick(seen)
            passed[planted] += rung_dsr.judge(best, TRIALS, spread) is Answer.PASS
    assert passed[0] > 0.9 * sets, "as sampled: far over the stated rate"
    assert passed[1] == 0, "the loss that had not come yet, planted: none"
