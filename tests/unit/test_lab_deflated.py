"""The luck test fixed before any result: the deflated Sharpe and its bands, the yearly
Sharpe too good to be true, and the one rule that reads every named rung."""

from __future__ import annotations

import math
import random
from datetime import date, timedelta
from decimal import Decimal

import pytest
from test_lab_rung import FREE

from lab import deflated, luck, rung
from lab.cell import Cell, Key, Trade
from lab.rung import Answer, Priced, Verdict

DAY = date(2010, 1, 1)


def _verdict(gains: list[float], years: float = 10, name: str = "a") -> Verdict:
    """A trial with these gains, one per trade, over a window of so many years, judged by
    the first rung's own rule."""
    back = [Decimal(f"{100 * (1 + gain):.4f}") for gain in gains]
    priced = tuple(Priced(Trade(DAY, DAY), 1, Decimal(100), b, FREE, (DAY, DAY)) for b in back)
    window = Cell("breakout_20_10", "VUSA", DAY, DAY + timedelta(days=round(365.25 * years)))
    return rung.verdict(Key(window, "code", name), priced)


def _bell(seed: int, edge: float, trades: int = 40) -> Verdict:
    rng = random.Random(seed)  # noqa: S311 - a repeatable test draw, not a secret
    return _verdict([rng.gauss(edge, 0.02) for _ in range(trades)], name=str(seed))


def test_the_deflated_sharpe_is_the_published_one() -> None:
    #: Bailey and Lopez de Prado's own worked case: the best of 100 trials, a yearly Sharpe
    #: of 2.5 on 1,250 days, the trials' yearly Sharpes spread by a variance of a half
    bar = deflated.best_by_luck(1 / 500, 100)
    assert bar == pytest.approx(0.1132, abs=5e-5)
    assert deflated.deflate(2.5 / math.sqrt(250), bar, 1250, -3, 10) == pytest.approx(
        0.9004, abs=5e-5
    )
    assert deflated.best_by_luck(0.3, 1) == 0, "one trial alone was picked from nothing"
    assert deflated.deflate(0.1, 0.1, 50, 0, 3) == 0.5, "at luck's own best, an even chance"
    with pytest.raises(ValueError, match="no error left"):
        deflated.deflate(1, 0, 3, 2, 5)
    assert (deflated.PASS, deflated.FAIL, deflated.FLAG, luck.FAMILY) == (0.90, 0.50, 2.0, 0.05)


def test_one_rule_reads_every_named_rung_and_gives_the_worst() -> None:
    assert deflated.NAMED == ("first", "luck", "deflated", "yearly", "folds", "market", "shuffle")
    assert deflated.NAMED[:4] == deflated.OWN
    passes = dict.fromkeys(deflated.NAMED, Answer.PASS)
    assert deflated.rule(passes) is Answer.PASS
    assert deflated.rule(passes | {"yearly": Answer.DOUBT}) is Answer.DOUBT
    assert deflated.rule(passes | {"folds": Answer.THIN}) is Answer.THIN, "a thin fold: no pass"
    assert deflated.rule(passes | {"market": Answer.FAIL}) is Answer.FAIL
    assert deflated.rule(passes | {"yearly": Answer.DOUBT, "luck": Answer.FAIL}) is Answer.FAIL
    without = {name: Answer.PASS for name in deflated.NAMED if name != "folds"}
    for rungs in (without, passes | {"another": Answer.PASS}):
        with pytest.raises(ValueError, match="the rule reads"):
            deflated.rule(rungs)


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
    #: the luck rung fails a weaker winner the first rung passed and the Sharpe left in doubt
    weak = deflated.judge([*noise, _bell(9, 0.008)], 5)[-1]
    answers = (Answer.PASS, Answer.FAIL, Answer.DOUBT, Answer.PASS)
    assert weak.rungs == dict(zip(deflated.OWN, answers, strict=True))
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
