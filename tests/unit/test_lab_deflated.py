"""The luck test fixed before any result: the deflated Sharpe and its bands, the yearly
Sharpe too good to be true, and the one rule that reads every named rung."""

from __future__ import annotations

import math
import random
from datetime import date, timedelta
from decimal import Decimal

import pytest

from lab import deflated, luck, rung
from lab.cell import Cell, Key, Trade
from lab.deflated import Answer
from lab.rung import Priced, Verdict

DAY = date(2010, 1, 1)


def _verdict(gains: list[float], years: float = 10, name: str = "a") -> Verdict:
    """A trial with these gains, one per trade, over a window of so many years, judged by
    the first rung's own rule."""
    back = [Decimal(f"{100 * (1 + gain):.4f}") for gain in gains]
    priced = tuple(Priced(Trade(DAY, DAY), 1, Decimal(100), b, b - 100) for b in back)
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
    assert (deflated.PASS, deflated.FAIL, deflated.FLAG, luck.FAMILY) == (0.90, 0.50, 2.0, 0.05)


def test_one_rule_reads_every_named_rung_and_gives_the_worst() -> None:
    assert deflated.NAMED == ("first", "luck", "deflated", "yearly")
    passes = dict.fromkeys(deflated.NAMED, Answer.PASS)
    assert deflated.rule(passes) is Answer.PASS
    assert deflated.rule(passes | {"yearly": Answer.DOUBT}) is Answer.DOUBT
    assert deflated.rule(passes | {"yearly": Answer.DOUBT, "luck": Answer.FAIL}) is Answer.FAIL
    for rungs in ({"first": Answer.PASS}, passes | {"another": Answer.PASS}):
        with pytest.raises(ValueError, match="the rule reads"):
            deflated.rule(rungs)


def test_a_winner_falls_through_the_bands_as_the_trials_it_was_picked_from_grow() -> None:
    winner, noise = _bell(9, 0.012), [_bell(n, 0) for n in range(100, 104)]
    (alone,) = deflated.judge([winner], 0)
    assert alone.bar == 0 and alone.deflated > 0.99 and alone.answer is Answer.PASS
    assert alone.luck == luck.correct([winner], 0)[0] and alone.sharpe == float(
        winner.t or 0
    ) / math.sqrt(40)
    assert alone.rungs == dict.fromkeys(deflated.NAMED, Answer.PASS)
    seen = {}
    for unjudged in (0, 20, 100):
        *others, picked = deflated.judge([*noise, winner], unjudged)
        assert picked.luck.trials == 5 + unjudged and all(o.answer is Answer.FAIL for o in others)
        seen[unjudged] = (picked.rungs["deflated"], picked.rungs["luck"], picked.answer)
        assert picked.bar == others[0].bar > 0, "one bar for the whole set"
    assert seen == {
        0: (Answer.PASS, Answer.PASS, Answer.PASS),
        20: (Answer.DOUBT, Answer.PASS, Answer.DOUBT),
        100: (Answer.FAIL, Answer.PASS, Answer.FAIL),
    }
    bars = [deflated.judge([*noise, winner], n)[-1] for n in (0, 20, 100)]
    assert bars[0].deflated >= deflated.PASS > bars[1].deflated >= deflated.FAIL > bars[2].deflated
    #: a trial with one trade has no Sharpe: it fails, and still counts
    single, *_ = deflated.judge([_verdict([0.5]), winner, noise[0]], 0)
    assert (single.sharpe, single.yearly, single.deflated, single.answer) == (
        None,
        None,
        0,
        Answer.FAIL,
    )
    with pytest.raises(ValueError, match="spread"):
        deflated.judge([winner], 3)


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
    assert (
        one.sharpe == pytest.approx(other.sharpe, abs=1e-3)
        and one.luck.passed
        and other.luck.passed
    )
    assert one.deflated < deflated.PASS < other.deflated
    assert (one.answer, other.answer) == (Answer.DOUBT, Answer.PASS)


def test_a_yearly_sharpe_above_two_is_flagged_and_is_not_a_win() -> None:
    gains = [0.01 + 0.02 * math.sin(n) for n in range(40)]
    slow, fast = (deflated.judge([_verdict(gains, years)], 0)[0] for years in (10, 2))
    sharpe = slow.sharpe or 0.0
    assert 0.7 < sharpe == fast.sharpe and slow.deflated == fast.deflated > deflated.PASS
    assert slow.yearly == pytest.approx(sharpe * 2, rel=1e-3) and slow.answer is Answer.PASS
    assert deflated.FLAG < sharpe * math.sqrt(20) == pytest.approx(fast.yearly, rel=1e-3)
    assert fast.rungs == dict.fromkeys(deflated.NAMED, Answer.PASS) | {"yearly": Answer.DOUBT}
    assert fast.answer is Answer.DOUBT


def test_among_noise_chance_winners_do_not_survive_and_a_real_edge_does() -> None:
    families = [[_bell(100 * f + n, 0) for n in range(40)] for f in range(40)]
    fooled = sum(
        any(j.answer is Answer.PASS for j in deflated.judge(family, 0)) for family in families
    )
    assert fooled <= 2, "5% of forty sets of forty trials with no edge in any of them"
    believed = sum(any(j.deflated >= deflated.PASS for j in deflated.judge(f, 0)) for f in families)
    assert believed <= 6, "the deflated Sharpe alone lets through about its stated one in ten"
    found = [deflated.judge([*family, _bell(7, 0.015)], 0)[-1] for family in families]
    assert all(j.answer is Answer.PASS for j in found), "a real edge is not thrown out"
