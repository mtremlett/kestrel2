"""The basket: a rule's lines pooled as one portfolio, judged on the pooled after-cost gains, and
its retail rung beside the market, on known answers worked by hand (R-RUNNER-229)."""

from __future__ import annotations

from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from test_lab_rung import FREE, POUND, _bars

from desk.lines import LINES, YARDSTICK
from lab import basket, rung, verdict
from lab.basket import Against, Standing, standing
from lab.cell import Cell, Key, Trade
from lab.rung import Answer, Priced, Verdict

DAY = date(2010, 1, 1)
LINE_NAMES = ("VUSA", "ISF", "SMGB")


def _line_verdict(symbol: str) -> Verdict:
    """12 trades of a line: gains alternating 5% and 1%, so 6 and 6 after the (nil) costs."""
    gains = [Decimal("0.05"), Decimal("0.01")] * 6
    priced = tuple(
        Priced(Trade(DAY, DAY), 1, Decimal(100), 100 * (1 + g), FREE, (DAY, DAY), None)
        for g in gains
    )
    line = next(one for one in LINES if one.symbol == symbol)
    window = Cell("breakout_20_10", line, DAY, DAY + timedelta(days=3652))
    return rung.verdict(Key(window, "code", symbol), priced)


def test_three_thin_lines_make_one_basket_of_36_trades_judged_on_the_pooled_gains(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(verdict, "EASED", True)
    lines = [_line_verdict(s) for s in LINE_NAMES]
    assert {v.answer for v in lines} == {Answer.THIN}  #: none is judged alone: 12 of 30
    row = basket.row(7, "breakout_20_10", lines, 50, Answer.PASS)
    #: by hand: 36 gains, 18 of 0.05 and 18 of 0.01; mean 0.03, each 0.02 from it, so the
    #: sample variance is 36 * 0.0004 / 35, the standard error sqrt(0.0004 / 35), and
    #: t = 0.03 / sqrt(0.0004 / 35) = 0.03 * sqrt(87500) = 8.874: above 2 on 36 trades, PASS
    assert row["trades"] == 36
    assert row["answer"] == "PASS"
    assert row["cell"] == ["breakout_20_10", "BASKET", "all lines pooled"]
    assert row["trials"] == 50
    assert "36 trades judged" in row["rungs"]["first"][1]
    assert "8.87 standard errors" in row["rungs"]["first"][1]
    assert row["unrun"] == basket.UNRUN  #: a basket's pass is no pass of the whole ladder
    assert not verdict.goes(row)


def test_a_failing_basket_over_one_standard_error_is_incubate_listed_apart_and_never_goes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(verdict, "EASED", True)
    lines = [_line_verdict(s) for s in LINE_NAMES]
    failing = replace(lines[0], answer=Answer.FAIL, t=Decimal("1.5"))
    monkeypatch.setattr(rung, "verdict", lambda key, _: replace(failing, key=key))
    row = basket.row(7, "breakout_20_10", lines, 50, Answer.PASS)
    assert row["answer"] == "INCUBATE" and not verdict.goes(row)
    assert basket.row(7, "breakout_20_10", lines, 50, Answer.FAIL)["answer"] == "FAIL"
    table = verdict.write_table(tmp_path, "T", "Q?", [row], ["breakout_20_10"], 3, (1, 2))
    assert "## INCUBATE: paper only" in table.read_text(encoding="utf-8")


def test_the_retail_rung_stands_in_a_basket_row_only_while_eased_and_given_a_market(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bars = _bars([100] * 40 + [110])
    against = basket.Against(YARDSTICK, bars, POUND)
    lines = [replace(_line_verdict(s), trades=()) for s in LINE_NAMES[:1]]
    monkeypatch.setattr(verdict, "EASED", False)
    assert "retail" not in basket.row(7, "breakout_20_10", lines, 50, Answer.PASS, against)["rungs"]
    monkeypatch.setattr(verdict, "EASED", True)
    assert "retail" not in basket.row(7, "breakout_20_10", lines, 50, Answer.PASS)["rungs"]
    row = basket.row(7, "breakout_20_10", lines, 50, Answer.PASS, against)
    assert row["rungs"]["retail"][0] == "FAULT"  #: no trade to set beside the market: inherited


def test_a_basket_with_one_stale_market_line_publishes_naming_the_line_refused(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(verdict, "EASED", True)
    bars = _bars([100] * 40)
    late = (bars[-1].day + timedelta(days=10),) * 2
    lines = [_line_verdict(s) for s in LINE_NAMES]
    lines = [replace(v, trades=tuple(replace(p, held=late) for p in v.trades)) for v in lines]
    row = basket.row(7, "breakout_20_10", lines, 50, Answer.PASS, Against(YARDSTICK, bars, POUND))
    assert row["rungs"]["retail"][0] == "FAULT"
    assert f"stale market line refused: {YARDSTICK.symbol} has no bar" in row["rungs"]["retail"][1]
    assert verdict.write_table(tmp_path, "T", "Q?", [row], ["breakout_20_10"], 3, (1, 2)).exists()


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
    assert basket.beats(ours, theirs)


def test_a_basket_that_matches_the_return_with_the_whole_fall_fails() -> None:
    ours, theirs = standing(WHOLE_FALL), standing(RISING)
    assert ours.made == pytest.approx(0.089) and ours.fall == pytest.approx(theirs.fall)
    assert ours.made >= 0.8 * theirs.made and ours.sharpe < theirs.sharpe
    assert not basket.beats(ours, theirs)


def test_an_equal_sharpe_passes_and_the_boundary_is_the_markets_own() -> None:
    same = Standing(0.1, 0.3, 0.5)
    assert basket.beats(same, same)
    assert not basket.beats(Standing(0.1, 0.3, 0.49), same)


def test_judge_fails_fairly_and_loudly() -> None:
    market = [0.01, -0.005] * 15
    assert basket.judge([], [])[0] is Answer.FAULT
    assert basket.judge(HALF_FALL, MARKET)[0] is Answer.THIN
    assert basket.judge(market, market)[0] is Answer.PASS
    worse = [day - 0.02 for day in market]
    assert basket.judge(worse, market)[0] is Answer.FAIL
    with pytest.raises(ValueError, match="beside"):
        basket.judge(market[:-1], market)
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
    b = Verdict(Key(window, "code", "x"), "b", (trade,), Decimal(3), Answer.PASS, ())
    against = Against(YARDSTICK, bars, POUND)
    #: one sale on the third day: 150 - 100 = 50 pounds of 10,000 capital; none on the second
    assert basket.days(b, against) == pytest.approx(([0.0, 0.005], [0.1, -0.1]))
    assert basket.grade(b, against) is None  #: off: nothing is asked
    monkeypatch.setattr(verdict, "EASED", True)
    assert (basket.grade(b, against) or (None,))[0] is Answer.THIN


def test_a_sale_on_a_day_the_market_is_shut_is_booked_to_its_next_bar() -> None:
    """A London line judged on a US proxy sells on a UK bank holiday, New York open: ISF has
    no bar that day, so the sale's pounds land on ISF's next bar; after its last, refused."""
    bars = _bars([100, 110, 99, 99])
    shut = bars[:2] + bars[3:]  #: the market has no bar on the third day
    sale = (bars[0].day, bars[2].day)
    trade = Priced(Trade(*sale), 1, Decimal(100), Decimal(150), FREE, sale, None)
    window = Cell("breakout_20_10", YARDSTICK, *sale)
    b = Verdict(Key(window, "code", "x"), "b", (trade,), Decimal(3), Answer.PASS, ())
    assert basket.days(b, Against(YARDSTICK, shut, POUND)) == pytest.approx(
        ([0.0, 0.005], [0.1, -0.1])
    )
    with pytest.raises(ValueError, match="no bar on or after"):
        basket.days(b, Against(YARDSTICK, bars[:2], POUND))


def test_the_scorecard_rule_over_the_rungs() -> None:
    weak, ok = Answer.THIN, Answer.PASS
    assert verdict.scorecard([ok, weak, Answer.DOUBT], 1.0) == "PASS"
    assert verdict.scorecard([weak, weak, weak], 1.0) == "FAIL"
    assert verdict.scorecard([ok, Answer.FAIL], 1.0) == "FAIL"
    assert verdict.scorecard([ok], 2.1) == "STOP"
