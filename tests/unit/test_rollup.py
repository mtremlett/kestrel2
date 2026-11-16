"""The roll-up: coarser bars built from 1m bars, hand-worked, aligned to the session open."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from desk.rollup import Candle, rollup

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
