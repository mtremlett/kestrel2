"""The market's rung: the edge judged against the market risk it took; a rule that only rides
its market fails, and a planted edge of its own passes."""

from __future__ import annotations

import math
import random
from dataclasses import replace
from decimal import Decimal

import pytest
from test_lab_rung import POUND, SHAPE, SPY, _bars, _judge, _walk

from desk.lines import YARDSTICK
from desk.orders import Settings
from desk.store import Bar
from lab import cell, market, rung
from lab.cell import Cell
from lab.rung import Answer

ROOM = Settings(Decimal(100_000))  #: room for a share of a market that has risen a hundredfold
VUSA = _judge(_bars(SHAPE), 24).key.cell.line


def _rising(seed: int, days: int = 5000) -> tuple[Bar, ...]:
    """A market that climbs a tenth of 1% a day whatever came before: nothing to time."""
    rng, closes = random.Random(seed), [10.0]  # noqa: S311 - a repeatable test walk, not a secret
    while len(closes) < days:
        closes.append(closes[-1] * (1.001 + rng.gauss(0, 0.01)))
    return _bars(closes)


def _against(bars: tuple[Bar, ...], held: tuple[Bar, ...], end: int = -1) -> market.Against:
    return market.judge(_judge(bars, end, room=ROOM), bars, YARDSTICK, held, POUND)


def test_a_rule_that_only_rides_its_market_fails_and_an_edge_of_its_own_passes() -> None:
    for seed in (1, 2, 4, 5):  #: four markets whose rider the first rung passes
        up = _rising(seed + 100)  #: its own draws: the walks share none with it
        rider = _against(up, up)  #: the breakout on the rising market itself
        assert rider.verdict.passed, "it earned, after costs: the first rung passes it"
        assert rider.t is not None and rider.t < 1 and rider.answer is Answer.FAIL, (seed, rider.t)
        assert rider.beta is not None and 0.3 < rider.beta < 0.9, "in the market half its days"
        #: a planted edge on a line of its own, the market rising beside it, is its own
        edge = _against(_walk(seed, 0.008), up)
        assert edge.answer is Answer.PASS and edge.t is not None and edge.t > 2.5, (seed, edge.t)
        assert edge.beta is not None and abs(edge.beta) < 0.05 and 4900 < edge.days <= 4999
        timed = _against(_walk(seed, 0.008), _walk(seed, 0.008))  #: the line its own market
        assert timed.answer is Answer.PASS, "in for its rises and out for the rest: an edge"
        none = _against(_walk(seed, 0), up)
        assert none.answer is Answer.FAIL and none.t is not None and none.t < 1, (seed, none.t)
        #: too few trades are not enough evidence here either, and nothing is measured
        few = _against(_walk(seed, 0)[:1500], up)
        assert (few.answer, few.t, few.beta, few.days) == (Answer.THIN, None, None, 0)
    none = _against(_bars(SHAPE), _rising(0), 23)
    assert none.answer is Answer.FAULT, "no trade: a fault in the test"


def test_a_trade_still_held_at_the_end_ends_the_days_counted_where_it_was_bought() -> None:
    bars, up = _walk(0, 0.008), _rising(100)
    end = next(n for n in range(4000, 5000) if _judge(bars, n).trades != _judge(bars, n + 1).trades)
    #: at `end` the last sale has not filled: its trade is not judged, nor are its days
    cut = _against(bars, up, end)
    judged = cut.verdict.trades[-1].held[1]
    assert bars[end].day > judged and cut.days < end
    assert bars[cut.days].day >= judged, "every judged day is counted"
    assert bars[cut.days + 1].day > judged, "and the unjudged trade's own days are not"
    #: the days before a window's start warm the rule, and are not counted
    late = cell.run(Cell("breakout_20_10", "VUSA", bars[1000].day, bars[end].day), bars)
    after = market.judge(rung.judge(late, bars, ROOM, POUND), bars, YARDSTICK, up, POUND)
    assert after.answer is Answer.PASS and cut.days - after.days == 999


