"""The walk-forward folds rung (rung 10), proven alone: a known answer from the literature, a
planted edge, pure noise at the stated rate, a power curve, broken copies, and the old audit's
defects (LAD-09, LAD-03, LAD-08) kept as cases that must fail."""

from __future__ import annotations

import math
import random
from collections.abc import Callable, Sequence
from datetime import date, timedelta
from decimal import Decimal

import pytest

from lab import rung_folds
from lab.rung import MIN_TRADES, Answer
from lab.rung_folds import Gain, Walked

Decide = Callable[[Walked], bool]
START, FOLDS, CELLS, EACH = date(2020, 1, 1), 2, 500, 100
END = START + timedelta(days=(FOLDS + 1) * 2 * EACH - 1)
#: the chance one fold's mean sits two standard errors above nothing by luck: 1 - Phi(2); a rung
#: that needs every fold to is stated at that to the power of the folds
TAIL = 1 - 0.5 * (1 + math.erf(2 / math.sqrt(2)))
STATED = TAIL**FOLDS


def _trades(rng: random.Random, edge: Sequence[float]) -> list[Gain]:
    """EACH trades in each part, a day long and a day apart, of unit spread; part n has a true
    mean of edge[n] spreads."""
    return [
        (
            day := START + timedelta(days=2 * i),
            day,
            Decimal(str(round(rng.gauss(edge[i // EACH], 1), 6))),
        )
        for i in range(len(edge) * EACH)
    ]


def _walk(edge: Sequence[float], seed: int) -> Walked:
    return rung_folds.judge(_trades(random.Random(seed), edge), START, END, FOLDS)  # noqa: S311


def _within(passed: int, rate: float) -> bool:
    """Whether `passed` of CELLS lies in the central 99.8% of the binomial at `rate`."""
    chance = [math.comb(CELLS, k) * rate**k * (1 - rate) ** (CELLS - k) for k in range(passed + 1)]
    return sum(chance) > 0.001 and sum(chance[:-1]) < 0.999


def _passes(decide: Decide, edge: float, seed: int) -> int:
    return sum(decide(_walk([edge] * 3, seed * CELLS + n)) for n in range(CELLS))


def _sound(decide: Decide) -> bool:
    """Passes a planted edge, and passes noise at about the stated rate and no more."""
    return _passes(decide, 0.5, 1) > 0.95 * CELLS and _within(_passes(decide, 0.0, 2), STATED)


def _day(n: int) -> date:
    return START + timedelta(days=n)


def test_known_answer_from_the_literature() -> None:
    """Pardo (2008), walk-forward analysis: test windows follow the in-sample window in time;
    Wasserman, All of Statistics, 6.3.2: gains 1..5 are 3 over sqrt(0.5) = 4.2426 standard errors.
    A 12-day window cut in 3 parts of 4 days: the second part is the first fold's, the third the
    second's, and the first fold's in-sample is the first part alone."""
    assert rung_folds.stretch([Decimal(g) for g in range(1, 6)]).t == pytest.approx(
        Decimal("4.2426"), abs=Decimal("0.0001")
    )
    made = rung_folds.judge(
        [
            (_day(0), _day(1), Decimal(1)),
            (_day(4), _day(5), Decimal(2)),
            (_day(8), _day(9), Decimal(3)),
        ]
        + [(_day(2), _day(3), Decimal(-1)), (_day(3), _day(5), Decimal(7))],
        START,
        _day(11),
        2,
    )
    first, second = made.folds
    assert (first.inside.trades, first.outside.trades) == (2, 1), "the day 3-5 trade crosses a cut"
    assert (second.inside.trades, second.outside.trades) == (4, 1), "whole before the later cut"


def test_a_planted_edge_passes_and_noise_passes_at_the_stated_rate_only() -> None:
    assert _sound(lambda w: w.passed)


def test_power_at_three_effect_sizes() -> None:
    """With 100 trades a fold, 0.1 spreads is rarely found, 0.25 about half the time, 0.4 always."""
    small, mid, large = (_passes(lambda w: w.passed, e, 3) / CELLS for e in (0.1, 0.25, 0.4))
    assert small < 0.1 < 0.3 < mid < 0.7 < 0.9 < large


def test_a_broken_copy_is_caught() -> None:
    """Three plausible mistakes fail the same proof: judging on the best fold, on the folds
    pooled, and on the in-sample part."""

    def best(w: Walked) -> bool:
        return any(f.outside.answer is Answer.PASS for f in w.folds)

    def inside(w: Walked) -> bool:
        return all(f.inside.answer is Answer.PASS for f in w.folds)

    def pooled(w: Walked) -> bool:
        return bool(sum(float(f.outside.t or 0) for f in w.folds) / FOLDS**0.5 >= 2)

    assert not _sound(best)
    assert not _sound(inside)
    assert not _sound(pooled)


def test_the_old_audits_defects_must_fail() -> None:
    rng = random.Random(7)  # noqa: S311
    edge = _trades(rng, [0.6] * 3)
    held = [t for t in edge if t[0] < START + timedelta(days=2 * EACH)]  #: the first part only
    assert rung_folds.judge(held, START, END, FOLDS).answer is Answer.FAULT  # LAD-09: no trade
    assert rung_folds.stretch([]).answer is Answer.FAULT
    few = rung_folds.judge(edge[: EACH + MIN_TRADES - 1] + edge[2 * EACH :], START, END, FOLDS)
    assert few.worst.outside.answer is Answer.THIN  # LAD-03: too few trades is thin, never a pass
    assert not few.passed
    with pytest.raises(ValueError, match="no spread"):
        rung_folds.stretch([Decimal(1)] * MIN_TRADES)  # LAD-09: gains with no spread are refused
    with pytest.raises(ValueError, match="cannot be cut"):
        rung_folds.judge(edge, START, START + timedelta(days=1), FOLDS)
    bad = _walk([0.6, 0.6, -0.6], 11)
    assert bad.answer is Answer.FAIL and bad.worst is bad.folds[1]  # LAD-08: one bad fold fails
    assert _walk([0.6, 0.6, 0.0], 12).answer is not Answer.PASS  # the worst fold decides
