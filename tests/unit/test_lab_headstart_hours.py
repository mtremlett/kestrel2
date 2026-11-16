"""The old Stooq store's hourly bars enter the history database: named by their start in UTC
(Stooq stamps the hour's end), under their own source, an unvouched or spoilt one left and
counted, and a second run adding nothing."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import pyarrow as pa  # type: ignore[import-untyped]  # ships no stubs
import pyarrow.parquet as pq  # type: ignore[import-untyped]  # ships no stubs

from desk import bars
from desk.bars import Source
from desk.lines import Line
from desk.store import Bar
from lab import headstart_hours

LONDON = Line("BA", "LSE", "GBP", 1)
DAY = date(2026, 10, 20)  # British Summer Time: London's 08:00 is 07:00 UTC, 09:00 on Stooq's clock


def _old(folder: Path) -> None:
    """Hourly rows stamped by their end on Stooq's clock: three good, one spoilt, one beyond its
    day's range, and one on a day with no daily bar."""
    file = folder / "freq=h/market=uk/ticker=BA.UK/part.parquet"
    file.parent.mkdir(parents=True)
    ends = [datetime(2026, 10, 20, h) for h in (10, 11, 12, 13, 14)] + [datetime(2026, 10, 21, 10)]
    high = [101, 101, 101, 101, 500, 101]
    state = ["OK", "OK", "OK", "SPIKE-REVERSAL", "OK", "OK"]
    cols = {"ts": ends, "open": [100] * 6, "high": high, "low": [99] * 6, "close": [100] * 6}
    pq.write_table(pa.table({**cols, "volume": [9] * 6, "row_state": state}), file)


def test_hourly_bars_enter_by_their_start_under_their_source_and_a_second_run_adds_nothing(
    tmp_path: Path,
) -> None:
    old, path = tmp_path / "old", tmp_path / "market_live.db"
    _old(old)
    day = Bar(DAY, Decimal(100), Decimal(105), Decimal(95), Decimal(100), 9)
    with bars.writing(path) as round_:
        round_.daily(LONDON, [day])
    said = headstart_hours.main(old, path, [LONDON])
    assert said == "BA: 3 hours filled; 2 not vouched, 0 faults"  # the spoilt row was never read
    got = bars.timed(
        path, LONDON, "1h", datetime(2026, 10, 20, tzinfo=UTC), datetime(2026, 10, 22, tzinfo=UTC)
    )
    assert [bar.start.hour for bar in got] == [7, 8, 9]
    assert bars.sources(path, LONDON, "1h") == {Source.STOOQ_HOURLY: 3}
    assert bars.sources(path, LONDON, bars.DAILY) == {Source.ARCHIVE: 1}
    assert headstart_hours.main(old, path, [LONDON]) == "BA: already in"
    other = Line("ZZ", "LSE", "GBP", 1)
    assert "ZZ: refused: ticker=ZZ.UK holds no hourly bar" in headstart_hours.main(
        old, path, [other]
    )
