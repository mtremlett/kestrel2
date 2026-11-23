"""The ladder's eighth rung proven alone (R-RUNNER-119): a planted edge passes it, five hundred
cells of noise pass at its stated rate, its power is recorded at three sizes of edge, and a copy
of it with its decision inverted is caught by each of those three."""

from __future__ import annotations

import random
from bisect import bisect_left, bisect_right
from collections.abc import Callable, Sequence
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal
from fractions import Fraction
from functools import cache
from itertools import accumulate
from math import comb, sqrt

import pytest
from test_lab_rung import FREE, VUSA

from lab import cell, rung, rung_cpcv
from lab.cell import Cell, Key, Trade
from lab.rung import Answer, Priced, Verdict
from lab.rung_cpcv import Crossed

Rung = Callable[[Verdict], Crossed]
Days = tuple[int, int, float]  #: a trade: the day it was bought, the day sold, its gain
START = date(2001, 1, 1)
CELLS, TRADES = 500, 60  #: the cells asked for, each five years of a trade a month, 4 purged
EDGE = [0.02, 0.02, -0.01] * 20  #: planted: two wins to a smaller loss, the whole way through
#: THE POWER CURVE, recorded: of 500 cells whose true edge stands this many standard errors
#: above nothing over their 60 trades, how many pass. One draw, give or take 11; of 20,000
#: drawn outside the repository 14%, 39% and 88% pass (the first rung: 17%, 51% and 98%)
POWER = {1: 60, 2: 194, 4: 438}
#: THE RATE EXCEEDED, recorded: of 500 cells with no edge and 36 trades, nine small wins to
#: each loss nine times the size, how many pass; of even noise, 8 to 24 do
LOPSIDED = 47


def _tape(trades: Sequence[Days], name: str = "a") -> Verdict:
    """A tape priced: the first rung's verdict on these trades, free of costs."""
    at = [(START + timedelta(b), START + timedelta(s), Decimal(f"{g:.6f}")) for b, s, g in trades]
    priced = tuple(Priced(Trade(b, s), 1, Decimal(1), 1 + g, FREE, (b, s), None) for b, s, g in at)
    window = Cell("breakout_20_10", VUSA, START, START + timedelta(days=36500))
    return rung.verdict(Key(window, "code", name), priced)


def _monthly(gains: Sequence[float]) -> list[Days]:
    """A trade bought every thirty days and sold ten later, with these gains."""
    return [(30 * n, 30 * n + 10, gain) for n, gain in enumerate(gains)]


