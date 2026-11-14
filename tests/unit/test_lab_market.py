"""The market's rung: the edge judged against the market risk it took; a rule that only rides
its market fails, and a planted edge of its own passes."""

from __future__ import annotations

import math
import random
from dataclasses import replace
from decimal import Decimal

import pytest
from test_lab_rung import AAPL, POUND, SHAPE, _bars, _judge, _walk

from desk.lines import LINES, YARDSTICK
from desk.orders import Settings
from desk.store import Bar
from lab import cell, market, rung
from lab.cell import Cell
from lab.rung import Answer

ROOM = Settings(Decimal(100_000))  #: room for a share of a market that has risen a hundredfold
IDTL = next(line for line in LINES if line.symbol == "IDTL")
VUSA = _judge(_bars(SHAPE), 24).key.cell.line


def _rising(seed: int, days: int = 5000) -> tuple[Bar, ...]:
    """A market that climbs a tenth of 1% a day whatever came before: nothing to time."""
    rng, closes = random.Random(seed), [10.0]  # noqa: S311 - a repeatable test walk, not a secret
    while len(closes) < days:
        closes.append(closes[-1] * (1.001 + rng.gauss(0, 0.01)))
    return _bars(closes)


def _against(bars: tuple[Bar, ...], held: tuple[Bar, ...], end: int = -1) -> market.Against:
    return market.judge(_judge(bars, end, room=ROOM), bars, YARDSTICK, held, POUND)


def _t(found: market.Against) -> tuple[float, float]:
    assert found.line is not None and found.wide is not None
    return found.line.t, found.wide.t


def test_a_rule_that_only_rides_its_market_fails_and_an_edge_of_its_own_passes() -> None:
    for seed in (1, 2, 4, 5):  #: four markets whose rider the first rung passes
        up = _rising(seed + 100)  #: its own draws: the walks share none with it
        rider = _against(up, up)  #: the breakout on the rising market itself
        assert rider.verdict.passed, "it earned, after costs: the first rung passes it"
        assert max(_t(rider)) < 1 and rider.answer is Answer.FAIL, (seed, _t(rider))
        assert rider.wide is not None and 0.3 < rider.wide.beta < 0.9, "in it half its days"
        #: a line that climbs of itself beside a flat market: its rider beats the market by
        #: the line's own climb, and has still found nothing
        alone = _against(up, _walk(seed, 0))
        assert alone.verdict.passed and alone.answer is Answer.FAIL, seed
        assert _t(alone)[0] < 1 and _t(alone)[1] > 2.5, (seed, _t(alone))
        #: a planted edge is its own: in for the line's rises and out for the rest
        edge = _against(_walk(seed, 0.008), up)
        assert edge.answer is Answer.PASS and min(_t(edge)) > 2.5, (seed, _t(edge))
        assert edge.wide is not None and abs(edge.wide.beta) < 0.05 and 4900 < edge.days <= 4999
        none = _against(_walk(seed, 0), up)
        assert none.answer is Answer.FAIL and max(_t(none)) < 1, (seed, _t(none))
        #: too few trades are not enough evidence here either, and nothing is measured
        few = _against(_walk(seed, 0)[:1500], up)
        assert (few.answer, few.line, few.wide, few.days) == (Answer.THIN, None, None, 0)
    #: the bar sits between these two, and the lesser of the two excesses is the one judged
    faint, just = (
        _against(_walk(24, 0.0035), _rising(100)),
        _against(_walk(27, 0.004), _rising(100)),
    )
    assert _t(faint)[0] > 2.1 and 1.97 < _t(faint)[1] < 2 and faint.answer is Answer.FAIL
    assert 2 < min(_t(just)) < max(_t(just)) < 2.05 and just.answer is Answer.PASS
    none = _against(_bars(SHAPE), _rising(0), 23)
    assert none.answer is Answer.FAULT, "no trade: a fault in the test"


def test_a_trade_not_judged_ends_the_days_counted_on_the_day_it_was_bought() -> None:
    bars, up = _walk(0, 0.008), _rising(100)

    def trades(n: int, start: int = 0) -> tuple[cell.Trade, ...]:
        return cell.run(Cell("breakout_20_10", "VUSA", bars[start].day, bars[n].day), bars).trades

    #: still held at the window's end, and sold on its last day with no morning after to fill
    held = next(n for n in range(4000, 5000) if trades(n)[-1].sold is None)
    sold = next(n for n in range(4000, 5000) if trades(n)[-1].sold == bars[n].day)
    for end in (held, sold):
        cut = _against(bars, up, end)
        assert cut.verdict.trades[-1].trade == trades(end)[-2], "the last trade is not judged"
        assert bars[cut.days].day == trades(end)[-1].bought, "bar 0 moves from nothing"
    #: the days before a window's start warm the rule, and are not counted
    late = cell.run(Cell("breakout_20_10", "VUSA", bars[1000].day, bars[sold].day), bars)
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
    usd = _judge(bars, 24, "AAPL", fills).trades
    with pytest.raises(ValueError, match=f"no rate of pounds per USD to price {bars[22].day}"):
        market.daily(usd, bars, AAPL, fills)
    marked = market.daily(usd, bars, AAPL, fills | {bars[22].day: Decimal("0.7")})
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
    with pytest.raises(ValueError, match="AAPL trades on US, VUSA on LSE"):
        market.judge(verdict, bars, AAPL, up, POUND)
    hole = bars[2500].day
    with pytest.raises(ValueError, match=f"VUAG has no bar on {hole}"):
        market.judge(verdict, bars, YARDSTICK, up[:2500] + up[2501:], POUND)
    with pytest.raises(ValueError, match="did not make the verdict"):
        market.judge(verdict, bars[:-1], YARDSTICK, up, POUND)
    with pytest.raises(ValueError, match="never moved"):
        market.judge(verdict, bars, YARDSTICK, _bars([10] * 5000), POUND)
    #: a dollar market is read in pounds at each day's own rate, whatever the line's currency
    with pytest.raises(ValueError, match=f"IDTL: no rate of pounds per USD to price {bars[0].day}"):
        market.judge(verdict, bars, IDTL, up, POUND)
