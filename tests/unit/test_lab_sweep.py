"""The grid's pass: every strategy on every ticker of a list, a ticker to a worker under the
auto-tune, each cell kept by its code and its bars, and only what changed run again."""

from __future__ import annotations

import os
from collections.abc import Sequence
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from test_lab_tune import Pc

from desk import store, strategy, venues
from desk.lines import STAMP_DUTY, Line
from desk.store import Bar
from lab import batch, cell, sweep, universe

DAY = date(2026, 11, 13)
START = DAY - timedelta(200)
SATURDAY = datetime(2026, 11, 14, 12, tzinfo=UTC)
BOEING, BAE = Line("BA", "US", "USD", 1), Line("BA", "LSE", "GBP", 1, STAMP_DUTY)
ABSENT = Line("NONE", "US", "USD", 1)  #: on the list, with no bars in the store
FATAL = Line("FATAL", "US", "USD", 1)  #: the ticker whose worker dies
LINES = (BOEING, ABSENT, BAE)
EACH = len(strategy.STRATEGIES)


def _keep(root: Path, line: Line, lift: int = 0, split: int = 0) -> None:
    """A line's bars cleaned into the store at root: a slow wave, so rules trade on it, its
    first `split` bars at ten times the price, as before a split nobody adjusted."""
    days = venues.sessions(line.venue, START, DAY - timedelta(1))
    up = [n % 40 if n % 80 < 40 else 40 - n % 40 for n in range(len(days))]
    wave = [Decimal(100 + lift + step) * (10 if n < split else 1) for n, step in enumerate(up)]
    bars = [Bar(d, p, p + 1, p - 1, p, 9) for d, p in zip(days, wave, strict=True)]
    assert bool(store.prepare(root / line.venue, {line: bars}, DAY)) == bool(split)


def _dying(root: Path, kept: Path, start: date, end: date, lines: Sequence[Line]) -> None:
    """A worker's work, its process ending dead two cells into the fatal ticker."""
    for line in lines:
        if line == FATAL:
            kept.joinpath(line.venue).mkdir(parents=True, exist_ok=True)
            none = dict[Line, Sequence[Bar]]().__getitem__  # no bars: each cell fails
            batch.run(sweep.cells(line, start, end)[:2], none, sweep.journal(kept, line))
            os._exit(3)
        sweep.work(root, kept, start, end, [line])


def _pass(tmp_path: Path, lines: Sequence[Line] = LINES) -> sweep.Pass:
    pc, folders = Pc(tmp_path), (tmp_path / "store", tmp_path / "kept")
    return sweep.run(lines, *folders, START, DAY, pc, tmp_path, 2, lambda: SATURDAY)


def test_every_strategy_on_every_ticker_is_kept_and_only_what_changed_is_run_again(
    tmp_path: Path,
) -> None:
    root, kept = tmp_path / "store", tmp_path / "kept"
    _keep(root, BOEING)
    _keep(root, BAE, lift=50, split=30)  # parked by the store, and studied all the same
    first = _pass(tmp_path)
    assert (first.cells, first.ran, first.failed) == (3 * EACH, 2 * EACH, EACH)
    assert (first.kept, first.undone, first.report.died) == (0, 0, ())
    for line in (BOEING, BAE):  # the two companies called BA, each from its own venue's bars
        bars = universe.read(root, line).bars  # research's reading: none before a split
        assert len(bars) == len(store.read(root / line.venue, "BA")) - 30 * (line == BAE)
        cells = sweep.cells(line, START, DAY)
        assert [c.strategy for c in cells] == list(strategy.STRATEGIES)
        held = batch.run(cells, {line: bars}.__getitem__, sweep.journal(kept, line))
        assert held == tuple(cell.run(c, bars) for c in cells)
        assert any(record.trades for record in held if isinstance(record, cell.Record))
        assert len(batch.rows(sweep.journal(kept, line))) == EACH, "a kept cell was run again"
    errors = {row["error"] for row in batch.rows(sweep.journal(kept, ABSENT))}
    assert len(errors) == 1 and errors.pop().startswith("FileNotFoundError")

    with sweep.journal(kept, BOEING).open("ab") as cut:
        cut.write(b'{"cell": ["breakout_20_10", "BA')  # a line a stop cut short
    again = _pass(tmp_path)  # nothing changed: only the failed cells are tried again
    assert (again.ran, again.kept, again.failed, again.undone) == (0, 2 * EACH, EACH, 0)
    _keep(root, BAE, lift=60)  # one ticker's bars mended: its cells alone are run again
    third = _pass(tmp_path)
    assert (third.ran, third.kept, third.failed, third.undone) == (EACH, EACH, EACH, 0)


def test_a_ticker_whose_worker_dies_is_named_and_the_rest_are_kept(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _keep(tmp_path / "store", BOEING)
    _keep(tmp_path / "store", BAE)
    monkeypatch.setattr(sweep, "work", _dying)
    done = _pass(tmp_path, (BOEING, ABSENT, FATAL, BAE))  # one batch, halved twice
    assert done.report.died == (FATAL,) and done.report.batches == 5
    assert (done.cells, done.ran, done.kept, done.failed) == (4 * EACH, 2 * EACH, 0, EACH + 2)
    assert len(batch.rows(sweep.journal(tmp_path / "kept", ABSENT))) == 2 * EACH  # tried twice
    assert done.undone == EACH - 2, "the dead ticker's cells with no outcome are counted so"


def test_a_backward_window_or_a_ticker_listed_twice_runs_no_pass(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="ends before it starts"):
        sweep.run(LINES, tmp_path, tmp_path, DAY, START, Pc(tmp_path), tmp_path, 8)
    with pytest.raises(ValueError, match="more than once: BA on LSE"):
        _pass(tmp_path, (BOEING, BAE, BAE))
    assert not (tmp_path / "autotune.json").exists()
