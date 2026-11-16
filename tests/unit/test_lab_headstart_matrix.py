"""The old Stooq matrices' 15-minute, 30-minute and hourly arrays enter by their start in UTC,
vouched for by their day, under their own source; a second run adds nothing."""

from __future__ import annotations

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
