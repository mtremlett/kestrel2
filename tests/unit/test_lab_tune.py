"""The pass's auto-tune: a ceiling on the workers' memory that Windows itself holds, workers
sized to the free cores and backed off under load, a dead worker's batch carried on."""

from __future__ import annotations

import json
import multiprocessing
import os
import sys
import time
from collections.abc import Callable, Sequence
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from functools import partial
from multiprocessing.process import BaseProcess
from pathlib import Path

import pytest

from desk import strategy
from desk.lines import LINES, Line
from desk.store import Bar
from lab import batch, tune
from lab.cell import Cell

GB = 1 << 30
SMALL = 400 * (1 << 20)  #: a ceiling for the proof: 400 MB for the one worker of two threads
SATURDAY = datetime(2026, 11, 14, 12, tzinfo=UTC)
START = date(2020, 1, 1)
SHAPE = [10] * 20 + [10.4, 11, 11, 9.4, 9.4]
BARS = tuple(
    Bar(START + timedelta(n), p, p + Decimal("0.5"), p - Decimal("0.5"), p, 1)
    for n, p in enumerate(Decimal(str(value)) for value in SHAPE)
)
SPY, QQQ = (next(line for line in LINES if line.symbol == s) for s in ("SPY", "QQQ"))


class Pc:
    """A 64 GB PC whose free memory and load are given; it keeps what the pass asked of it."""

    def __init__(self, data: Path, free: float = 0.9, busy: float = 0.1) -> None:
        self.data, self.free, self.busy = data, free, busy
        self.limits, self.held, self.flags, self.closed = (0, 0), list[str](), list[str](), False

    def memory(self) -> tuple[int, int]:
        if (self.data / tune.FLAG).exists():
            self.flags.append((self.data / tune.FLAG).read_text(encoding="utf-8"))
        return 64 * GB, int(64 * GB * self.free)

    def load(self) -> tuple[float, float]:
        return self.busy, 0.0

    def limit(self, job: int, process: int) -> None:
        self.limits = (job, process)

    def hold(self, worker: BaseProcess) -> None:
        self.held.append(worker.name)

    def spent(self, worker: BaseProcess) -> int:
        assert worker.exitcode == 0, "only a worker that finished its batch is measured"
        return self.limits[1] // 4  # so a batch of twice the cells fills half a share

    def peak(self) -> int:
        return 3 * GB

    def close(self) -> None:
        self.closed = True


def _ticking(start: datetime, by: timedelta) -> Callable[[], datetime]:
    times = (start + by * n for n in range(10**6))
    return lambda: next(times)


def _mark(folder: Path, cells: Sequence[str]) -> None:
    """A worker's work: each cell marked done; the cell called fatal ends its worker dead."""
    for name in cells:
        if name == "fatal":
            os._exit(3)
        time.sleep(600 if name == "stuck" else 0)
        (folder / name).write_text("done", encoding="utf-8")


def _study(folder: Path, cells: Sequence[Cell]) -> None:
    """A worker's real work: a batch of cells, where reading QQQ's bars wants a gigabyte."""

    def bars(line: Line) -> Sequence[Bar]:
        hungry = bytearray(GB if line == QQQ else 1)
        return BARS[: len(BARS) * len(hungry)]

    batch.run(cells, bars, folder / "journal.jsonl")


@pytest.mark.parametrize(
    ("now", "left"),
    [
        (datetime(2026, 11, 13, 8, 0, tzinfo=UTC), 2),  # a Friday, as London opens
        (datetime(2026, 11, 13, 20, 59, tzinfo=UTC), 2),  # New York's last minute
        (datetime(2026, 11, 13, 21, 0, tzinfo=UTC), 1),  # overnight
        (datetime(2026, 11, 13, 7, 59, tzinfo=UTC), 1),
        (datetime(2026, 7, 1, 7, 30, tzinfo=UTC), 2),  # 08:30 on a UK clock in summer
        (datetime(2026, 7, 1, 20, 30, tzinfo=UTC), 1),  # 21:30 on a UK clock in summer
        (SATURDAY, 1),  # a weekend
        (datetime(2026, 8, 31, 12, tzinfo=UTC), 2),  # London's holiday, New York trading
        (datetime(2026, 4, 3, 12, tzinfo=UTC), 1),  # Good Friday: both shut
    ],
)
def test_two_threads_are_left_free_in_market_hours_and_one_otherwise(
    now: datetime, left: int
) -> None:
    assert tune.spare(now) == left


@pytest.mark.parametrize(
    ("allowed", "most", "free", "busy", "ours", "then"),
    [
        (3, 6, 0.50, 0.40, 0.375, 4),  # room: one more
        (6, 6, 0.50, 0.75, 0.75, 6),  # never above what the cores allow
        (6, 6, 0.24, 0.10, 0.10, 5),  # short of memory: one fewer
        (1, 6, 0.10, 0.99, 0.10, 1),  # never fewer than one
        (7, 7, 0.50, 0.875, 0.875, 7),  # the workers' own load is no reason to back off
        (7, 7, 0.50, 1.00, 0.75, 6),  # other programs crowd the PC: one fewer
        (5, 7, 0.50, 0.80, 0.55, 5),  # others busy and no room for one more: hold
        (4, 7, 0.50, 0.70, 0.45, 5),  # others busy, yet room for one more
        (7, 6, 0.50, 0.30, 0.30, 6),  # the markets open: down to the day's number
    ],
)
def test_workers_back_off_under_load_and_step_back_up_with_room(
    allowed: int, most: int, free: float, busy: float, ours: float, then: int
) -> None:
    assert tune.step(allowed, most, 8, free, busy, ours) == then


