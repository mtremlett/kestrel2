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

from desk import bars as database
from desk import strategy, venues
from desk.bars import Source
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


def _keep(root: Path, line: Line, lift: int = 0, split: int = 0, path: Path | None = None) -> None:
    """A line's bars cleaned into the store at root, and all but the last into the history
    database beside it (or at path): a slow wave, so rules trade on it, its first `split`
    bars at ten times the price, as before a split nobody adjusted."""
    days = venues.sessions(line.venue, START, DAY - timedelta(1))
    up = [n % 40 if n % 80 < 40 else 40 - n % 40 for n in range(len(days))]
    wave = [Decimal(100 + lift + step) * (10 if n < split else 1) for n, step in enumerate(up)]
    bars = [Bar(d, p, p + 1, p - 1, p, 9) for d, p in zip(days, wave, strict=True)]
    with database.writing(path or root.parent / database.LIVE, Source.ARCHIVE) as opened:
        opened.daily(line, bars[:-1])


def _dying(
    root: Path, kept: Path, start: date, end: date, lines: Sequence[Line], transfer: bool
) -> None:
    """A worker's work, its process ending dead two cells into the fatal ticker."""
    for line in lines:
        if line == FATAL:
            kept.joinpath(line.venue).mkdir(parents=True, exist_ok=True)
            none = dict[Line, Sequence[Bar]]().__getitem__  # no bars: each cell fails
            batch.run(sweep.cells(line, start, end, transfer)[:2], none, sweep.journal(kept, line))
            os._exit(3)
        sweep.work(root, kept, start, end, [line], transfer)


def _pass(
    tmp_path: Path,
    lines: Sequence[Line] = LINES,
    clock: Any = lambda: SATURDAY,
    transfer: bool = True,
) -> sweep.Pass:
    pc, folders = Pc(tmp_path), (tmp_path / database.LIVE, tmp_path / "kept")
    return sweep.run(lines, *folders, START, DAY, pc, tmp_path, 2, clock, transfer)


def test_every_strategy_on_every_ticker_is_kept_and_only_what_changed_is_run_again(
    tmp_path: Path,
) -> None:
    root, kept = tmp_path / "store", tmp_path / "kept"
    _keep(root, BOEING)
    _keep(root, BAE, lift=50, split=30)  # parked by the store, and studied all the same
    ticks = itertools.count()
    first = _pass(tmp_path, clock=lambda: SATURDAY + timedelta(seconds=next(ticks)))
    assert first.seconds > 0, "the pass's own time is measured, for the weekend it must fit"
    assert (first.cells, first.ran, first.failed) == (3 * EACH, 2 * EACH, EACH)
    assert (first.kept, first.undone, first.report.died) == (0, 0, ())
    for line in (BOEING, BAE):  # the two companies called BA, each from its own venue's bars
        bars = universe.read(tmp_path / database.LIVE, line).bars  # none before a split
        days = len(venues.sessions(line.venue, START, DAY - timedelta(1)))
        assert len(bars) == days - 1 - 30 * (line == BAE)  # the last day is never written
        cells = sweep.cells(line, START, DAY, transfer=True)
        assert [c.strategy for c in cells] == list(strategy.STRATEGIES)
        held = batch.run(cells, {line: bars}.__getitem__, sweep.journal(kept, line))
        assert held == tuple(cell.run(c, bars) for c in cells)
        assert any(record.trades for record in held if isinstance(record, cell.Record))
        assert len(batch.rows(sweep.journal(kept, line))) == EACH, "a kept cell was run again"
    errors = {row["error"] for row in batch.rows(sweep.journal(kept, ABSENT))}
    assert len(errors) == 1 and errors.pop().startswith("FileNotFoundError")
    assert [(why.split(":")[0], n) for why, n in first.why] == [("FileNotFoundError", EACH)]
    assert sweep.summary(first)["why"] == [list(pair) for pair in first.why]  # the log names it

    with sweep.journal(kept, BOEING).open("ab") as cut:
        cut.write(b'{"cell": ["breakout_20_10", "BA')  # a line a stop cut short
    again = _pass(tmp_path)  # nothing changed: only the failed cells are tried again
    assert (again.ran, again.kept, again.failed, again.undone) == (0, 2 * EACH, EACH, 0)
    _keep(root, BAE, lift=60)  # one ticker's bars mended: its cells alone are run again
    with database.writing(tmp_path / database.LIVE, Source.ARCHIVE) as opened:
        gone = [b.day for b in database.daily(tmp_path / database.LIVE, BOEING)]
        opened.daily(BOEING, (), withdrawn=gone)  # and another's cannot be read
    third = _pass(tmp_path)
    assert (third.ran, third.kept, third.failed, third.undone) == (EACH, 0, 2 * EACH, 0)
    _keep(root, BOEING)  # back as they were: found kept
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
        sweep.run(LINES, tmp_path, tmp_path, DAY, START, Pc(tmp_path), tmp_path, 8, transfer=True)
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
        if not (tmp_path / sweep.WEEK).exists():  # an hour's week: one pass, seventy minutes long
            clock = lambda: SATURDAY + timedelta(minutes=70) * next(ticks)  # noqa: E731
            sweep.week(partial(sweep.fresh, *folders), tmp_path, 1 / 24, clock, lambda _: None)
        return SATURDAY

    assert _pass(tmp_path, (ABSENT,), second).failed == EACH
    (row,) = batch.rows(tmp_path / sweep.WEEK)  # the week's one pass, the real command: refused
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
        if n == 100:  # a pass that raises is logged, and the week carries on
            raise OSError("no store")
        return idle if n == 30 else {**idle, "ran": 1}

    def wait(seconds: float) -> None:
        waits.append(seconds)
        now[0] += timedelta(seconds=seconds)

    sweep.week(once, tmp_path, 2, lambda: now[0], wait)
    # its last pass is the first to end two days in, and the week does not wait on after it
    assert now[0] == SATURDAY + timedelta(days=2, minutes=25)
    assert sweep.unbroken(tmp_path) == timedelta(hours=31, minutes=25)  # up to the idle pass
    now[0] += timedelta(hours=2)  # the PC off for two hours, then the week started again
    sweep.week(once, tmp_path, 3, lambda: now[0], wait)
    rows = batch.rows(tmp_path / sweep.WEEK)
    assert rows[0] == {
        "started": SATURDAY.isoformat(),
        "ended": (SATURDAY + timedelta(minutes=5)).isoformat(),
        **{"ran": 1, "kept": 0, "failed": 9},
    }
    assert (len(rows), rows[100]["error"]) == (120, "OSError: no store")
    assert waits[8:11] == [55 * 60, 0, 55 * 60], "a pass starts on the hour, or as the last ends"
    assert rows[10]["started"] == rows[9]["ended"]
    # an idle pass, two hours off, the longest run of all, a failed pass, then the last
    assert sweep.unbroken(tmp_path) == timedelta(hours=52, minutes=5)
    (clean := tmp_path / "clean").mkdir()  # a week nothing stops shows its whole length
    sweep.week(lambda: {"ran": 1, "kept": 0}, clean, 7, lambda: now[0], wait)
    assert sweep.unbroken(clean) == timedelta(days=7)
    late = sweep.fresh(clean, clean, clean, timedelta(milliseconds=1))  # a pass past its limit
    assert late == {"error": "TimeoutExpired: ended at its limit of 0:00:00.001000"}


