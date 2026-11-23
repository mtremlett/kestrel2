"""The confidence-interval rung (rung 3), proven alone: a known answer from the literature, a
planted edge, pure noise at the stated rate, a power curve, broken copies, and the old audit's
defects (LAD-09, LAD-03, LAD-08) kept as cases that must fail."""

from __future__ import annotations

import math
import random
from collections.abc import Callable, Sequence
from decimal import Decimal

import pytest

from lab import rung, rung_ci
from lab.rung import MIN_TRADES, Answer

Judge = Callable[[Sequence[Decimal]], Answer]
CELLS, TRADES = 500, 200
#: the chance a mean sits two standard errors above nothing by luck alone: 1 - Phi(2)
STATED = 1 - 0.5 * (1 + math.erf(2 / math.sqrt(2)))


def _cell(rng: random.Random, edge: float, n: int = TRADES) -> list[Decimal]:
    """n trade gains of unit spread whose true mean is `edge` spreads."""
    return [Decimal(str(round(rng.gauss(edge, 1), 6))) for _ in range(n)]


def _binomial_range(n: int, p: float, tail: float = 0.001) -> tuple[int, int]:
    """The counts out of n that a rate p gives all but `tail` of the time on either side."""
    cdf, low, high = 0.0, 0, n
    for k in range(n + 1):
        cdf += math.comb(n, k) * p**k * (1 - p) ** (n - k)
        if cdf < tail:
            low = k + 1
        if cdf >= 1 - tail:
            high = k
            break
    return low, high


def _passes(judge: Judge, edge: float, seed: int) -> int:
    """How many of CELLS cells with this true edge the rung passes."""
    rng = random.Random(seed)  # noqa: S311 - a repeatable test draw, not a secret
    return sum(judge(_cell(rng, edge)) is Answer.PASS for _ in range(CELLS))


def _sound(judge: Judge) -> bool:
    """A rung is sound if it passes a planted edge and passes noise at about the stated rate."""
    low, high = _binomial_range(CELLS, STATED)
    return _passes(judge, 0.5, 1) > 0.95 * CELLS and low <= _passes(judge, 0.0, 2) <= high


def test_known_answer_from_the_textbook() -> None:
    """Wasserman, All of Statistics, section 6.3.2: the mean plus and minus z times s over root n.
    Gains 1..5: mean 3, s squared 2.5, standard error sqrt(0.5); two errors give 1.5858, 4.4142."""
    _, low, high = rung.interval([Decimal(g) for g in range(1, 6)])
    assert (round(low, 4), round(high, 4)) == (Decimal("1.5858"), Decimal("4.4142"))


def test_a_planted_edge_passes_and_noise_passes_at_the_stated_rate_only() -> None:
    assert _sound(rung_ci.judge)


def test_power_at_three_effect_sizes() -> None:
    """With 200 trades an edge of 0.1 spreads is rarely found, 0.2 half the time, 0.4 always."""
    small, mid, large = (_passes(rung_ci.judge, e, 3) / CELLS for e in (0.1, 0.2, 0.4))
    assert small < 0.45 < 0.5 < mid < 0.95 < large
    assert large > 0.99


def test_a_broken_copy_is_caught() -> None:
    """Two plausible mistakes fail the same proof: forgetting the root of n, and a sign test."""

    def no_root_n(gains: Sequence[Decimal]) -> Answer:
        mean = sum(gains, Decimal(0)) / len(gains)
        sd = (sum(((g - mean) ** 2 for g in gains), Decimal(0)) / (len(gains) - 1)).sqrt()
        return Answer.PASS if mean - 2 * sd > 0 else Answer.DOUBT

    def sign_only(gains: Sequence[Decimal]) -> Answer:
        return Answer.PASS if sum(gains, Decimal(0)) > 0 else Answer.DOUBT

    assert not _sound(no_root_n)
    assert not _sound(sign_only)


def test_the_old_audits_defects_must_fail() -> None:
    wins = [Decimal(1) + Decimal(n) / 100 for n in range(MIN_TRADES - 1)]
    assert rung_ci.judge(wins) is Answer.THIN  # LAD-09: too few trades is thin, never a pass
    assert rung_ci.judge([]) is Answer.FAULT  # LAD-09: no trade at all says nothing of the rule
    with pytest.raises(ValueError, match="no spread"):
        rung_ci.judge([Decimal(1)] * MIN_TRADES)  # LAD-09: gains with no spread are refused
    rare_loss = [Decimal("0.01")] * 59 + [Decimal(-1)]
    assert rung_ci.judge(rare_loss) is Answer.DOUBT  # LAD-03: one large loss widens the interval
    assert rung_ci.judge([-g for g in wins * 2]) is Answer.FAIL  # LAD-08: a loss is a fail
    # LAD-08: an interval holding nothing is never a pass or a fail
    assert rung_ci.judge([Decimal(g % 3 - 1) for g in range(90)]) is Answer.DOUBT
