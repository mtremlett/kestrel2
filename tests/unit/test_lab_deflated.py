"""The luck test fixed before any result: the deflated Sharpe and its bands, the yearly
Sharpe too good to be true, and the one rule that reads every named rung."""

from __future__ import annotations

import math
import random
from collections.abc import Callable, Sequence
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal, localcontext
from functools import cache

import numpy as np
import pytest
from numpy.typing import NDArray
from test_lab_rung import FREE

from desk.lines import LINES, Line
from desk.strategy import ARITHMETIC
from lab import deflated, luck, rung, trials, verdict
from lab.cell import Cell, Key, Trade
from lab.rung import Answer, Priced, Verdict
from lab.rung_sample import band

VUSA, AAPL, NVDA = (next(n for n in LINES if n.symbol == s) for s in ("VUSA", "AAPL", "NVDA"))

DAY = date(2010, 1, 1)


def _verdict(
    gains: list[float], years: float = 10, name: str = "a", line: Line = VUSA, every: int = 0
) -> Verdict:
    """A trial with these gains, one per trade sold `every` days apart, over a window of so
    many years, judged by the first rung's own rule."""
    back = [Decimal(f"{100 * (1 + gain):.4f}") for gain in gains]
    days = [DAY + timedelta(days=every * n) for n in range(len(back))]
    priced = tuple(
        Priced(Trade(d, d), 1, Decimal(100), b, FREE, (d, d), None)
        for b, d in zip(back, days, strict=True)
    )
    window = Cell("breakout_20_10", line, DAY, DAY + timedelta(days=round(365.25 * years)))
    return rung.verdict(Key(window, "code", name), priced)


def _bell(seed: int, edge: float, trades: int = 40) -> Verdict:
    rng = random.Random(seed)  # noqa: S311 - a repeatable test draw, not a secret
    return _verdict([rng.gauss(edge, 0.02) for _ in range(trades)], name=str(seed))


def test_the_deflated_sharpe_is_the_published_one() -> None:
    #: Bailey and Lopez de Prado's own worked case: the best of 100 trials, a yearly Sharpe
    #: of 2.5 on 1,250 days, the trials' yearly Sharpes spread by a variance of a half
    assert deflated.best_by_luck(1 / 500, 100) == pytest.approx(0.1132, abs=5e-5)
    for count, paper in ((100, 0.9004), (46, 0.9505)):  #: found among 46 trials, 0.9505
        bar = deflated.best_by_luck(1 / 500, count)
        assert deflated.deflate(2.5 / math.sqrt(250), bar, 1250, -3, 10) == pytest.approx(
            paper, abs=5e-5
        )
    assert deflated.best_by_luck(0.3, 1) == 0, "one trial alone was picked from nothing"
    assert deflated.deflate(0.1, 0.1, 50, 0, 3) == 0.5, "at luck's own best, an even chance"
    with pytest.raises(ValueError, match="no error left"):
        deflated.deflate(1, 0, 3, 2, 5)
    assert (deflated.PASS, deflated.FAIL, deflated.FLAG, luck.FAMILY) == (0.90, 0.50, 2.0, 0.05)
    assert set(deflated.OWN) - set(deflated.NAMED) == {"luck"}, "one correction, not two"


