"""The ladder's first rung: a cell's trades filled at the next open, sized by the desk, priced
under the broker's own schedule; a planted edge passes and a planted non-edge does not."""

from __future__ import annotations

import math
import random
from collections.abc import Sequence
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal

import pytest

from desk.orders import BROKER, Settings
from desk.store import Bar
from lab import cell, rung
from lab.cell import Cell, Trade

TEN_K, POUND = Settings(Decimal(10_000)), Decimal(1)
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


def _walk(seed: int, push: float, days: int = 5000) -> tuple[Bar, ...]:
    """A random walk pulled gently back towards 10; a push is a planted edge, added to each
    day after a close over the 20 before it, so a breakout is followed by a rise."""
    rng, closes = random.Random(seed), [10.0]  # noqa: S311 - a repeatable test walk, not a secret
    while len(closes) < days:
        up = len(closes) > 20 and closes[-1] > max(closes[-21:-1])
        pull = 0.005 * math.log(closes[-1] / 10)
        closes.append(closes[-1] * (1 + rng.gauss(0, 0.01) + (push if up else 0) - pull))
    return _bars(closes)


def _judge(
    bars: tuple[Bar, ...],
    last: int,
    symbol: str = "VUSA",
    fx: Decimal = POUND,
    room: Settings = TEN_K,
) -> rung.Verdict:
    record = cell.run(Cell("breakout_20_10", symbol, bars[0].day, bars[last].day), bars)
    return rung.judge(record, bars, room, fx)


def test_a_trade_is_sized_at_its_close_filled_at_the_next_open_and_stopped_by_the_broker() -> None:
    bars = _bars(SHAPE)
    (gbp,) = _judge(bars, 24).trades  #: 192 shares sized at 10.40, filled at bar 21's 10.70
    assert gbp.trade == Trade(bars[20].day, bars[23].day)
    assert (gbp.shares, gbp.paid) == (192, Decimal("2057.4")), "192 x 10.70 + £3"
    #: bar 23's low of 9.353 reaches the stop 10% under 10.40, so it sells there, not at 9.40
    assert gbp.received == Decimal("1794.12"), "192 x 9.36 - £3"
    assert (gbp.gross, gbp.costs) == (Decimal("-257.28"), Decimal(6))
    assert gbp.gain == Decimal("-263.28") / Decimal("2057.4")
    (usd,) = _judge(bars, 24, "SPY", Decimal("0.8")).trades
    #: paid (2568 + 1.2) x 0.8 x 1.0003; back 2246.4 x 0.8 x 2 less (2246.4 + 1.2) x 0.8 x 1.0003
    assert (usd.shares, usd.paid) == (240, Decimal("2055.976608"))
    assert (usd.received, usd.gross) == (Decimal("1795.620576"), Decimal("-257.28"))
    assert _judge(bars, 23).trades == _judge(bars, 22).trades == (), "sold on the last day, or held"
    assert _judge(bars, 24).broker == BROKER


def test_a_planted_edge_passes_and_a_planted_non_edge_does_not() -> None:
    for seed in range(8):
        edge, none = _judge(_walk(seed, 0.008), -1), _judge(_walk(seed, 0), -1)
        assert edge.passed and len(edge.trades) >= rung.MIN_TRADES, (seed, edge.t)
        assert not none.passed and none.t is not None and none.t < 1, (seed, none.t)
    #: the bar sits between these two: 1.98 standard errors fails, 2.14 passes
    faint, just = _judge(_walk(5, 0.005), -1), _judge(_walk(27, 0.006), -1)
    assert faint.t is not None and Decimal("1.9") < faint.t < rung.T_PASS and not faint.passed
    assert just.t is not None and just.t < Decimal("2.14") and just.passed
    #: and between these: 29 trades are too few, however strong, and 30 enough
    short, thirty = _judge(_walk(0, 0.008)[:2400], -1), _judge(_walk(0, 0.008)[:2450], -1)
    assert len(short.trades) == 29 and short.t is not None and short.t > 3 and not short.passed
    assert len(thirty.trades) == 30 and thirty.passed


def test_an_edge_the_costs_eat_is_rejected() -> None:
    #: at £500, a holding is £100 and the £3 least commission on each leg is 6% of it
    eaten = _judge(_walk(0, 0.008), -1, room=Settings(Decimal(500)))
    before = rung.standard_errors([p.gross / p.paid for p in eaten.trades])
    assert before is not None and before > 3 and eaten.t is not None and eaten.t < 0


def test_the_mean_is_judged_in_standard_errors_of_the_sample() -> None:
    assert (
        rung.standard_errors([Decimal(1), Decimal(2), Decimal(3)]) == Decimal(12).sqrt()
    ), "2 over the root of 1 / 3"
    assert rung.standard_errors([Decimal(1)]) is None
    with pytest.raises(ValueError, match="no spread"):
        rung.standard_errors([Decimal(1), Decimal(1)])


def test_a_record_is_judged_only_on_the_bars_that_made_it() -> None:
    bars = _bars(SHAPE)
    record = cell.run(Cell("breakout_20_10", "VUSA", bars[0].day, bars[24].day), bars)
    with pytest.raises(ValueError, match="did not make the record"):
        rung.judge(record, (replace(bars[0], close=Decimal(9)),) + bars[1:], TEN_K, POUND)
