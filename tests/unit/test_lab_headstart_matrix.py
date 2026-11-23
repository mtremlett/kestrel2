"""The old Stooq matrices' 15-minute, 30-minute and hourly arrays enter by their start in UTC,
vouched for by their day, under their own source; a second run adds nothing."""

from __future__ import annotations

import sqlite3
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import numpy as np

from desk import bars
from desk.bars import Source
from desk.lines import Line
from desk.store import Bar
from lab import headstart_hours, headstart_matrix

LONDON = Line("BA", "LSE", "GBP", 1)
DAY = date(2026, 10, 20)  # British Summer Time: London's 08:00 is 09:00 on Stooq's clock


def _write(folder: Path, span: str, hours: list[int], high: list[int]) -> None:
    """Arrays of one span: stamps in milliseconds on Stooq's clock, five rows of numbers."""
    base = datetime(1970, 1, 1)
    ms = [int((datetime(2026, 10, 20, h) - base).total_seconds() * 1000) for h in hours]
    n = len(hours)
    rows = [[100] * n, high, [99] * n, [100] * n, [9] * n]
    np.save(folder / f"BA.UK_{span}_ts.npy", np.array(ms, dtype=np.int64))
    np.save(folder / f"BA.UK_{span}_ohlcv.npy", np.array(rows, dtype=float))


def test_matrix_spans_enter_by_their_start_vouched_by_their_day_and_a_second_run_adds_nothing(
    tmp_path: Path,
) -> None:
    old, path = tmp_path, tmp_path / "market_live.db"
    _write(old, "30m", [9, 10], [101, 500])  # starts; the second beyond its day's range
    _write(old, "1h", [10, 11, 12], [101, 101, 101])  # ends: the hours 09, 10, 11 on Stooq's clock
    day = Bar(DAY, Decimal(100), Decimal(105), Decimal(95), Decimal(100), 9)
    with bars.writing(path) as round_:
        round_.daily(LONDON, [day])
    said = headstart_hours.main(old, path, [LONDON], headstart_matrix.one)
    assert said == (
        "BA: 15m not held; 1 30m bars filled; 1 not vouched, 0 faults;"
        " 3 1h bars filled; 0 not vouched, 0 faults"
    )
    start = datetime(2026, 10, 20, tzinfo=UTC), datetime(2026, 10, 22, tzinfo=UTC)
    assert [b.start.hour for b in bars.timed(path, LONDON, "1h", *start)] == [7, 8, 9]
    assert [b.start.hour for b in bars.timed(path, LONDON, "30m", *start)] == [7]
    assert bars.sources(path, LONDON, "1h") == {Source.MATRIX_INTRADAY: 3}
    again = headstart_hours.main(old, path, [LONDON], headstart_matrix.one)
    assert "15m not held; 30m already in; 1h already in" in again


def test_the_whole_pass_lands_the_matrices_daily_and_intraday_bars_each_under_its_source(
    tmp_path: Path,
) -> None:
    old, path = tmp_path / "stooq_store_matrix", tmp_path / "market_live.db"
    old.mkdir()
    for span, hours in ("1d", [0]), ("30m", [9]), ("1h", [10]):
        _write(old, span, hours, [101] * len(hours))
    with bars.writing(path) as round_:  # the archive's day, which vouches for the hours
        round_.daily(LONDON, [Bar(DAY, Decimal(100), Decimal(105), Decimal(95), Decimal(100), 9)])
    register = tmp_path / "register.md"
    register.write_text(f"| IMPORT | `{old}` |\n", encoding="utf-8")
    first = headstart_matrix.whole(register, path, [LONDON], DAY)
    assert first == "stooq_store_matrix: filled 2, refused 1, differ 0"
    assert bars.sources(path, LONDON, "30m") == {Source.MATRIX_INTRADAY: 1}
    assert bars.sources(path, LONDON, "1h") == {Source.MATRIX_INTRADAY: 1}
    again = headstart_matrix.whole(register, path, [LONDON], DAY)
    assert again == "stooq_store_matrix: filled 0, refused 1, differ 0"


def test_the_old_database_timeframes_enter_on_their_marks_and_the_rest_are_refused(
    tmp_path: Path,
) -> None:
    old, path = tmp_path / "old.db", tmp_path / "market_live.db"
    with sqlite3.connect(old) as db:
        db.execute("CREATE TABLE ohlcv (ticker, timeframe, ts, open, high, low, close, volume)")
        for span, at in ("1h", "07:00"), ("1h", "07:30"), ("1wk", "00:00"):
            day = "2026-10-23" if span == "1wk" else "2026-10-20"  # a Friday week
            db.execute(
                "INSERT INTO ohlcv VALUES ('BA.L', ?, ?, 100, 101, 99, 100, 9)",
                (span, f"{day}T{at}:00+00:00"),
            )
    with bars.writing(path) as round_:
        round_.daily(LONDON, [Bar(DAY, Decimal(100), Decimal(105), Decimal(95), Decimal(100), 9)])
    said = headstart_hours.main(old, path, [LONDON], headstart_matrix.trend)
    assert "1h 1 bars filled" not in said and "1 1h bars filled" in said
    assert said.count("1 off its marks refused") == 2  # the :30 hour and the Friday week
    assert bars.sources(path, LONDON, "1h") == {Source.DATABASE: 1}
    assert "1h already in" in headstart_hours.main(old, path, [LONDON], headstart_matrix.trend)
