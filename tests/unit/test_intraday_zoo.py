"""The zoo: twenty MACHINERY strategies, never edge, over every regime and the daily, 15-minute
and 5-minute bars, on the fixed lines of the master; each intraday rule on fixture bars, the
day-trader's sale before the close, and 15-minute bars rolled from the 5-minute store."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import ClassVar

from desk import bars, intraday, venues
from desk.grimes import GRIMES
from desk.intraday import ZOO, Regime, Span
from desk.lines import Line
from desk.rollup import Candle
from desk.spans import Five
from desk.strategy import STRATEGIES, Action

DAY, NEXT = date(2026, 11, 16), date(2026, 11, 17)
Row = tuple[float, float, float, float] | tuple[float, float, float, float, int]


def _session(day: date, rows: Sequence[Row], span: int = 5) -> list[Candle]:
    """Candles from the session's open, one per row of open, high, low, close (and volume)."""
    start, made = venues.hours("LSE", day).open, []
    for n, row in enumerate(rows):
        o, h, low, c = (Decimal(str(x)) for x in row[:4])
        volume = int(row[4]) if len(row) == 5 else 1
        made.append(Candle(start + timedelta(minutes=span * n), o, h, low, c, volume, "ibkr"))
    return made


def _flat(close: float) -> Row:
    return (close, close, close, close)


def _actions(name: str, candles: list[Candle]) -> list[Action]:
    machine = next(m for m in ZOO if m.name == name)
    rule = machine.rule()
    return [d.action for d in intraday.run(name, rule, "LSE", "X", candles)]  # type: ignore[arg-type]


def test_the_zoo_is_thirty_machines_over_every_regime_and_none_a_candidate() -> None:
    names = [m.name for m in ZOO]
    assert len(names) == 30 == len(set(names)) and all(n.startswith("zoo_") for n in names)
    assert [n for n in names if n.startswith("zoo_ag")] == [f"zoo_{n}" for n in GRIMES]
    assert not set(names) & (set(STRATEGIES) | set(intraday.RULES))
    assert {m.regime for m in ZOO} == set(Regime)
    fives = [m for m in ZOO if m.span is Span.FIVE_MINUTES]
    assert sum(m.regime is Regime.SCALP for m in fives) >= 4
    assert sum(m.regime is Regime.GAPPER for m in fives) >= 2
    assert {m.span for m in ZOO} == {None, Span.FIVE_MINUTES, Span.FIFTEEN_MINUTES}
    assert all(m.source for m in ZOO)


def test_the_zoo_trades_thirteen_plain_london_lines_and_every_us_security() -> None:
    lines = intraday.zoo_lines()
    london = [line for line in lines if line.venue == "LSE"]
    assert len(london) == 13 and all(line.leverage == 1 for line in london)
    #: the three plain inverse lines join by the zoo's own rule; LQQS, three times, stays out
    assert {"XSPS", "SUK1", "1MCS"} <= {ln.symbol for ln in london}
    us = [line for line in lines if line.venue == "US"]
    assert len(us) == 9 and all(line.isin for line in us)


def test_opening_range_breakout_buys_over_the_first_bar_and_sells_under_its_low() -> None:
    rows = [(10, 10.5, 9.5, 10), _flat(10.2), _flat(10.6), _flat(10.4), _flat(9.4)]
    got = _actions("zoo_opening_range_15m", _session(DAY, rows, 15))
    assert got == [Action.HOLD, Action.HOLD, Action.BUY, Action.HOLD, Action.SELL]


def test_gap_and_go_buys_only_a_session_opened_a_gap_up() -> None:
    before = _session(DAY, [_flat(100)])
    up = _session(NEXT, [(102, 103, 101.5, 102.5), _flat(102.8), _flat(103.5), _flat(101)])
    assert _actions("zoo_gap_and_go_5m", before + up)[1:] == [
        Action.HOLD,
        Action.HOLD,
        Action.BUY,
        Action.SELL,
    ]
    level = _session(NEXT, [(100.2, 103, 100, 102.5), _flat(103.5)])
    assert Action.BUY not in _actions("zoo_gap_and_go_5m", before + level)


def test_gap_fade_buys_a_gap_down_that_holds_and_sells_when_it_fills() -> None:
    before = _session(DAY, [_flat(100)])
    down = _session(NEXT, [(98, 98.6, 97.8, 98.4), _flat(99), _flat(100.1)])
    assert _actions("zoo_gap_fade_5m", before + down)[1:] == [
        Action.BUY,
        Action.HOLD,
        Action.SELL,
    ]


def test_vwap_reversion_buys_a_stretch_under_the_session_average_and_sells_at_it() -> None:
    rows: list[Row] = [(100, 100, 100, 100, 1000), (99, 99, 99, 99, 10), (100, 100, 100, 100, 10)]
    got = _actions("zoo_vwap_reversion_5m", _session(DAY, rows))
    assert got == [Action.HOLD, Action.BUY, Action.SELL]


def test_micro_pullback_buys_a_dip_to_the_fast_average_in_a_rising_session() -> None:
    rising: list[Row] = [_flat(100 + n) for n in range(25)]
    dip, crash = (124, 125, 115, 124.5), _flat(110)
    got = _actions("zoo_micro_pullback_5m", _session(DAY, [*rising, dip, crash]))
    assert got[:25] == [Action.HOLD] * 25 and got[25:] == [Action.BUY, Action.SELL]