def test_a_winner_falls_through_the_bands_as_the_trials_it_was_picked_from_grow() -> None:
    winner, noise = _bell(9, 0.012), [_bell(n, 0) for n in range(100, 104)]
    (alone,) = deflated.judge([winner], 0)
    assert alone.bar == 0 and alone.deflated > 0.99 and alone.least is Answer.PASS
    assert alone.luck == luck.correct([winner], 0)[0]
    assert alone.sharpe == float(winner.t or 0) / math.sqrt(40)
    assert alone.rungs == dict.fromkeys(deflated.OWN, Answer.PASS)
    seen, chances = {}, []
    for unjudged in (0, 100, 50000):
        *others, picked = deflated.judge([*noise, winner], unjudged)
        assert picked.luck.trials == 5 + unjudged
        assert all(o.rungs["first"] is o.rungs["luck"] is Answer.FAIL for o in others)
        assert picked.bar == deflated.best_by_luck(1 / 39, 5 + unjudged) == others[0].bar
        seen[unjudged] = (picked.rungs["deflated"], picked.rungs["luck"], picked.least)
        chances.append(picked.deflated)
    assert seen == {
        0: (Answer.PASS, Answer.PASS, Answer.PASS),
        100: (Answer.DOUBT, Answer.PASS, Answer.DOUBT),
        50000: (Answer.FAIL, Answer.FAIL, Answer.FAIL),
    }
    assert chances[0] >= deflated.PASS > chances[1] >= deflated.FAIL > chances[2]
    #: the bar is the count's alone: a trial's company, even its own twin, does not move it
    twin, _ = deflated.judge([winner, winner], 103)
    assert twin.deflated == chances[1] and twin.bar == pytest.approx(0.408, abs=5e-4)
    #: the luck rung fails a weaker winner the Sharpe left in doubt: reported, it bounds nothing
    weak = deflated.judge([*noise, _bell(9, 0.008)], 5)[-1]
    answers = (Answer.PASS, Answer.FAIL, Answer.DOUBT, Answer.PASS)
    assert weak.rungs == dict(zip(deflated.OWN, answers, strict=True))
    assert weak.least is Answer.DOUBT
    #: failing fairly: a trial with one trade has no Sharpe and one with no trades nothing at
    #: all; neither has failed, on any rung, and both still count
    single, none, counted = deflated.judge([_verdict([0.5]), _verdict([]), winner], 102)
    assert (single.sharpe, single.yearly, single.bar, single.deflated) == (None, None, None, 0)
    assert single.rungs == dict.fromkeys(deflated.OWN, Answer.THIN) and counted == twin
    assert (single.least, none.least) == (Answer.THIN, Answer.FAULT)
    #: 29 trades at a yearly Sharpe far too good, or far under nothing: not enough evidence
    for thin in (_bell(9, 0.05, 29), _bell(9, -0.05, 29)):
        (judged,) = deflated.judge([_verdict([float(p.gain) for p in thin.trades], 1)], 0)
        assert judged.least is Answer.THIN and abs(judged.yearly or 0) > deflated.FLAG
    assert list(Answer) == [Answer.FAULT, Answer.FAIL, Answer.THIN, Answer.DOUBT, Answer.PASS]


def test_small_wins_and_a_rare_large_loss_are_believed_less_than_a_bell() -> None:
    rng = random.Random(4)  # noqa: S311 - a repeatable test draw, not a secret
    lopsided = [0.012 + rng.gauss(0, 0.002) for _ in range(38)] + [-0.07, -0.05]
    mean = sum(lopsided) / 40
    spread = math.sqrt(sum((g - mean) ** 2 for g in lopsided) / 39)
    #: a bell of the same trades, mean and spread, so the same standard errors
    draws = [rng.gauss(0, 1) for _ in range(40)]
    centre = sum(draws) / 40
    width = math.sqrt(sum((d - centre) ** 2 for d in draws) / 39)
    bell = [mean + spread * (d - centre) / width for d in draws]
    noise = [_bell(n, 0) for n in range(100, 110)]
    one, other = (deflated.judge([*noise, _verdict(g)], 0)[-1] for g in (lopsided, bell))
    width = math.sqrt(39 / 40) * spread
    skew, tails = (sum((g - mean) ** p for g in lopsided) / 40 / width**p for p in (3, 4))
    by_hand = deflated.deflate(one.sharpe or 0, deflated.best_by_luck(1 / 39, 11), 40, skew, tails)
    assert skew < -3 and tails > 15 and one.deflated == pytest.approx(by_hand, abs=1e-3)
    assert (
        one.sharpe == pytest.approx(other.sharpe, abs=1e-3)
        and one.luck.passed
        and other.luck.passed
    )
    assert one.deflated < deflated.PASS < other.deflated
    assert (one.least, other.least) == (Answer.DOUBT, Answer.PASS)


