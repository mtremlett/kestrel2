"""The roll-up: coarser bars built from 1m bars, hand-worked, aligned to the session open."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from desk.rollup import Candle, merged, rollup, weekly

OPEN = datetime(2026, 11, 16, 8, 0, tzinfo=UTC)  # a London Monday in winter: 08:00 to 16:30


def minute(n: int, price: int | None = None) -> Candle:
    """The 1m bar n minutes after the open: open n, high n+2, low n-1, close n+1, volume 10."""
    p = Decimal(n if price is None else price)
    return Candle(OPEN + timedelta(minutes=n), p, p + 2, p - 1, p + 1, 10, "ibkr")


def test_five_minute_bars_are_worked_by_hand() -> None:
    got = rollup("LSE", [minute(n) for n in range(10)], "5m")
    assert [(c.start, c.open, c.high, c.low, c.close, c.volume, c.source) for c in got] == [
        (OPEN, Decimal(0), Decimal(6), Decimal(-1), Decimal(5), 50, "rollup:1m"),
        (
            OPEN + timedelta(minutes=5),
            Decimal(5),
            Decimal(11),
            Decimal(4),
            Decimal(10),
            50,
            "rollup:1m",
        ),
    ]


def test_a_gap_or_a_partial_interval_is_not_written() -> None:
    held = [minute(n) for n in range(13) if n != 3]  # 08:03 missing; 08:10-08:12 part-built
    assert [c.start for c in rollup("LSE", held, "5m")] == [OPEN + timedelta(minutes=5)]


def test_no_bar_crosses_the_session_break() -> None:
    day = [minute(n) for n in range(510)]  # the whole 8h30 session
    assert [c.start for c in rollup("LSE", day, "4h")] == [OPEN, OPEN + timedelta(hours=4)]
    last = rollup("LSE", day, "1h")[-1]  # 16:00-17:00 would pass the 16:30 close
    assert last.start == OPEN + timedelta(hours=7)
    assert len(rollup("LSE", day, "30m")) == 17
    assert rollup("LSE", [minute(-5), minute(600)], "5m") == []  # before the open, after the close


def day(d: int, price: int) -> Candle:
    """The daily bar of November d 2026: open price, high price+5, low price-3, close price+1."""
    p = Decimal(price)
    return Candle(datetime(2026, 11, d, tzinfo=UTC), p, p + 5, p - 3, p + 1, 100, "stooq")


def test_weekly_bars_need_every_session_of_the_week() -> None:
    week = [day(16 + i, 10 * (i + 1)) for i in range(5)]
    got = weekly("LSE", week + [day(23, 7), day(24, 7)])  # the second week is only part-held
    assert [(c.start, c.open, c.high, c.low, c.close, c.volume, c.source) for c in got] == [
        (
            datetime(2026, 11, 16, tzinfo=UTC),
            Decimal(10),
            Decimal(55),
            Decimal(7),
            Decimal(51),
            500,
            "rollup:1d",
        )
    ]
    assert weekly("LSE", week[:3] + week[4:]) == []  # Thursday missing


def test_a_pulled_bar_wins_over_a_rolled_one_and_a_disagreement_is_a_fault() -> None:
    built = rollup("LSE", [minute(n) for n in range(15)], "5m")  # 08:00, 08:05, 08:10
    same = replace(built[0], source="ibkr")
    off = Candle(built[1].start, Decimal(5), Decimal(12), Decimal(4), Decimal(10), 50, "yf")
    kept, faults = merged([same, off], built)
    assert [(c.start, c.source) for c in kept] == [
        (OPEN, "ibkr"),
        (OPEN + timedelta(minutes=5), "yf"),
        (OPEN + timedelta(minutes=10), "rollup:1m"),
    ]
    assert faults == [(off, built[1])]  # the agreeing pulled bar is no fault