def test_each_day_of_a_trade_is_marked_at_its_close_and_the_days_sum_to_its_gain() -> None:
    bars = _bars(SHAPE)
    gbp = _judge(bars, 24).trades  #: 192 shares bought at 10.70 on bar 21, stopped on bar 23
    days = market.daily(gbp, bars, VUSA, POUND)
    paid = Decimal("2054.4")
    assert days == {
        bars[21].day: (192 * Decimal(11) - paid) / paid,
        bars[22].day: Decimal(0),
        bars[23].day: (Decimal("1797.12") - gbp[0].costs.total - 192 * Decimal(11)) / paid,
    }
    assert abs(sum(days.values()) - gbp[0].gain) < Decimal("1e-25")
    #: a dollar line is marked at each day's own rate, so the currency's move is in its days
    fills = {bars[21].day: Decimal("0.8"), bars[23].day: Decimal("0.75")}
    usd = _judge(bars, 24, "SPY", fills).trades
    with pytest.raises(ValueError, match=f"no rate of pounds per USD to price {bars[22].day}"):
        market.daily(usd, bars, SPY, fills)
    marked = market.daily(usd, bars, SPY, fills | {bars[22].day: Decimal("0.7")})
    assert marked[bars[22].day] == 240 * 11 * Decimal("-0.1") / paid, "the dollar fell a tenth"
    assert abs(sum(marked.values()) - usd[0].gain) < Decimal("1e-25")
    #: bought and stopped on one day: the whole gain is that day's
    (once,) = market.daily([replace(gbp[0], held=(bars[21].day,) * 2)], bars, VUSA, POUND).values()
    assert once == gbp[0].gain


def test_the_fit_is_the_least_squares_line_and_its_excess_is_judged_in_standard_errors() -> None:
    moves = [1.0, -1.0, 2.0, -2.0]  #: they sum to nothing, as does the noise, set square to them
    own = [2 * m + 0.5 + e for m, e in zip(moves, (0.25, 0.25, -0.25, -0.25), strict=True)]
    fit = market.fit(own, moves)
    assert (fit.beta, fit.excess) == (2.0, 0.5)
    assert math.isclose(fit.t, 0.5 / math.sqrt(0.125 / 4)), "0.25 squared, four times, over two"
    #: a market that is not flat on average takes its share of the doubt about the excess
    lifted = market.fit(own, [m + 1 for m in moves])
    assert (lifted.beta, lifted.excess) == (2.0, -1.5)
    assert math.isclose(lifted.t, -1.5 / math.sqrt(0.125 * (1 / 4 + 1 / 10)))
    with pytest.raises(ValueError, match="never moved"):
        market.fit(own, [1.0] * 4)
    with pytest.raises(ValueError, match="no spread"):
        market.fit([2 * m for m in moves], moves)


def test_what_cannot_be_the_market_it_took_is_refused() -> None:
    bars, up = _walk(0, 0.008), _rising(100)
    verdict = _judge(bars, -1)
    with pytest.raises(ValueError, match="SPY trades on US, VUSA on LSE"):
        market.judge(verdict, bars, SPY, up, POUND)
    hole = bars[2500].day
    with pytest.raises(ValueError, match=f"VUAG has no bar on {hole}"):
        market.judge(verdict, bars, YARDSTICK, up[:2500] + up[2501:], POUND)
    with pytest.raises(ValueError, match="did not make the verdict"):
        market.judge(verdict, bars[:-1], YARDSTICK, up, POUND)
    with pytest.raises(ValueError, match="never moved"):
        market.judge(verdict, bars, YARDSTICK, _bars([10] * 5000), POUND)
    #: a dollar market is read in pounds, each day at its own rate, on days nothing is held too
    dollars = {bar.day: Decimal("0.8") for bar in bars[2:]}
    with pytest.raises(ValueError, match=f"no rate of pounds per USD to price {bars[1].day}"):
        market.judge(_judge(bars, -1, "SPY", dollars), bars, SPY, up, dollars)
