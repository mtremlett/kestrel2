"""The intraday engine: a five-minute rule decides the same in the backtest and in the desk's
step at each bar, cannot see a later bar, and the session and span are held to."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import ClassVar

import pytest

from desk import bars, intraday, venues
from desk.intraday import Span
from desk.lines import Line
from desk.rollup import Candle
from desk.spans import Five
from desk.strategy import Action

CLOSES = [10, 9, 8, 9, 10, 11, 10, 9, 10, 12, 11, 8]


class _Dip:
    """Buys a close under 9, sells a close over 10."""

    span: ClassVar[Span] = Span.FIVE_MINUTES

    def step(self, bar: Candle, holding: bool) -> bool:
        return bar.close <= 10 if holding else bar.close < 9


def _candle(start: datetime, close: int) -> Candle:
    price = Decimal(close)
    return Candle(start, price, price, price, price, 1, "ibkr")


def _bars(closes: list[int], day: date = date(2026, 11, 16)) -> list[Candle]:
    start = venues.hours("LSE", day).open
    return [_candle(start + timedelta(minutes=5 * n), c) for n, c in enumerate(closes)]


def _backtest(bars: list[Candle]) -> list[Action]:
    return [d.action for d in intraday.run("dip", _Dip(), "LSE", "X", bars)]


def test_the_step_at_each_bar_matches_the_backtest_and_is_future_blind() -> None:
    bars = _bars(CLOSES)
    whole = _backtest(bars)
    assert whole.count(Action.BUY) == 2 and whole.count(Action.SELL) == 1
    held = False
    for n, action in enumerate(whole):
        step = intraday.latest("dip", _Dip, "LSE", "X", bars[: n + 1], held)
        assert step.action == action and step.at == bars[n].start
        held = action is Action.BUY or (held and action is not Action.SELL)


@pytest.mark.parametrize("shift", [timedelta(hours=-1), timedelta(hours=9), timedelta(0)])
def test_a_bar_outside_the_session_or_out_of_order_is_refused(shift: timedelta) -> None:
    bars = _bars(CLOSES[:3])
    bars = [_candle(b.start + shift, 1) for b in bars] if shift else [bars[1], bars[0]]
    with pytest.raises(ValueError, match="not"):
        _backtest(bars)


def test_the_last_bar_must_end_inside_the_session() -> None:
    close = venues.hours("LSE", date(2026, 11, 16)).close
    late = _candle(close - timedelta(minutes=2), 1)
    with pytest.raises(ValueError, match="5-minute"):
        _backtest([late])


def test_today_reads_the_position_from_the_book_and_trades_no_rule_by_default() -> None:
    bars = {"X": _bars(CLOSES[:3]), "Y": []}
    assert intraday.today("LSE", bars, {}) == ()
    rules = {"dip": _Dip}
    assert [d.action for d in intraday.today("LSE", bars, {}, rules)] == [Action.BUY]
    assert [d.action for d in intraday.today("LSE", bars, {"X": "dip"}, rules)] == [Action.HOLD]


def test_a_session_reads_only_its_own_bars_and_a_span_never_held_is_refused(tmp_path: Path) -> None:
    day, line, store = date(2026, 11, 16), Line("X", "LSE", "GBP", 1), tmp_path / "bars.db"
    marks = [venues.hours("LSE", day).open + timedelta(minutes=m) for m in (-5, 0, 5, 10, 1440)]
    prices = [Decimal(c) for c in CLOSES[:5]]
    with bars.writing(store) as round_:
        round_.five(line, [Five(t, p, p, p, p, 1) for t, p in zip(marks, prices, strict=True)])
    got = intraday.session(store, line, Span.FIVE_MINUTES, day)
    assert [(c.start, c.close) for c in got] == list(zip(marks[1:4], prices[1:4], strict=True))
    rules, hand = {"d": _Dip}, _bars(CLOSES[1:4], day)
    assert intraday.today("LSE", {"X": got}, {}, rules) == intraday.today(
        "LSE", {"X": hand}, {}, rules
    )
    with pytest.raises(LookupError):
        intraday.session(store, line, Span.ONE_MINUTE, day)
