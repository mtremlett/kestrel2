"""The old database's daily rows enter the fast store: the daily rows alone, a fresh day wins and
a disagreement is said, and a second run adds nothing."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import numpy as np
import pyarrow as pa  # type: ignore[import-untyped]  # ships no stubs
import pyarrow.parquet as pq  # type: ignore[import-untyped]  # ships no stubs
import pytest

from desk import bars, venues
from desk.bars import Source
from desk.lines import Line
from desk.store import Bar
from lab import headstart_days

BA = Line("BA", "US", "USD", 1)
DAYS = venues.sessions("US", date(2026, 8, 3), date(2026, 11, 12))
TODAY = date(2026, 11, 13)
SHAPE = "(ticker, timeframe, ts, open, high, low, close, volume)"


def _row(ticker: str, frame: str, day: date, close: float) -> tuple[object, ...]:
    return ticker, frame, f"{day}T00:00:00+00:00", close - 1, close + 1, close - 2, close, 9


def _old(path: Path) -> None:
    daily = [_row("BA", "1d", day, 100 + n) for n, day in enumerate(DAYS)]
    daily.append(_row("BA", "5m", DAYS[0], 555))  # intraday: not a daily row
    with closing(sqlite3.connect(path)) as made:
        for table in ("ohlcv", "ohlcv_quarantine", "ohlcv_unit_drift_backup"):
            made.execute(f"CREATE TABLE {table} {SHAPE}")
        made.executemany("INSERT INTO ohlcv VALUES (?,?,?,?,?,?,?,?)", daily)
        bad = [_row("BA", "1d", date(2026, 7, 1), 999), _row("BA", "1d", DAYS[3], 999)]
        for table in ("ohlcv_quarantine", "ohlcv_unit_drift_backup"):
            made.executemany(f"INSERT INTO {table} VALUES (?,?,?,?,?,?,?,?)", bad)  # noqa: S608  # fixed names
        made.commit()


def _fresh(day: date, close: str) -> Bar:
    c = Decimal(close)
    return Bar(day, c - 1, c + 1, c - 2, c, 9)


def test_the_daily_rows_alone_enter_a_fresh_day_wins_and_a_second_run_adds_nothing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    old, path = tmp_path / "old.db", tmp_path / "market.db"
    _old(old)
    held = [_fresh(day, str(100 + n)) for n, day in enumerate(DAYS) if n >= len(DAYS) - 5]
    held[0] = _fresh(held[0].day, str(Decimal(held[0].close) + Decimal("0.5")))  # they disagree
    with bars.writing(path) as round_:
        round_.daily(BA, held)
    said = headstart_days.main(old, path, [BA], TODAY)
    kept = {bar.day: bar for bar in bars.daily(path, BA)}
    assert set(kept) == set(DAYS)  # no quarantined day, and no 5m row read as a day
    assert kept[held[0].day] == held[0]  # the fresh one stays
    assert kept[DAYS[10]].close == Decimal(110)
    assert bars.sources(path, BA, bars.DAILY) == {
        Source.ARCHIVE: 5,
        Source.MTT_DB: len(DAYS) - 5,
    }
    assert f"BA: {len(DAYS) - 5} days filled from {DAYS[0]}" in said
    assert "1 of 5 days held differ" in said
    assert headstart_days.main(old, path, [BA], TODAY) == "BA: already in"
    assert capsys.readouterr().out.count("BA:") == 2


def _stooq(folder: Path, scale: float) -> None:
    """stooq_store's daily file of BA: every session, one row spoilt, prices times scale."""
    file = folder / "freq=d/market=us/ticker=BA.US/part.parquet"
    file.parent.mkdir(parents=True)
    at = [datetime(d.year, d.month, d.day) for d in DAYS]
    close = [(100 + n) * scale for n in range(len(DAYS))]
    state = ["SPIKE-REVERSAL" if n == 3 else "OK" for n in range(len(DAYS))]
    prices = dict.fromkeys(("open", "high", "low", "close"), close)
    cols = {"ts": at, **prices, "volume": [9] * len(at)}
    pq.write_table(pa.table({**cols, "row_state": state}), file)


def test_stooq_stores_daily_rows_enter_under_their_source_but_not_adjusted_ones(
    tmp_path: Path,
) -> None:
    held = [_fresh(day, str(100 + n)) for n, day in enumerate(DAYS) if n >= len(DAYS) - 30]
    path = tmp_path / "market.db"
    with bars.writing(path) as round_:
        round_.daily(BA, held)
    _stooq(tmp_path / "adjusted", 0.8)
    _stooq(tmp_path / "traded", 1)
    said = headstart_days.main(tmp_path / "adjusted", path, [BA], TODAY)
    assert "refused" in said
    assert "the one store would park it" in said
    assert headstart_days.main(tmp_path / "traded", path, [BA], TODAY).startswith("BA: ")
    assert bars.sources(path, BA, bars.DAILY)[Source.STOOQ_DAILY] == len(DAYS) - 30 - 1
    assert DAYS[3] not in {bar.day for bar in bars.daily(path, BA)}  # the spoilt row stays out


def test_ibkr_stores_daily_rows_enter_under_the_brokers_source(tmp_path: Path) -> None:
    folder, path = tmp_path / "ibkr", tmp_path / "market.db"
    _stooq(folder, 1)
    (folder / "freq=d/market=us/ticker=BA.US/fetch.json").write_text("{}", encoding="utf-8")
    with bars.writing(path) as round_:
        round_.daily(
            BA, [_fresh(d, str(100 + n)) for n, d in enumerate(DAYS) if n >= len(DAYS) - 5]
        )
    assert headstart_days.main(folder, path, [BA], TODAY).startswith("BA: ")
    assert bars.sources(path, BA, bars.DAILY)[Source.IBKR_DAILY] == len(DAYS) - 6
    assert headstart_days.main(folder, path, [BA], TODAY) == "BA: already in"


def test_the_matrices_daily_arrays_enter_under_their_source_and_a_hole_is_left(
    tmp_path: Path,
) -> None:
    folder, path = tmp_path / "matrix", tmp_path / "market.db"
    folder.mkdir()
    stamps = [
        int((datetime(d.year, d.month, d.day) - datetime(1970, 1, 1)).total_seconds() * 1000)
        for d in DAYS
    ]
    close = np.array([100.0 + n for n in range(len(DAYS))])
    table = np.array([close - 1, close + 1, close - 2, close, np.full(len(DAYS), 9.0)])
    table[3, 3] = np.nan  # a hole: that day has no bar
    np.save(folder / "BA.US_1d_ts.npy", np.array(stamps))
    np.save(folder / "BA.US_1d_ohlcv.npy", table)
    with bars.writing(path) as round_:
        round_.daily(
            BA, [_fresh(d, str(100 + n)) for n, d in enumerate(DAYS) if n >= len(DAYS) - 5]
        )
    said = headstart_days.main(folder, path, [BA], TODAY)
    assert f"BA: {len(DAYS) - 6} days filled from {DAYS[0]}" in said
    assert bars.sources(path, BA, bars.DAILY) == {
        Source.ARCHIVE: 5,
        Source.MATRIX_DAILY: len(DAYS) - 6,
    }
    assert headstart_days.main(folder, path, [BA], TODAY) == "BA: already in"
