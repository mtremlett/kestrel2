"""The beta rung, proven alone: a textbook known answer, a planted edge, pure noise at the stated
rate, a power curve, broken copies, and the old audit's defects (LAD-09, LAD-03, LAD-08)."""

from __future__ import annotations

import math
import random
from collections.abc import Callable, Sequence

import pytest
from test_lab_rung_ci import CELLS, TRADES, _binomial_range

from lab import market
from lab.rung import MIN_TRADES, Answer

Judge = Callable[[Sequence[float], Sequence[float]], Answer]
#: the chance an intercept sits two standard errors above nothing by luck: Student's t, 198 d.f.
STATED = 0.0235


def _cell(rng: random.Random, edge: float, n: int = TRADES) -> tuple[list[float], list[float]]:
    """n days of a benchmark drifting up 0.2 a day, and of a strategy carrying half its moves
    and earning `edge` a day of its own, noise of unit spread on each."""
    bench = [rng.gauss(0.2, 1) for _ in range(n)]
    return [0.5 * b + edge + rng.gauss(0, 1) for b in bench], bench


def _passes(judge: Judge, edge: float, seed: int) -> int:
    """How many of CELLS cells with this true edge the rung passes."""
    rng = random.Random(seed)  # noqa: S311 - a repeatable test draw, not a secret
    return sum(judge(*_cell(rng, edge)) is Answer.PASS for _ in range(CELLS))


def _sound(judge: Judge) -> bool:
    """A rung is sound if it passes a planted edge and passes noise at about the stated rate."""
    low, high = _binomial_range(CELLS, STATED)
    return _passes(judge, 0.5, 1) > 0.95 * CELLS and low <= _passes(judge, 0.0, 2) <= high


def test_known_answer_from_the_textbook() -> None:
    """Weisberg, Applied Linear Regression, 2.3, and Wasserman, All of Statistics, 13.3: for x of
    1..5 and y of 2, 4, 5, 4, 5 the line is 2.2 + 0.6x, the residual variance 0.8, and the
    intercept's standard error sqrt(0.8 * (1/5 + 3**2/10)) = sqrt(0.88), so t is 2.2 / that."""
    found = market.fit([2.0, 4.0, 5.0, 4.0, 5.0], [1.0, 2.0, 3.0, 4.0, 5.0])
    assert (round(found.beta, 9), round(found.excess, 9)) == (0.6, 2.2)
    assert math.isclose(found.t, 2.2 / math.sqrt(0.88))


def test_a_planted_edge_passes_and_noise_passes_at_the_stated_rate_only() -> None:
    assert _sound(market.banded)


def test_power_at_three_effect_sizes() -> None:
    """With 200 days an edge of 0.1 is rarely found, 0.2 mostly, 0.4 always."""
    small, mid, large = (_passes(market.banded, e, 3) / CELLS for e in (0.1, 0.2, 0.4))
    assert small < 0.45 < 0.6 < mid < 0.95 < large
    assert large > 0.99


def test_a_broken_copy_is_caught() -> None:
    """Three plausible mistakes fail the same proof: no beta taken out, a beta of one assumed,
    and a sign test."""

    def raw_mean(own: Sequence[float], _bench: Sequence[float]) -> Answer:
        return market.banded(own, [(-1) ** n * (1 + n % 2 / 2) for n in range(len(own))])

    def beta_of_one(own: Sequence[float], bench: Sequence[float]) -> Answer:
        return raw_mean([o - b for o, b in zip(own, bench, strict=True)], bench)

    def sign_only(own: Sequence[float], bench: Sequence[float]) -> Answer:
        return Answer.PASS if market.fit(own, bench).excess > 0 else Answer.DOUBT

    assert not any(_sound(copy) for copy in (raw_mean, beta_of_one, sign_only))


def test_the_old_audits_defects_must_fail() -> None:
    rng = random.Random(7)  # noqa: S311 - a repeatable test draw, not a secret
    few = _cell(rng, 0.5, MIN_TRADES - 1)
    assert market.banded(*few) is Answer.THIN  # LAD-09: too few days is thin, never a pass
    assert market.banded([], []) is Answer.FAULT  # LAD-09: no day at all says nothing
    with pytest.raises(ValueError, match="no spread"):
        bench = [float(n % 3) for n in range(MIN_TRADES)]
        market.banded([2 * b for b in bench], bench)  # LAD-09: days with no spread are refused
    with pytest.raises(ValueError, match="never moved"):
        market.banded(few[0] * 2, [1.0] * len(few[0]) * 2)  # a benchmark that never moved
    own, bench = _cell(rng, 0.1, 60)
    own[7] -= 20  # LAD-03: one large loss widens the interval; the edge is not then a pass
    assert market.banded(own, bench) is Answer.DOUBT
    assert market.banded(*_cell(rng, -0.5)) is Answer.FAIL  # LAD-08: a loss is a fail
    # LAD-08: an interval holding nothing is never a pass or a fail
    assert market.banded(*_cell(random.Random(5), 0.0)) is Answer.DOUBT  # noqa: S311
