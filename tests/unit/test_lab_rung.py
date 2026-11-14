"""The ladder's first rung: a cell's trades filled at the next open, sized by the desk, priced
under the broker's own schedule; a planted edge passes and a planted non-edge does not."""

from __future__ import annotations

import math
import random
from collections.abc import Sequence
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from desk import book
from desk.broker import Pretend
from desk.lines import LINES
from desk.orders import BROKER, Charges, Order, Settings
from desk.store import Bar
from lab import cell, rung
from lab.cell import Cell, Trade
from lab.rung import Answer

TEN_K, ZERO = Settings(Decimal(10_000)), Decimal(0)
POUND: rung.Rates = {}  #: a pound line reads no rate
FREE = Charges(ZERO, ZERO, ZERO, ZERO, ZERO)
AAPL = next(line for line in LINES if line.symbol == "AAPL")
#: breakout_20_10 buys on the close of bar 20, over bar 19's high of 10.05, and sells on the
#: close of bar 23, under the low of 9.95 ten days before
SHAPE = [10] * 20 + [10.4, 11, 11, 9.4, 9.4]


def _bars(closes: Sequence[float]) -> tuple[Bar, ...]:
    """Each bar opens halfway from the close before it, its range half a percent beyond both."""
    bars, last = [], Decimal(str(closes[0]))
    for n, value in enumerate(closes):
        close = Decimal(f"{value:.2f}")
        high, low = max(last, close) * Decimal("1.005"), min(last, close) * Decimal("0.995")
        bars.append(Bar(date(2010, 1, 1) + timedelta(n), (last + close) / 2, high, low, close, 1))
        last = close
    return tuple(bars)


