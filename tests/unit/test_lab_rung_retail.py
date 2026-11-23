"""The retail rung, on known answers worked by hand (R-RUNNER-229)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from test_lab_rung import FREE, POUND, _bars

from desk.lines import YARDSTICK
from lab import rung_retail, verdict
from lab.cell import Cell, Key, Trade
from lab.rung import Answer, Priced, Verdict
from lab.rung_retail import Against, Standing, days, standing


@pytest.fixture
def eased_off(monkeypatch: pytest.MonkeyPatch) -> None:
    """The off assertions of these tests: the ladder's easing switch is set off, not assumed."""
    monkeypatch.setattr(verdict, "EASED", False)


#: Market [+10%, -20%, +10%]: 1.1, 0.88, 0.968 -> -3.2%, fell 0.2 from 1.1, mean 0 so Sharpe 0.
MARKET = [0.10, -0.20, 0.10]
#: Basket [+5%, -10%, +4%]: 1.05, 0.945, 0.9828 -> -1.72%, fell 0.1 from 1.05, mean < 0.
HALF_FALL = [0.05, -0.10, 0.04]
#: Market [+5%, +5%, -10%, +5%, +5%]: 1.05^4 * 0.9 -> 9.3956%, fell 0.1, Sharpe 0.02/0.067082.
RISING = [0.05, 0.05, -0.10, 0.05, 0.05]
#: Basket [+10%, -10%, +10%, 0, 0]: 1.089 -> 8.9%, the same fall 0.1, Sharpe 0.02/0.083666.
WHOLE_FALL = [0.10, -0.10, 0.10, 0.0, 0.0]


def test_standing_is_worked_by_hand() -> None:
    got = standing(MARKET)
    assert got.made == pytest.approx(-0.032) and got.fall == pytest.approx(0.2)
    assert got.sharpe == pytest.approx(0.0)
    assert standing(RISING).sharpe == pytest.approx(0.298142, abs=1e-6)
    assert standing(WHOLE_FALL).sharpe == pytest.approx(0.239046, abs=1e-6)


def test_a_basket_that_loses_a_little_but_falls_half_as_far_passes_on_risk() -> None:
    ours, theirs = standing(HALF_FALL), standing(MARKET)
    assert ours.made == pytest.approx(-0.0172) and ours.fall == pytest.approx(0.1)
    assert ours.sharpe < theirs.sharpe  #: the Sharpe clause fails: only the risk clause passes it
    assert -0.0172 >= 0.8 * -0.032 and 0.1 <= 0.6 * 0.2  #: 80% of the return, 60% of the fall
    assert rung_retail.beats(ours, theirs)


def test_a_basket_that_matches_the_return_with_the_whole_fall_fails() -> None:
    ours, theirs = standing(WHOLE_FALL), standing(RISING)
    assert ours.made == pytest.approx(0.089) and ours.fall == pytest.approx(theirs.fall)
    assert ours.made >= 0.8 * theirs.made and ours.sharpe < theirs.sharpe
    assert not rung_retail.beats(ours, theirs)


def test_an_equal_sharpe_passes_and_the_boundary_is_the_markets_own() -> None:
    same = Standing(0.1, 0.3, 0.5)
    assert rung_retail.beats(same, same)
    assert not rung_retail.beats(Standing(0.1, 0.3, 0.49), same)


def test_judge_fails_fairly_and_loudly() -> None:
    market = [0.01, -0.005] * 15
    assert rung_retail.judge([], [])[0] is Answer.FAULT
    assert rung_retail.judge(HALF_FALL, MARKET)[0] is Answer.THIN
    assert rung_retail.judge(market, market)[0] is Answer.PASS
    worse = [day - 0.02 for day in market]
    assert rung_retail.judge(worse, market)[0] is Answer.FAIL
    with pytest.raises(ValueError, match="beside"):
        rung_retail.judge(market[:-1], market)
    with pytest.raises(ValueError, match="no spread"):
        standing([0.01] * 30)


@pytest.mark.usefixtures("eased_off")  #: the first assert is of the switch off
def test_days_pair_the_sale_days_pounds_with_the_markets_closes_and_grade_waits_for_the_switch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bars = _bars([100, 110, 99])  #: closes 100, 110, 99: market days +10%, -10%
    sale = (bars[0].day, bars[2].day)
    trade = Priced(Trade(*sale), 1, Decimal(100), Decimal(150), FREE, sale, None)
    window = Cell("breakout_20_10", YARDSTICK, *sale)
    basket = Verdict(Key(window, "code", "x"), "b", (trade,), Decimal(3), Answer.PASS, ())
    against = Against(YARDSTICK, bars, POUND)
    #: one sale on the third day: 150 - 100 = 50 pounds of 10,000 capital; none on the second
    assert days(basket, against) == pytest.approx(([0.0, 0.005], [0.1, -0.1]))
    assert rung_retail.grade(basket, against) is None  #: off: nothing is asked
    monkeypatch.setattr(verdict, "EASED", True)
    assert (rung_retail.grade(basket, against) or (None,))[0] is Answer.THIN


def test_the_scorecard_rule_over_the_rungs() -> None:
    weak, ok = Answer.THIN, Answer.PASS
    assert verdict.scorecard([ok, weak, Answer.DOUBT], 1.0) == "PASS"
    assert verdict.scorecard([weak, weak, weak], 1.0) == "FAIL"
    assert verdict.scorecard([ok, Answer.FAIL], 1.0) == "FAIL"
    assert verdict.scorecard([ok], 2.1) == "STOP"