def test_a_yearly_sharpe_above_two_is_flagged_and_is_not_a_win() -> None:
    gains = [0.01 + 0.02 * math.sin(n) for n in range(40)]
    slow, fast = (deflated.judge([_verdict(gains, years)], 0)[0] for years in (10, 2))
    sharpe = slow.sharpe or 0.0
    assert 0.7 < sharpe == fast.sharpe and slow.deflated == fast.deflated > deflated.PASS
    assert slow.yearly == pytest.approx(sharpe * 2, rel=1e-3) and slow.least is Answer.PASS
    assert deflated.FLAG < sharpe * math.sqrt(20) == pytest.approx(fast.yearly, rel=1e-3)
    assert fast.rungs == dict.fromkeys(deflated.OWN, Answer.PASS) | {"yearly": Answer.DOUBT}
    assert fast.least is Answer.DOUBT


def test_among_noise_chance_winners_do_not_survive_and_a_real_edge_does() -> None:
    families = [[_bell(100 * f + n, 0) for n in range(40)] for f in range(40)]
    judged = [deflated.judge(family, 0) for family in families]
    assert sum(any(j.luck.verdict.passed for j in family) for family in judged) > 20
    fooled = sum(any(j.least is Answer.PASS for j in family) for family in judged)
    assert fooled <= 2, "forty sets of forty trials with no edge in any: 5% is the most"
    found = [deflated.judge([*family, _bell(7, 0.015)], 0)[-1] for family in families]
    assert all(j.least is Answer.PASS for j in found), "a real edge is not thrown out"


def test_a_rule_is_judged_on_its_own_lines_clustered_and_one_correction_gates() -> None:
    #: L18's known answer: two lines trading as one and a stranger are two looks, three lines
    rng = random.Random(5)  # noqa: S311 - a repeatable test draw, not a secret
    twin, other = ([rng.gauss(0.006, 0.02) for _ in range(40)] for _ in "ab")
    lines = [
        _verdict(g, 0.33, n, line, 3)
        for g, n, line in ((twin, "1", VUSA), (twin, "2", AAPL), (other, "3", NVDA))
    ]
    judged = deflated.judge_lines(lines)
    looks = trials.clusters(trials.daily(lines), 0)
    assert (looks.trials, looks.held, looks.days) == (2, 3, 122)
    assert [j.luck.trials for j in judged] == [3, 3, 3], "the set's own lines, not 3,435"
    above = looks.above(lines[0].key.cell, judged[0].sharpe or 0, 40)
    assert judged[0].bar == pytest.approx(deflated.best_by_luck(looks.spread(40), 2) + above)
    bars = [n for j in judged[1:] for n in (j.bar, j.deflated, j.luck.corrected)]
    assert bars == pytest.approx([0.1166, 0.7602, 0.2354, 0.1145, 0.9971, 0.0008], abs=1e-4)
    assert judged[2].luck.chance * 3435 > luck.FAMILY, "charged every line ever, it would fail"
    refused = replace(_verdict(other, 0.5, "7", NVDA, 3), refusal="too big at this capital")
    pool = verdict.Pool([], {one.key.cell: one for one in (*lines, refused)}, "", False)
    assert [pool.among(one.key.cell) for one in lines] == list(judged), "the pool's lines, once"
    *both, idle = deflated.judge_lines([*lines[:2], _verdict([], 0.33, "4", NVDA)])
    assert (idle.least, idle.luck.trials) == (Answer.FAULT, 3) and (both[0].bar or 1) < (
        bars[0] or 0
    )
    rsi = rung.verdict(Key(replace(lines[2].key.cell, strategy="rsi2_pullback"), "", ""), ())
    with pytest.raises(ValueError, match="no first rung"):
        pool.among(rsi.key.cell)
    for odd in ([], [*lines[:2], rsi]):
        with pytest.raises(ValueError, match="one rule's"):
            deflated.judge_lines(odd)
    with pytest.raises(ValueError, match="not one set"):
        trials.daily([lines[0], lines[0]])
    longer = trials.daily([lines[0], _verdict(twin, 1, "5", NVDA, 3)])  #: one window, aligned
    assert [len(row) for row in longer.values()] == [366, 366]
    assert len({tuple(row) for row in longer.values()}) == 1, "day for day on the span"
    sour = verdict.Pool([], {one.key.cell: one for one in (lines[0], rsi)}, "", False)
    for _ in range(2):  #: the set's failure remembered, as `fold` remembers its own
        with pytest.raises(ValueError, match="one rule's"):
            sour.among(rsi.key.cell)
    assert isinstance(sour.unlooked, ValueError)


