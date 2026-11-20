"""The ladder on the pool (R-RUNNER-110): the rows are the serial run's, in its order; a
worker's break is that cell's row, and the set goes on."""

from __future__ import annotations

import os
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from test_lab_ladder import (  # noqa: F401 - eased_off is an autouse fixture
    AAPL,
    EDGE,
    ISF,
    NOISE,
    VUSA,
    _door,
    _rows,
    eased_off,
)
from test_lab_ladder import _set as _cells

from desk.lines import Line
from desk.store import Bar
from lab import folds, ladder, ladder_pool
from lab.batch import Bars

CLOCK = lambda: datetime(2026, 11, 14, tzinfo=UTC)  # noqa: E731


def _book() -> Bars:
    """What each worker makes for itself: two lines with bars, and one whose bars break."""
    held = _door({VUSA: EDGE, ISF: NOISE})

    def bars(line: Line) -> Sequence[Bar]:
        if line == AAPL:
            raise RuntimeError("a bug in the worker")
        return held(line)

    return bars


def test_the_pool_writes_the_serial_runs_rows_in_its_order_and_a_workers_break_is_a_row(
    tmp_path: Path,
) -> None:
    todo = [
        *_cells(VUSA, ISF),
        *(c.__class__("trend_50_200", c.line, c.start, c.end) for c in _cells(VUSA, ISF)),
    ]
    serial, pooled = tmp_path / "serial", tmp_path / "pool"
    ladder.run(serial, _book(), {}, todo, CLOCK)
    said = ladder_pool.run(pooled, _book, {}, todo, CLOCK, size=2)
    assert _rows(pooled) == _rows(serial) and "on 2 cores: 4 cells" in said
    again = ladder_pool.run(pooled, _book, {}, todo, CLOCK, size=2)
    assert "0 judged now, 4 kept from before" in again
    bug = [c.__class__("trend_50_200", AAPL, c.start, c.end) for c in _cells(AAPL)]
    broken = ladder_pool.run(tmp_path / "broken", _book, {}, [*bug, *_cells(VUSA)], CLOCK, size=2)
    bad, fine = _rows(tmp_path / "broken")
    assert bad["error"] == "RuntimeError: a bug in the worker" and "answer" in fine
    assert "1 judged now" in broken and "1 could not be judged" in broken


def test_a_unit_is_one_lines_one_fold_so_one_lines_history_spreads_over_the_workers(
    tmp_path: Path,
) -> None:
    (one,) = _cells(VUSA)
    cut = ladder_pool.units([one, *_cells(ISF)])
    assert len(cut) == 2 * (1 + folds.YEARS) and len({u for u in cut}) == len(cut)
    assert [y for c, y in cut if c == one] == [None, *range(2021, 2026)]  # five folds, one cell
    ladder_pool.run(tmp_path, _book, {}, [one], CLOCK, size=2)
    warmed = len(list((tmp_path / ladder.FOLDER / "tapes").glob("*.tape")))
    assert 1 <= warmed <= 2  # the line, and its market where reached: never a tape per fold


def test_a_stop_planted_after_the_first_unit_ends_the_pass_there_and_a_stale_one_changes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    todo = [
        *_cells(VUSA, ISF),
        *(c.__class__("trend_50_200", c.line, c.start, c.end) for c in _cells(VUSA, ISF)),
    ]
    serial = tmp_path / "serial"
    ladder.run(serial, _book(), {}, todo, CLOCK)
    stop = tmp_path / "pool" / ladder.FOLDER / ladder_pool.STOP
    stop.parent.mkdir(parents=True)
    stop.write_text("main moved")
    os.utime(stop, (1, 1))  # stale: older than the pass's start
    ladder_pool.run(tmp_path / "pool", _book, {}, todo, CLOCK, size=2)
    assert not stop.exists() and _rows(tmp_path / "pool") == _rows(serial)
    count, planted = ladder._count, list[int]()
    stop = tmp_path / "cut" / ladder.FOLDER / ladder_pool.STOP
    stop.parent.mkdir(parents=True)

    def plant(*args: Any) -> None:
        if not planted:
            planted.append(stop.write_text("main moved"))
        count(*args)

    monkeypatch.setattr(ladder, "_count", plant)
    said = ladder_pool.run(tmp_path / "cut", _book, {}, todo, CLOCK, size=2)
    assert said == "stopped after a unit: main moved" and not stop.exists()
    assert _rows(tmp_path / "cut") == _rows(serial)[:2]


GB = 2**30


def test_the_pool_is_sized_by_free_memory_beyond_a_reserve_of_a_fifth_and_never_below_one() -> None:
    assert ladder_pool.workers(64 * GB, 40 * GB, cores=8) == 5  #: (40 - 12.8) / 5, floored
    assert ladder_pool.workers(64 * GB, 60 * GB, cores=8) == 6  #: the cores' bound: 8 - 2
    assert ladder_pool.workers(64 * GB, 15 * GB, cores=8) == 1  #: only 2.2 GB beyond the reserve
    assert ladder_pool.workers(64 * GB, 2 * GB, cores=8) == 1  #: below the reserve: one