def test_a_batch_is_sized_from_the_memory_measured_per_cell() -> None:
    assert tune.fit(peak=GB, cells=8, share=4 * GB) == 16  # an eighth of a GB a cell, 2 to fill
    assert tune.fit(peak=5 * GB, cells=2, share=4 * GB) == 1  # never fewer than one
    assert tune.fit(peak=GB, cells=8, share=1000 * GB) == tune.MOST


def test_a_pass_runs_every_cell_and_a_dead_worker_costs_only_its_own_cell(tmp_path: Path) -> None:
    cells = [f"cell{n}" for n in range(11)] + ["fatal"] + [f"cell{n}" for n in range(11, 20)]
    pc, clock = Pc(tmp_path), _ticking(SATURDAY, timedelta(hours=1))
    report = tune.run(cells, partial(_mark, tmp_path), pc, tmp_path, 8, clock)
    assert report.died == ("fatal",)
    assert all((tmp_path / name).exists() for name in cells if name != "fatal")
    assert pc.limits == (int(64 * GB * 0.6), int(64 * GB * 0.6) // 7)
    assert len(pc.held) == report.batches > 3 and pc.closed
    assert report.most_workers > 1  # stepped up, with room
    busy = [json.loads(flag) for flag in pc.flags]
    assert busy and all(flag["busy"] for flag in busy)
    assert len({flag["at"] for flag in busy}) > 1  # its time renewed as the pass goes on
    assert json.loads((tmp_path / tune.FLAG).read_text(encoding="utf-8")) == {"busy": False}
    logged = json.loads((tmp_path / tune.LOG).read_text(encoding="utf-8"))
    assert (logged["cells"], logged["died"], logged["peak_memory"]) == (21, 1, 3 * GB)
    assert (logged["peak_cpu"], logged["least_free"]) == (0.1, pytest.approx(0.9))
    assert logged["most_workers"] == report.most_workers


def test_a_pc_short_of_memory_gets_one_worker_at_a_time(tmp_path: Path) -> None:
    cells = [f"cell{n}" for n in range(4)]
    clock = _ticking(SATURDAY, timedelta(seconds=1))
    report = tune.run(cells, partial(_mark, tmp_path), Pc(tmp_path, free=0.2), tmp_path, 8, clock)
    assert report.most_workers == 1 and report.batches > 1 and not report.died
    assert all((tmp_path / name).exists() for name in cells)


def test_batches_grow_to_what_the_memory_measured_allows(tmp_path: Path) -> None:
    cells = [f"cell{n}" for n in range(40)]  # two threads: one worker, its part all that is left
    report = tune.run(cells, partial(_mark, tmp_path), Pc(tmp_path), tmp_path, 2, lambda: SATURDAY)
    assert report.batches == 3  # eight cells unmeasured, then sixteen at a time
    assert all((tmp_path / name).exists() for name in cells)


def test_a_dead_batch_is_halved_until_its_one_cell_stands_alone(tmp_path: Path) -> None:
    cells = [f"cell{n}" for n in range(7)] + ["fatal"]
    report = tune.run(cells, partial(_mark, tmp_path), Pc(tmp_path), tmp_path, 2, lambda: SATURDAY)
    assert report.died == ("fatal",) and report.batches == 7  # 8 cells; 4 and 4; 2 and 2; 1 and 1
    assert all((tmp_path / name).exists() for name in cells[:7])


def test_a_pass_that_is_stopped_leaves_no_worker_and_no_busy_flag(tmp_path: Path) -> None:
    def stopped() -> datetime:
        if (tmp_path / tune.FLAG).exists():
            raise KeyboardInterrupt
        return SATURDAY

    pc = Pc(tmp_path)
    with pytest.raises(KeyboardInterrupt):
        tune.run(["stuck"], partial(_mark, tmp_path), pc, tmp_path, 8, stopped)
    assert pc.closed and multiprocessing.active_children() == []
    assert json.loads((tmp_path / tune.FLAG).read_text(encoding="utf-8")) == {"busy": False}


def test_windows_refuses_a_hungry_cell_its_memory_and_the_batch_carries_on(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if sys.platform != "win32":  # no Job Object, so no ceiling: no pass may run at all
        with pytest.raises(OSError, match="Job Object"):
            tune.windows()
    else:
        pc = tune.windows()
        monkeypatch.setattr(tune, "CEILING", SMALL / pc.memory()[0])
        names = tuple(strategy.STRATEGIES)
        cells = [Cell(names[0], SPY, START, START + timedelta(24))]
        cells += [Cell(names[0], QQQ, START, START + timedelta(24))]
        cells += [Cell(name, SPY, START, START + timedelta(24)) for name in names[1:]]
        report = tune.run(cells, partial(_study, tmp_path), pc, tmp_path, 2)
        journal = (tmp_path / "journal.jsonl").read_text(encoding="utf-8")
        rows = [json.loads(row) for row in journal.splitlines()]
        assert [row["cell"][:2] for row in rows] == [[c.strategy, c.symbol] for c in cells]
        assert [row.get("error", "")[:11] for row in rows] == ["", "MemoryError", *[""] * 4]
        assert not report.died and report.batches == 1  # one worker: refused, it ran the rest
        assert 0 < report.peak_memory <= report.ceiling <= SMALL
        assert 0 <= report.peak_cpu <= 1 and 0 < report.least_free < 1