#: THE PROOFS OF RUNG 7 (R-RUNNER-135): the deflated Sharpe of a pick's gains against the count
#: and spread of the set it was picked from, as `_deflated` reads them. Its stated rate is one
#: in ten, of bell gains: what a trial at exactly luck's best passes at (1 - PASS).
Judge = Callable[[Sequence[Decimal], int, float], Answer]
Pick = tuple[tuple[Decimal, ...], float]
CELLS, TRIALS, TRADES, PICKED = 500, 100, 60, 0.01  #: the pick of a hundred noise: one in 100
#: THE POWER CURVE, recorded: of CELLS sets of TRIALS trials, one with this true Sharpe a trade
#: planted among noise, those whose pick passes against the whole set
POWER = {0.3: 33, 0.5: 208, 0.8: 492}


def _judge(gains: Sequence[Decimal], count: int, spread: float) -> Answer:
    """The deflated rung's answer on a pick's gains, on the first rung's own Sharpe."""
    values = [float(gain) for gain in gains]
    with localcontext(ARITHMETIC):
        one = deflated.per_trade(float(rung.standard_errors(gains) or 0), len(values))
    bar = deflated.best_by_luck(spread, count)
    return deflated.believe(deflated.deflate(one, bar, len(values), *deflated.shape(values)))


def _pick(gains: NDArray[np.float64]) -> Pick:
    """A set's best trial, each row a trial's gains, and the spread of the set's Sharpes."""
    sharpes = gains.mean(axis=1) / gains.std(axis=1, ddof=1)
    return tuple(map(Decimal, gains[sharpes.argmax()].tolist())), float(sharpes.var(ddof=1))


@cache
def _picks(edge: float) -> tuple[Pick, ...]:
    """The picks of CELLS sets of TRIALS bell trials, the first of each with this edge."""
    rng, picks = np.random.default_rng(round(edge * 10)), []
    for _ in range(CELLS):
        gains = rng.standard_normal((TRIALS, TRADES))
        gains[0] += edge
        picks.append(_pick(gains))
    return tuple(picks)


def _passes(judge: Judge, edge: float) -> int:
    return sum(judge(gains, TRIALS, spread) is Answer.PASS for gains, spread in _picks(edge))


def _edge(judge: Judge) -> bool:
    """A planted edge passes: a true Sharpe of 1 a trade among a hundred trials, 499 in 500."""
    return _passes(judge, 1.0) > 0.99 * CELLS


def _noise(judge: Judge) -> bool:
    """Noise judged alone passes inside the stated rate's exact band; its pick of a hundred,
    judged against the hundred, under the band of one time in a hundred."""
    rng = np.random.default_rng(7)
    alone = (tuple(map(Decimal, rng.standard_normal(TRADES).tolist())) for _ in range(CELLS))
    low, high = band(CELLS, 1 - deflated.PASS)
    passed = sum(judge(gains, 1, 0.0) is Answer.PASS for gains in alone)
    return low <= passed <= high and _passes(judge, 0.0) <= band(CELLS, PICKED)[1]


def _power(judge: Judge) -> bool:
    return [_passes(judge, edge) for edge in POWER] == list(POWER.values())