def test_rsi2_scalp_buys_a_sharp_drop_in_an_up_session_and_sells_the_bounce() -> None:
    closes = [100, 101, 102, 99, 97, 93, 98, 103]
    rows = [(90, 100, 90, 100), *(_flat(c) for c in closes[1:])]
    got = _actions("zoo_rsi2_scalp_5m", _session(DAY, rows))
    assert got == [Action.HOLD] * 5 + [Action.BUY, Action.HOLD, Action.SELL]


def test_ema_cross_buys_the_cross_up_and_sells_the_cross_down() -> None:
    rows = [_flat(100)] * 21 + [_flat(101), _flat(102)] + [_flat(90)] * 3
    got = _actions("zoo_ema_cross_5m", _session(DAY, rows))
    assert got.index(Action.BUY) == 21 and Action.SELL in got[23:]


class _AlwaysIn:
    """Always wants to be in, a day-trader's rule."""

    span: ClassVar[Span] = Span.FIVE_MINUTES
    flat: ClassVar[bool] = True

    def step(self, bar: Candle, holding: bool) -> bool:
        return bar.volume >= 0 or holding  #: every bar has a volume: always in


def test_a_day_trader_is_sold_before_the_close_and_never_bought_after() -> None:
    close = venues.hours("LSE", DAY).close
    marks = [close - timedelta(minutes=m) for m in (15, 10, 5)]
    late = [Candle(t, Decimal(1), Decimal(1), Decimal(1), Decimal(1), 1, "ibkr") for t in marks]
    got = [d.action for d in intraday.run("in", _AlwaysIn(), "LSE", "X", late)]
    assert got == [Action.BUY, Action.SELL, Action.HOLD]


def test_fifteen_minute_bars_are_rolled_from_the_five_minute_store(tmp_path: Path) -> None:
    line, store = Line("X", "LSE", "GBP", 1), tmp_path / "bars.db"
    start = venues.hours("LSE", DAY).open
    fives = [
        Five(start + timedelta(minutes=5 * n), p, p, p, p, 1)
        for n, p in enumerate(Decimal(c) for c in (1, 2, 3, 4, 5, 6, 7))
    ]
    with bars.writing(store) as round_:
        round_.five(line, fives)
    got = intraday.session(store, line, Span.FIFTEEN_MINUTES, DAY)
    assert [(c.start, c.open, c.close, c.source) for c in got] == [
        (start, Decimal(1), Decimal(3), "rollup:5m"),
        (start + timedelta(minutes=15), Decimal(4), Decimal(6), "rollup:5m"),
    ]


def test_every_intraday_machine_runs_through_the_one_engine_on_a_fixture_session() -> None:
    assert len([m for m in ZOO if m.span is None]) == 23  #: the daily ones: strategy's engine
    for m in ZOO:
        if m.span is not None:
            candles = _session(DAY, [_flat(100 + n % 3) for n in range(20)], m.span.value)
            assert len(_actions(m.name, candles)) == 20


def test_a_session_missing_its_opening_bar_or_its_day_before_is_never_traded_as_one() -> None:
    rows = [(10, 10.5, 9.5, 10), _flat(10.2), _flat(10.6), _flat(10.4)]
    late = _session(DAY, rows, 15)[1:]  #: the store lost 08:00: 08:15 is not the open
    assert Action.BUY not in _actions("zoo_opening_range_15m", late)
    up = _session(NEXT, [(102, 103, 101.5, 102.5), _flat(103.5)])
    assert Action.BUY not in _actions("zoo_gap_and_go_5m", _session(DAY, [_flat(100)])[:1] + up[1:])
    friday = _session(date(2026, 11, 13), [_flat(100)])  #: Monday 16th lost: not the day before
    assert Action.BUY not in _actions("zoo_gap_and_go_5m", friday + up)


def test_each_day_trader_decides_today_alike_whatever_older_days_it_saw() -> None:
    older = _session(date(2026, 11, 13), [_flat(90 + n % 7) for n in range(30)])
    before = _session(DAY, [_flat(100 - n % 5) for n in range(30)])
    today = _session(NEXT, [(97, 99, 96, 98)] + [_flat(98 + (n * 7) % 9) for n in range(40)])
    for m in (m for m in ZOO if m.span is Span.FIVE_MINUTES):
        assert (
            _actions(m.name, older + before + today)[-41:] == _actions(m.name, before + today)[-41:]
        )


def test_a_us_half_day_sells_a_day_trader_before_its_early_close() -> None:
    hours = venues.hours("US", date(2026, 11, 27))  #: the day after Thanksgiving, shut early
    assert hours.early
    marks = [hours.close - timedelta(minutes=m) for m in (15, 10, 5)]
    late = [Candle(t, Decimal(1), Decimal(1), Decimal(1), Decimal(1), 1, "ibkr") for t in marks]
    assert [d.action for d in intraday.run("in", _AlwaysIn(), "US", "X", late)] == [
        Action.BUY,
        Action.SELL,
        Action.HOLD,
    ]