def _even(*sums: int) -> list[Days]:
    """Thirty trades in 600 days, five well inside each of the six stretches (cuts on days 100
    to 500, an embargo of 6 days, none purged), a stretch's gains summing to 5% times its sum."""
    days = [(100 * k + 20 * i + 10, 100 * k + 20 * i + 12) for k in range(6) for i in range(5)]
    days[0], days[-1] = (0, 2), (598, 600)
    return [(b, s, (sums[n // 5] + n % 5 - 2) / 100) for n, (b, s) in enumerate(days)]


@cache
def _cells(errors: int) -> tuple[Verdict, ...]:
    """Five hundred cells of noise about a true edge of so many standard errors over a cell's
    trades, the draw named by the request and the edge."""
    rng = random.Random(f"R-RUNNER-119 {errors}")  # noqa: S311 - a repeatable draw, not a secret
    edge = errors / sqrt(TRADES)
    return tuple(
        _tape(_monthly([rng.gauss(edge, 1) / 50 for _ in range(TRADES)])) for _ in range(CELLS)
    )


def _passes(judge: Rung, errors: int) -> int:
    return sum(judge(one).passed for one in _cells(errors))


def _interval(n: int, p: float, tail: float = 0.025) -> tuple[int, int]:
    """The central 95% of a binomial count: the fewest and the most successes of n at rate p."""
    below = list(accumulate(comb(n, k) * p**k * (1 - p) ** (n - k) for k in range(n + 1)))
    return bisect_right(below, tail), bisect_left(below, 1 - tail)


def planted(judge: Rung) -> None:
    """A planted edge passes, and the same edge planted the wrong way up fails."""
    assert judge(_tape(_monthly(EDGE))).passed
    assert judge(_tape(_monthly([-gain for gain in EDGE]))).answer is Answer.FAIL


def noise(judge: Rung) -> None:
    """Five hundred cells of pure noise pass at the stated rate, 1 in 32: 8 to 24 of them."""
    low, high = _interval(CELLS, float(rung_cpcv.RATE))
    assert (rung_cpcv.RATE, low, high) == (Fraction(1, 32), 8, 24)
    assert low <= _passes(judge, 0) <= high


def power(judge: Rung) -> None:
    """The curve is the one recorded, and rises with the edge from the noise's own count."""
    curve = [_passes(judge, errors) for errors in POWER]
    assert curve == list(POWER.values())
    assert sorted({_passes(judge, 0), *curve}) == [_passes(judge, 0), *curve]


PROOFS = (planted, noise, power)


@pytest.mark.parametrize("proof", PROOFS)
def test_the_rung_is_proven_alone(proof: Callable[[Rung], None]) -> None:
    proof(rung_cpcv.judge)


@pytest.mark.parametrize("proof", PROOFS)
def test_a_copy_with_its_decision_inverted_is_caught(proof: Callable[[Rung], None]) -> None:
    inverted = {Answer.PASS: Answer.FAIL, Answer.FAIL: Answer.PASS}

    def broken(verdict: Verdict) -> Crossed:
        got = rung_cpcv.judge(verdict)
        return replace(got, answer=inverted.get(got.answer, got.answer))

    with pytest.raises(AssertionError):
        proof(broken)


def test_no_edge_in_many_small_wins_passes_more_often_than_stated_and_it_is_recorded() -> None:
    rng = random.Random("R-RUNNER-119 lopsided")  # noqa: S311 - a repeatable draw, not a secret

    def gains() -> list[float]:
        return [rng.uniform(0.005, 0.015) if rng.random() < 0.9 else -0.09 for _ in range(36)]

    passes = sum(rung_cpcv.judge(_tape(_monthly(gains()))).passed for _ in range(CELLS))
    assert _interval(CELLS, float(rung_cpcv.RATE))[1] < passes == LOPSIDED


def test_each_split_is_counted_as_it_is_known_to_fall() -> None:
    def crossed(*sums: int) -> tuple[Answer, int, int, Fraction | None]:
        got = rung_cpcv.judge(_tape(_even(*sums)[::-1]))  #: newest first: the order is not read
        return got.answer, got.chosen, got.lost, got.overfit

    #: thirty trades are enough, and a poor stretch losing less than the next worst earns passes
    assert crossed(3, 3, 3, 3, 3, -1) == (Answer.PASS, 15, 0, Fraction(0))
    #: the two worst earn exactly nothing together: chosen in every split, lost on that pair
    assert crossed(2, 2, 2, 2, 1, -1) == (Answer.FAIL, 15, 1, Fraction(1, 15))
    #: exactly nothing in-sample is not chosen: chosen only with the bad stretch out, lost there
    assert crossed(1, 1, 1, 1, 1, -3) == (Answer.FAIL, 5, 5, Fraction(1))
    assert crossed(-1, -1, -1, -1, -1, -1) == (Answer.FAIL, 0, 0, None), "never chosen"
    #: every gain made in one stretch: the first rung passes the total, and this rung fails it
    lucky = _tape(_even(-1, -1, -1, -1, -1, 100))
    assert lucky.passed and crossed(-1, -1, -1, -1, -1, 100) == (Answer.FAIL, 10, 10, Fraction(1))
    said = rung_cpcv.judge(lucky).reason
    assert "chosen in-sample in 10, lost out-of-sample in 10 of those" in said


def test_a_trade_across_a_cut_or_in_its_embargo_is_in_no_stretch() -> None:
    #: a loss held across the cut on day 100, and one bought on it: either would sink a stretch
    sunk = [(94, 100, -0.9), (100, 102, -0.9)]
    got = rung_cpcv.judge(_tape(_even(3, 3, 3, 3, 3, 3) + sunk))
    assert (got.trades, got.purged, got.answer, len(got.splits)) == (30, 2, Answer.PASS, 15)


def test_it_fails_fairly_too_few_trades_or_an_empty_stretch_is_thin_and_none_a_fault() -> None:
    assert rung_cpcv.judge(_tape([])).answer is Answer.FAULT
    few = rung_cpcv.judge(_tape(_monthly(EDGE[:29])))
    assert (few.answer, few.splits, few.overfit) == (Answer.THIN, (), None)
    #: thirty judged, one bought on the embargo's last day: twenty-nine are left, too few
    short = _even(3, 3, 3, 3, 3, 3)
    short[5] = (105, 107, 0.01)
    cut = rung_cpcv.judge(_tape(short))
    assert (cut.answer, cut.trades, cut.purged) == (Answer.THIN, 29, 1)
    short[5] = (106, 108, 0.01)
    assert rung_cpcv.judge(_tape(short)).purged == 0, "the day after the embargo is the stretch's"
    gap = _monthly(EDGE[:20]) + [(b + 9000, s + 9000, g) for b, s, g in _monthly(EDGE[:20])]
    idle = rung_cpcv.judge(_tape(gap))
    assert (idle.answer, idle.trades) == (Answer.THIN, 40), "forty trades, and four stretches idle"
    assert "a trade in every stretch" in idle.reason


def test_the_result_is_keyed_by_the_tape_and_this_rungs_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    one = _tape(_monthly(EDGE))
    key = rung_cpcv.judge(one).key
    assert key == one.key.rung(rung_cpcv.ME) != one.key
    monkeypatch.setitem(cell.RUNGS, rung_cpcv.ME, "this rung edited")
    assert rung_cpcv.judge(one).key not in (key, one.key), "the rung edited: a new key"
