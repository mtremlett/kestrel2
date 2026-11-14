"""The grid's pass: every strategy on every ticker of a list, a ticker to a worker under the
auto-tune, each cell kept by its code and its bars, and only what changed run again."""

from __future__ import annotations

import itertools
import os
import sys
from collections.abc import Sequence
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from functools import partial
from pathlib import Path
from typing import Any

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


def _pass(
    tmp_path: Path, lines: Sequence[Line] = LINES, clock: Any = lambda: SATURDAY
) -> sweep.Pass:
    pc, folders = Pc(tmp_path), (tmp_path / "store", tmp_path / "kept")
    return sweep.run(lines, *folders, START, DAY, pc, tmp_path, 2, clock)


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
    (root / "US" / "BA.csv").rename(root / "US" / "away")  # and another's cannot be read
    third = _pass(tmp_path)
    assert (third.ran, third.kept, third.failed, third.undone) == (EACH, 0, 2 * EACH, 0)
    (root / "US" / "away").rename(root / "US" / "BA.csv")  # back as they were: found kept
    fourth = _pass(tmp_path)
    assert (fourth.ran, fourth.kept, fourth.failed, fourth.undone) == (0, 2 * EACH, EACH, 0)
    assert len(batch.rows(sweep.journal(kept, ABSENT))) == EACH, "a failure was written again"


def test_a_ticker_whose_worker_dies_is_named_and_the_rest_are_kept(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _keep(tmp_path / "store", BOEING)
    _keep(tmp_path / "store", BAE)
    monkeypatch.setattr(sweep, "work", _dying)
    done = _pass(tmp_path, (BOEING, ABSENT, FATAL, BAE))  # one batch, halved twice
    assert done.report.died == (FATAL,) and done.report.batches == 5
    assert (done.cells, done.ran, done.kept, done.failed) == (4 * EACH, 2 * EACH, 0, EACH + 2)
    assert len(batch.rows(sweep.journal(tmp_path / "kept", ABSENT))) == EACH  # written once
    assert done.undone == EACH - 2, "the dead ticker's cells with no outcome are counted so"
    again = _pass(tmp_path, (FATAL,))  # it fails the same way and dies: no line is written
    assert (again.failed, again.undone, again.report.died) == (0, EACH, (FATAL,))


def test_a_backward_window_or_a_ticker_listed_twice_runs_no_pass(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="ends before it starts"):
        sweep.run(LINES, tmp_path, tmp_path, DAY, START, Pc(tmp_path), tmp_path, 8)
    with pytest.raises(ValueError, match="more than once: BA on LSE"):
        _pass(tmp_path, (BOEING, BAE, BAE))
    assert not (tmp_path / "autotune.json").exists()


def test_a_second_pass_on_a_folder_a_pass_holds_is_refused_in_this_process_or_another(
    tmp_path: Path,
) -> None:
    def second() -> datetime:  # the first pass's clock: asked while it holds the folder
        with pytest.raises(RuntimeError, match="another pass is at work"):
            _pass(tmp_path)
        ticks, folders = itertools.count(), (tmp_path / "store", tmp_path / "kept", tmp_path)
        if not (tmp_path / sweep.WEEK).exists():  # an hour's week: one pass, forty minutes in
            clock = lambda: SATURDAY + timedelta(minutes=40) * next(ticks)  # noqa: E731
            sweep.week(partial(sweep.fresh, *folders), tmp_path, 1 / 24, clock, lambda _: None)
        return SATURDAY

    assert _pass(tmp_path, (ABSENT,), second).failed == EACH
    row = batch.rows(tmp_path / sweep.WEEK)[-1]  # the week's one pass, the real command: refused
    refused = "RuntimeError: another pass is at work" if sys.platform == "win32" else "OSError"
    assert row["error"].startswith(refused) and row["started"] < row["ended"]
    assert sweep.unbroken(tmp_path) == timedelta(0)


def test_a_week_is_pass_after_pass_and_its_log_shows_how_long_without_stopping(
    tmp_path: Path,
) -> None:
    now, waits = [SATURDAY], list[float]()

    def once() -> dict[str, Any]:
        n = len(batch.rows(tmp_path / sweep.WEEK))
        now[0] += timedelta(minutes=200 if n == 9 else 5)  # one pass takes over three hours
        idle = {"ran": 0, "kept": 0, "failed": 9}  # a pass that ends holding no cell
        return (
            {"error": "OSError: no store"} if n == 100 else idle if n == 30 else {**idle, "ran": 1}
        )

    def wait(seconds: float) -> None:
        waits.append(seconds)
        now[0] += timedelta(seconds=seconds)

    sweep.week(once, tmp_path, 2, lambda: now[0], wait)
    assert now[0] == SATURDAY + timedelta(days=2), "the week waited on after its last pass"
    assert sweep.unbroken(tmp_path) == timedelta(hours=31, minutes=25)  # up to the idle pass
    now[0] += timedelta(hours=1)  # the PC off for an hour, then the week started again
    sweep.week(once, tmp_path, 3, lambda: now[0], wait)
    rows = batch.rows(tmp_path / sweep.WEEK)
    assert rows[0] == {
        "started": SATURDAY.isoformat(),
        "ended": (SATURDAY + timedelta(minutes=5)).isoformat(),
        **{"ran": 1, "kept": 0, "failed": 9},
    }
    assert (len(rows), rows[100]["error"]) == (118, "OSError: no store")
    assert waits[8:11] == [55 * 60, 0, 55 * 60], "a pass starts on the hour, or as the last ends"
    assert rows[10]["started"] == rows[9]["ended"]
    # an idle pass, an hour off, the longest run of all, a failed pass, then the last
    assert sweep.unbroken(tmp_path) == timedelta(hours=53, minutes=5)