def _walk(seed: int, *pushes: float, days: int = 5000) -> tuple[Bar, ...]:
    """A random walk pulled gently back towards 10; each push is a planted edge for its stretch
    of days, added to each day after a close over the 20 before it: a breakout, then a rise."""
    rng, closes = random.Random(seed), [10.0]  # noqa: S311 - a repeatable test walk, not a secret
    while len(closes) < days * len(pushes):
        up = len(closes) > 20 and closes[-1] > max(closes[-21:-1])
        pull = 0.005 * math.log(closes[-1] / 10)
        push = pushes[len(closes) // days] if up else 0
        closes.append(closes[-1] * (1 + rng.gauss(0, 0.01) + push - pull))
    return _bars(closes)


def _judge(
    bars: Sequence[Bar],
    end: int,
    symbol: str = "VUSA",
    rates: rung.Rates = POUND,
    room: Settings = TEN_K,
) -> rung.Verdict:
    record = cell.run(Cell("breakout_20_10", symbol, bars[0].day, bars[end].day), bars)
    return rung.judge(record, bars, room, rates)


def test_a_trade_is_sized_at_its_close_filled_at_the_next_open_and_stopped_by_the_broker(
    tmp_path: Path,
) -> None:
    bars = _bars(SHAPE)
    (gbp,) = _judge(bars, 24).trades  #: 192 shares sized at 10.40, filled at bar 21's 10.70
    assert gbp.trade == Trade(bars[20].day, bars[23].day)
    assert gbp.held == (bars[21].day, bars[23].day), "filled the next morning; stopped on bar 23"
    assert (gbp.shares, gbp.paid) == (192, Decimal("2054.4")), "192 x 10.70"
    #: bar 23's low of 9.353 reaches the stop 10% under 10.40, so it sells there, not at 9.40
    assert (gbp.received, gbp.gross) == (Decimal("1797.12"), Decimal("-257.28")), "192 x 9.36"
    #: a leg: £3, and a twentieth of 1% for half the spread; as much slips, thrice at the stop
    assert gbp.costs == Charges(Decimal(6), Decimal("1.92576"), Decimal("3.72288"), ZERO, ZERO)
    assert gbp.gain == Decimal("-268.92864") / Decimal("2054.4")
    #: sold by the rule at the next open of 9.90, clear of the stop: a sale slips once
    (ruled,) = _judge(_bars([*SHAPE[:23], 9.9, 9.9]), 24).trades
    assert (ruled.received, ruled.costs.slippage) == (Decimal("1900.8"), Decimal("1.9776"))
    assert ruled.held == (bars[21].day, bars[24].day), "sold at the open after the rule's sell"
    #: but an open of 8.95, under the stop resting at 9.36, is the stop's sale and slips thrice
    (gapped,) = _judge(_bars([*SHAPE[:23], 9.9, 8]), 24).trades
    assert (gapped.received, gapped.costs.slippage) == (Decimal("1718.4"), Decimal("3.6048"))
    #: a dollar line: sized at the rate of the morning it is sent, each fill at its own day's
    days, dear, cheap = (bars[21].day, bars[23].day), Decimal("0.8"), Decimal("0.75")
    rates = dict(zip(days, (dear, cheap), strict=True))
    (usd,) = _judge(bars, 24, "AAPL", rates).trades
    assert (usd.shares, usd.paid, usd.received) == (240, Decimal("2054.4"), Decimal("1684.8"))
    assert usd.gross == Decimal("-369.6"), "the dollar's fall is in it: 240 x 9.36 x 0.05 more"
    #: bought: 0.96 + 1.0272 + 1.0272 + 0.616608 to convert; stopped: 0.96980688 with the US
    #: sale's own fees + 0.8424 + 2.5272 + 0.505149057936
    assert usd.costs.total == Decimal("8.475563937936")
    assert _judge(bars, 24, "AAPL", rates | {days[0]: Decimal("0.4")}).trades[0].shares == 480
    #: the desk's own book prices the same two fills to the same pounds and the same costs
    broker = Pretend({AAPL: bars[21:24]}, {})
    broker.open(bars[21].day)
    stop = Decimal("9.36")
    broker.place(Order("20100121-breakout_20_10-AAPL", AAPL, 240, Decimal("10.4"), dear, stop))
    for bar in bars[22:24]:
        broker.open(bar.day)
    book.collect(tmp_path, broker)
    for on, rate in rates.items():
        book.record_rates(tmp_path, on, {"USD": rate})
    (trip,) = book.round_trips(tmp_path, [AAPL])
    assert (trip.gross, trip.costs, trip.sell.price) == (usd.gross, usd.costs, stop)
    for needed in rates:  #: a rate not given, or not a number above nothing, is refused
        bad: tuple[dict[date, Decimal], ...] = (
            {},
            {needed: ZERO},
            {needed: -dear},
            {needed: Decimal("NaN")},
        )
        for wrong in bad:
            given = {d: rate for d, rate in rates.items() if d != needed} | wrong
            with pytest.raises(
                ValueError, match=f"AAPL: no rate of pounds per USD to price {needed}"
            ):
                _judge(bars, 24, "AAPL", given)
    assert _judge(bars, 23).trades == _judge(bars, 22).trades == (), "sold on the last day, or held"
    #: no trades at all is a fault in the test, and says nothing of the rule
    assert (_judge(bars, 23).answer, _judge(bars, 23).t) == (Answer.FAULT, None)
    assert (_judge(bars, 24).answer, _judge(bars, 24).t) == (Answer.THIN, None), "one trade"
    assert _judge(bars, 24).broker == BROKER


def test_a_planted_edge_passes_and_a_planted_non_edge_does_not() -> None:
    for seed in range(8):
        edge, none = _judge(_walk(seed, 0.008), -1), _judge(_walk(seed, 0), -1)
        assert edge.answer is Answer.PASS and len(edge.trades) >= rung.MIN_TRADES, (seed, edge.t)
        assert none.answer is Answer.FAIL and none.t is not None and none.t < 1, (seed, none.t)
        #: the same loser on too few trades has not failed: there is not enough evidence
        few = _judge(_walk(seed, 0)[:1500], -1)
        assert 2 <= len(few.trades) < rung.MIN_TRADES and few.answer is Answer.THIN, seed
        assert not few.passed and few.t is not None and few.t < 1, (seed, few.t)
    #: the bar sits between these two: 1.98 standard errors fails, 2.02 passes
    faint, just = _judge(_walk(12, 0.005), -1), _judge(_walk(40, 0.005), -1)
    assert faint.t is not None and Decimal("1.9") < faint.t < rung.T_PASS
    assert faint.answer is Answer.FAIL and not faint.passed
    assert just.t is not None and just.t < Decimal("2.03") and just.passed
    #: and between these: 29 trades are not enough evidence, however strong, and 30 are
    short, thirty = _judge(_walk(0, 0.008)[:2400], -1), _judge(_walk(0, 0.008)[:2450], -1)
    assert len(short.trades) == 29 and short.t is not None and short.t > Decimal("2.5")
    assert not short.passed and short.answer is Answer.THIN
    assert len(thirty.trades) == 30 and thirty.passed


def test_one_more_trade_is_planted_at_the_rules_own_stop_and_is_no_trade_counted() -> None:
    made = _judge(_walk(0, 0.008), -1)
    assert all(p.stopped < p.gain and p.stopped < 0 for p in made.trades)
    assert made.gains[-1] == min(p.stopped for p in made.trades)
    assert made.gains[:-1] == tuple(p.gain for p in made.trades), "the trades' own gains, unmoved"
    assert len(made.gains) == len(made.trades) + 1 and rung.planted([]) == ()


def test_an_edge_the_costs_eat_is_rejected() -> None:
    #: at £500, a holding is £100 and the £3 least commission on each leg is 6% of it
    eaten = _judge(_walk(0, 0.008), -1, room=Settings(Decimal(500)))
    before = rung.standard_errors([p.gross / p.paid for p in eaten.trades])
    assert before is not None and before > 3 and eaten.t is not None and eaten.t < 0


def test_the_mean_is_judged_in_standard_errors_of_the_sample() -> None:
    three = rung.standard_errors([Decimal(1), Decimal(2), Decimal(3)])
    assert three == Decimal(12).sqrt(), "2 over the root of 1 / 3"
    assert rung.standard_errors([Decimal(1)]) is None
    with pytest.raises(ValueError, match="no spread"):
        rung.standard_errors([Decimal(1), Decimal(1)])


def test_a_record_is_judged_only_on_the_bars_that_made_it() -> None:
    bars = _bars(SHAPE)
    record = cell.run(Cell("breakout_20_10", "VUSA", bars[0].day, bars[24].day), bars)
    with pytest.raises(ValueError, match="did not make the record"):
        rung.judge(record, (replace(bars[0], close=Decimal(9)),) + bars[1:], TEN_K, POUND)
