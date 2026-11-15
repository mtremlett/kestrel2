"""The ladder's eighth rung proven alone (R-RUNNER-119): a planted edge passes it, five hundred
cells of noise pass at its stated rate, its power is recorded at three sizes of edge, and a copy
of it with its decision inverted is caught by each of those three."""

from __future__ import annotations

import random
from collections.abc import Callable, Sequence
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal
from fractions import Fraction
from functools import cache
from math import comb, sqrt

import pytest
from test_lab_rung import FREE, VUSA

from lab import cell, rung, rung_cpcv, tape
from lab.cell import Cell, Key, Trade
from lab.rung import Answer, Priced, Verdict
from lab.rung_cpcv import Crossed

Rung = Callable[[Verdict], Crossed]
Days = tuple[int, int, float]  #: a trade: the day it was bought, the day sold, its gain
START = date(2001, 1, 1)
CELLS, TRADES = 500, 60  #: the cells of noise asked for, each five years of a trade a month
EDGE = [0.02, 0.02, -0.01] * 20  #: planted: two wins to a smaller loss, the whole way through
#: THE POWER CURVE, recorded: of 200 cells whose true edge stands this many standard errors
#: above nothing over their 60 trades, how many pass (noise, at none, passes 1 in 32)
POWER = {1: 22, 2: 77, 4: 187}


def _tape(trades: Sequence[Days], name: str = "a") -> Verdict:
    """A tape priced: the first rung's verdict on these trades, free of costs."""
    priced = tuple(
        Priced(Trade(day, day), 1, Decimal(1), 1 + Decimal(f"{gain:.6f}"), FREE, (day, sold))
        for day, sold, gain in (
            (START + timedelta(b), START + timedelta(s), g) for b, s, g in trades
        )
    )
    window = Cell("breakout_20_10", VUSA, START, START + timedelta(days=36500))
    return rung.verdict(Key(window, "code", name), priced)


def _monthly(gains: Sequence[float]) -> list[Days]:
    """A trade bought every thirty days and sold ten later, with these gains."""
    return [(30 * n, 30 * n + 10, gain) for n, gain in enumerate(gains)]


@cache
def _cells(errors: int, cells: int) -> tuple[Verdict, ...]:
    """Cells of noise about a true edge of so many standard errors over a cell's trades, the
    draw named by the request and the edge."""
    rng = random.Random(f"R-RUNNER-119 {errors}")  # noqa: S311 - a repeatable draw, not a secret
    edge = errors / sqrt(TRADES)
    return tuple(
        _tape(_monthly([rng.gauss(edge, 1) / 50 for _ in range(TRADES)])) for _ in range(cells)
    )


def _passes(judge: Rung, errors: int, cells: int = 200) -> int:
    return sum(judge(one).passed for one in _cells(errors, cells))


def _interval(n: int, p: float, tail: float = 0.025) -> tuple[int, int]:
    """The central 95% of a binomial count: the fewest and the most successes of n at rate p."""
    below, cuts = 0.0, []
    for k in range(n + 1):
        below += comb(n, k) * p**k * (1 - p) ** (n - k)
        cuts.append(below)
    return (
        next(k for k, c in enumerate(cuts) if c > tail),
        next(k for k, c in enumerate(cuts) if c >= 1 - tail),
    )


def planted(judge: Rung) -> None:
    """A planted edge passes, and the same edge planted the wrong way up fails."""
    assert judge(_tape(_monthly(EDGE))).passed
    assert judge(_tape(_monthly([-gain for gain in EDGE]))).answer is Answer.FAIL


def noise(judge: Rung) -> None:
    """Five hundred cells of pure noise pass at the stated rate, 1 in 32: 8 to 24 of them."""
    low, high = _interval(CELLS, float(rung_cpcv.RATE))
    assert (rung_cpcv.RATE, low, high) == (Fraction(1, 32), 8, 24)
    assert low <= _passes(judge, 0, CELLS) <= high