def test_held_is_every_ticker_the_store_has_bars_for_the_list_or_not(tmp_path: Path) -> None:
    other = Line("ZZZZ", "LSE", "GBP", 1, STAMP_DUTY)
    root = tmp_path / "store"
    for line in (BOEING, BAE, other):
        (root / line.venue).mkdir(parents=True, exist_ok=True)
        (root / line.venue / f"{line.symbol}.csv").write_text("day\n")
    assert sweep.held(root) == (BAE, other, BOEING)
    assert sweep.held(root)[0] is next(x for x in universe.UNIVERSE if x == BAE)


def test_a_pass_leaves_one_thread_free_when_london_is_shut_and_two_in_its_session() -> None:
    cores = os.cpu_count() or 2
    assert sweep.workers(SATURDAY) == max(1, cores - 1)
    assert sweep.workers(datetime(2026, 11, 13, 12, tzinfo=UTC)) == max(1, cores - 2)


def test_each_strategy_is_judged_on_its_declared_universe_and_the_transfer_study_on_all() -> None:
    mine = strategy.STRATEGIES["trend_50_200"].declared.universe[0]
    assert len(sweep.declared()) == len(set(sweep.declared()))
    assert mine in sweep.declared() and BOEING not in sweep.declared()
    names = [c.strategy for c in sweep.cells(mine, START, DAY)]
    assert names == [*strategy.STRATEGIES, *strategy.VARIANTS]
    assert sweep.cells(BOEING, START, DAY) == ()  # declared by none: no verdict is made there
    assert len(sweep.cells(BOEING, START, DAY, transfer=True)) == EACH


def test_a_variants_held_positions_are_the_desks_decisions_at_its_settings(
    tmp_path: Path,
) -> None:
    _keep(tmp_path / "store", BOEING)
    bars = universe.read(tmp_path / database.LIVE, BOEING).bars
    name = "bollinger_pullback[width=1.5]"
    said = strategy.decide({BOEING.symbol: bars}, {"bollinger_pullback": {"width": Decimal("1.5")}})
    held: list[bool] = []
    for d in (d for d in said if d.strategy == "bollinger_pullback"):
        was = held[-1] if held else False
        held.append({strategy.Action.BUY: True, strategy.Action.SELL: False}.get(d.action, was))
    assert any(held) and cell._held(cell.Cell(name, BOEING, START, DAY), bars) == held
