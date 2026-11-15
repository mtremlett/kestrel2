"""The ladder on the pool (R-RUNNER-110): the rows are the serial run's, in its order; a
worker's break is that cell's row, and the set goes on."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from test_lab_ladder import AAPL, EDGE, ISF, NOISE, VUSA, _door, _rows
from test_lab_ladder import _set as _cells

from desk.lines import Line
from desk.store import Bar
from lab import ladder, ladder_pool
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