def test_rung_seven_passes_each_proof_and_catches_three_broken_copies() -> None:
    """The count of trials forgotten; the spread in a year's units against a Sharpe a trade;
    the bar set by the spread itself, its root forgotten."""
    assert _edge(_judge) and _noise(_judge) and _power(_judge)

    def no_count(gains: Sequence[Decimal], _count: int, _spread: float) -> Answer:
        return _judge(gains, 1, 0.0)

    def yearly_spread(gains: Sequence[Decimal], count: int, spread: float) -> Answer:
        return _judge(gains, count, 250 * spread)

    def no_root(gains: Sequence[Decimal], count: int, spread: float) -> Answer:
        return _judge(gains, count, spread**2)

    assert _edge(no_count) and not _noise(no_count) and not _power(no_count)
    assert _edge(no_root) and not _noise(no_root) and not _power(no_root)
    assert _passes(no_count, 0.0) > 0.99 * CELLS, "luck's best of a hundred, passed nearly always"
    assert not _edge(yearly_spread) and not _power(yearly_spread), "no edge could ever pass"


def test_rung_sevens_old_audit_defects_must_fail() -> None:
    #: LAD-09: the deflating is never skipped: no count, or a set with no spread, is refused
    for count, spread in ((0, 0.01), (100, 0.0), (100, math.nan), (100, -0.01), (1, math.inf)):
        with pytest.raises(ValueError, match="nothing to deflate by"):
            deflated.best_by_luck(spread, count)
    #: by hand: 32 gains of 2% and 8 losses of 3%, mean 1%: skew -1.5, kurtosis 3.25
    assert deflated.shape([0.02] * 32 + [-0.03] * 8) == pytest.approx((-1.5, 3.25))
    #: LAD-03: many small wins and a rare large loss pass as a bell, and are in doubt here
    lopsided = [Decimal("0.01")] * 57 + [Decimal("-0.10")] * 3
    one = deflated.per_trade(float(rung.standard_errors(lopsided) or 0), 60)
    shaped = deflated.shape([float(gain) for gain in lopsided])
    as_a_bell, as_it_is = (deflated.deflate(one, 0, 60, *m) for m in ((0, 3), shaped))
    assert as_a_bell >= deflated.PASS > as_it_is > deflated.FAIL
    assert _judge(lopsided, 1, 0.0) is Answer.DOUBT
    #: LAD-08: the pick of a hundred trials of noise passes alone, and not against its hundred
    picked, spread = _picks(0.0)[0]
    assert _judge(picked, 1, 0.0) is Answer.PASS, "judged as if it were the only trial"
    assert _judge(picked, TRIALS, spread) is Answer.DOUBT, "a chance of 0.79: in doubt"
    assert _judge(picked, 100 * TRIALS, spread) is Answer.FAIL, "under it: luck likelier"
    assert _judge([-g for g in picked], 1, 0.0) is Answer.FAIL  #: LAD-08: a loss is a fail


def test_the_rate_is_of_bell_gains_and_lopsided_noise_needs_the_first_rungs_planted_loss() -> None:
    """Small wins, and one trade in twenty a loss nineteen times the size: the pick of a
    hundred as sampled nearly always met few losses and passes; with the one more loss the
    first rung plants (G2) among every trial's gains, as `Verdict.gains` holds them, none."""
    rng, sets, passed = np.random.default_rng(1), 100, [0, 0]
    for _ in range(sets):
        lost = rng.random((TRIALS, TRADES)) < 1 / 20
        gains = np.where(lost, -0.19, rng.normal(0.01, 0.005, (TRIALS, TRADES)))
        for planted, seen in enumerate((gains, np.c_[gains, np.full(TRIALS, -0.19)])):
            best, spread = _pick(seen)
            passed[planted] += _judge(best, TRIALS, spread) is Answer.PASS
    assert passed[0] > 0.9 * sets, "as sampled: far over the stated rate"
    assert passed[1] == 0, "the loss that had not come yet, planted: none"