def power(judge: Rung) -> None:
    """The curve is the one recorded, and rises with the edge from the noise's own count."""
    curve = [_passes(judge, errors) for errors in POWER]
    assert curve == list(POWER.values())
    assert sorted({_passes(judge, 0), *curve}) == [_passes(judge, 0), *curve]


PROOFS = (planted, noise, power)


@pytest.mark.parametrize("proof", PROOFS)
def test_the_rung_is_proven_alone(proof: Callable[[Rung], None]) -> None:
    proof(rung_cpcv.cross)


@pytest.mark.parametrize("proof", PROOFS)
def test_a_copy_with_its_decision_inverted_is_caught(proof: Callable[[Rung], None]) -> None:
    inverted = {Answer.PASS: Answer.FAIL, Answer.FAIL: Answer.PASS}

    def broken(verdict: Verdict) -> Crossed:
        got = rung_cpcv.cross(verdict)
        return replace(got, answer=inverted.get(got.answer, got.answer))

    with pytest.raises(AssertionError):
        proof(broken)


def test_a_trade_across_a_cut_or_in_its_embargo_is_in_no_stretch() -> None:
    #: 600 days: cuts on days 100 to 500, an embargo of 6 days after each. The trades bought on
    #: a cut are in its embargo, the one sold on day 200 is held across that cut: six purged,
    #: each a loss that would sink its stretch, and the 55 left earn in every stretch
    grid = [(10 * n, 10 * n + 4, 0.01 + n % 2 / 100) for n in range(60)] + [(596, 600, 0.01)]
    purged = {100, 190, 200, 300, 400, 500}
    got = rung_cpcv.cross(
        _tape([(b, 200 if b == 190 else s, -0.5 if b in purged else g) for b, s, g in grid])
    )
    assert (got.trades, got.purged, got.answer) == (55, 6, Answer.PASS)
    assert (len(got.splits), got.chosen, got.lost, got.overfit) == (15, 15, 0, Fraction(0))


def test_gains_all_made_in_one_lucky_stretch_pass_the_first_rung_and_fail_this_one() -> None:
    lucky = _tape(_monthly([-0.01 - n % 2 / 100 for n in range(100)] + [0.2, 0.3] * 10))
    got = rung_cpcv.cross(lucky)
    assert lucky.passed, "the first rung sees only the total"
    #: chosen wherever the lucky stretch is in-sample (10 splits), and lost in every one
    assert (got.answer, got.chosen, got.lost, got.overfit) == (Answer.FAIL, 10, 10, Fraction(1))
    assert "chosen in-sample in 10, lost out-of-sample in 10 of those" in got.reason
    one_poor = [0.02, 0.01] * 50 + [-0.01, 0.004] * 10
    assert rung_cpcv.cross(_tape(_monthly(one_poor))).passed, "one poor stretch is no fail"


def test_it_fails_fairly_too_few_trades_or_an_empty_stretch_is_thin_and_none_a_fault() -> None:
    assert rung_cpcv.cross(_tape([])).answer is Answer.FAULT
    few = rung_cpcv.cross(_tape(_monthly(EDGE[:29])))
    assert (few.answer, few.splits, few.overfit) == (Answer.THIN, (), None)
    gap = _monthly(EDGE[:20]) + [(b + 9000, s + 9000, g) for b, s, g in _monthly(EDGE[:20])]
    idle = rung_cpcv.cross(_tape(gap))
    assert idle.answer is Answer.THIN and "a trade in every stretch" in idle.reason


def test_the_result_is_keyed_by_the_tape_and_this_rungs_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    one = _tape(_monthly(EDGE))
    key = rung_cpcv.cross(one).key
    assert rung_cpcv.cross(one).key == key
    assert rung_cpcv.cross(_tape(_monthly(EDGE), name="other bars")).key != key
    monkeypatch.setitem(cell.RUNGS, rung_cpcv.ME, "this rung edited")
    edited = rung_cpcv.cross(one).key
    monkeypatch.setattr(tape, "rule_code", lambda _: "the rule edited")
    assert len({key, edited, rung_cpcv.cross(one).key}) == 3
