"""The benchmark rung, proven alone: a planted edge passes, noise passes at about the stated
rate, power grows with the edge, and a rung with its decision inverted is caught."""

from __future__ import annotations

import math
import random

import pytest
from test_lab_rung import POUND, SHAPE, _bars, _judge, _walk

from desk.lines import YARDSTICK
from lab import rung_benchmark as rb
from lab.rung import Answer

CELL, STATED = 200, 0.5 * math.erfc(2 / math.sqrt(2))  #: trades to a cell; P(z >= 2)


def _rate(edge: float, cells: int, seed: int = 7) -> float:
    """The share of cells passed, each CELL trades of unit spread whose true mean is `edge`."""
    rng = random.Random(seed)  # noqa: S311 - a repeatable test draw, not a secret
    draws = ([rng.gauss(edge, 1) for _ in range(CELL)] for _ in range(cells))
    return sum(rb.beats(rb.interval(d)[1]) for d in draws) / cells


def _answer(seed: int, edge: float, bench: float = 0) -> rb.Excess:
    return rb.judge(_judge(_walk(seed, edge), -1), YARDSTICK, _walk(seed + 50, bench), POUND)


def test_a_planted_edge_passes_and_the_result_is_keyed_by_the_tape_and_this_code() -> None:
    for seed in (1, 2, 3):
        found = _answer(seed, 0.008)
        assert found.answer is Answer.PASS and found.low and found.low > 0, seed
        assert found.key == _judge(_walk(seed, 0.008), -1).key.rung(rb.ME) and found.n >= 30
        assert (found.mean or 0) > 0.02 and found.broker
        assert _answer(seed, 0).answer is Answer.FAIL, "no edge, no pass"
    #: a rider of its benchmark made what holding it made: nothing of its own
    up = _walk(1, 0.008)
    assert rb.judge(_judge(up, -1), YARDSTICK, up, POUND).answer is Answer.FAIL


def test_too_few_trades_or_none_are_the_first_rungs_answer_and_a_lost_day_is_refused() -> None:
    few = rb.judge(_judge(_walk(1, 0)[:1500], -1), YARDSTICK, _walk(51, 0), POUND)
    assert (few.answer, few.n, few.low) == (Answer.THIN, 0, None)
    none = rb.judge(_judge(_bars(SHAPE), 23), YARDSTICK, _walk(51, 0), POUND)
    assert none.answer is Answer.FAULT
    with pytest.raises(ValueError, match="no bar on"):
        rb.judge(_judge(_walk(1, 0.008), -1), YARDSTICK, _walk(51, 0)[:100], POUND)
    with pytest.raises(ValueError, match="no spread"):
        rb.interval([0.1] * 5)


def test_noise_passes_at_about_the_stated_rate_and_power_grows_with_the_edge() -> None:
    cells, seen = 500, _rate(0, 500)
    #: the exact binomial interval around the stated rate that holds 99.8% of the draws
    pmf = [math.comb(cells, k) * STATED**k * (1 - STATED) ** (cells - k) for k in range(cells + 1)]
    inside = [k for k in range(cells + 1) if 0.001 <= sum(pmf[: k + 1]) <= 0.999]
    assert inside[0] <= seen * cells <= inside[-1], (seen, STATED)
    power = {edge: _rate(edge, 200) for edge in (0.1, 0.2, 0.3)}  #: recorded: edge, in spreads
    assert power[0.1] < power[0.2] < power[0.3] and power[0.3] > 0.95, power
    assert power[0.1] > 0.1, "even a faint edge passes more often than noise does"


def test_a_rung_with_its_decision_inverted_is_caught(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rb, "beats", lambda low: not low > 0)
    assert _answer(1, 0.008).answer is Answer.FAIL, "the planted edge no longer passes"
    assert _rate(0, 100) > 0.9, "noise passes almost always: far above the stated rate"
