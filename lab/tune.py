"""tune - THE PASS'S AUTO-TUNE, so a pass can never take the PC down: batches of the work run
in fresh worker processes under a memory ceiling Windows itself holds, as many at once as the
free cores allow, fewer while the PC is short of memory or busy with other work.

The ceiling is a Job Object every worker is put in: the workers together may commit 60% of
the PC's memory and each one its share of that, so a memory-hungry cell is refused its
memory, it alone, and its neighbours and the PC carry on. Windows keeps the workers below
normal priority, and ends them all if the pass itself dies. No pass runs without the
ceiling: on a machine that is not Windows it is refused.

Workers are sized to the cores: two of the PC's threads are left free while markets are open
(UK 08:00 to 21:00 on a day London or New York trades), one overnight and at weekends. Once a
second the pass reads the PC: under 25% free memory, or above 85% busy with other programs
taking more than the threads left to them, it starts one worker fewer, never fewer than one;
with room it steps back up by one. The workers' own load is no reason to back off.

A batch is cut from the front of the work, eight cells at first and then as many as fit half
a worker's share at the memory the last batch measured per cell, so a worker reads only its
own cells' bars, never the whole universe. A worker that dies has its batch halved and run
again until the one cell that kills it stands alone, and that one is reported.

While a pass runs it keeps `autotune.json` in the data folder as busy with the time, and as
not busy when it ends; the runner starts fewer sessions meanwhile. Each pass appends one
line to `passes.jsonl` there: its peak memory, peak CPU, least free memory and most workers.
"""

from __future__ import annotations

import ctypes
import json
import multiprocessing
import sys
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from multiprocessing import connection
from multiprocessing.process import BaseProcess
from pathlib import Path
from typing import Any, Generic, Protocol, TypeVar

from desk import venues

T = TypeVar("T")
CEILING = 0.60  #: the share of the PC's memory the workers together may commit
FREE_MEMORY = 0.25  #: back off under this share of memory free
BUSY = 0.85  #: back off above this share of the processor busy
OPEN, SHUT = 8, 21  #: UK hours, on a trading day, in which two threads are left free
FIRST, MOST = 8, 512  #: cells in a batch: before any is measured, and at most
TICK = timedelta(seconds=1)  #: how often the PC is read
REFRESH = timedelta(minutes=10)  #: how often the busy flag's time is renewed
FLAG, LOG = "autotune.json", "passes.jsonl"
#: the job's limits: each process's memory, the job's memory, no crash dialog, all workers
#: ended when the pass's handle closes, and one priority class - below normal
LIMITS, BELOW_NORMAL = 0x100 | 0x200 | 0x400 | 0x2000 | 0x20, 0x4000


class Machine(Protocol):
    """The PC, and the ceiling it holds on the pass's workers."""

    def memory(self) -> tuple[int, int]: ...  #: bytes in all, bytes free
    def load(self) -> tuple[float, float]: ...  #: since last asked: share busy, workers' share
    def limit(self, job: int, process: int) -> None: ...  #: the ceiling, in bytes
    def hold(self, worker: BaseProcess) -> None: ...  #: put a started worker under it
    def spent(self, worker: BaseProcess) -> int: ...  #: a finished worker's peak bytes
    def peak(self) -> int: ...  #: the most the workers together ever held
    def close(self) -> None: ...  #: end every worker still running


@dataclass(frozen=True)
class Report(Generic[T]):
    started: str
    ended: str
    cells: int
    batches: int  #: workers started, a died batch's halves included
    died: tuple[T, ...]  #: each cell whose worker died running it alone
    ceiling: int  #: bytes the workers together were allowed
    peak_memory: int  #: bytes the workers together reached
    peak_cpu: float  #: the PC's busiest second, as a share
    least_free: float  #: the smallest share of the PC's memory seen free
    most_workers: int


def _last_sunday(year: int, month: int) -> datetime:
    day = datetime(year, month + 1, 1, 1, tzinfo=UTC) - timedelta(days=1)
    return day - timedelta(days=(day.weekday() + 1) % 7)


def spare(now: datetime) -> int:
    """The threads left free: two in UK market hours on a day a venue trades, else one."""
    utc = now.astimezone(UTC)
    summer = _last_sunday(utc.year, 3) <= utc < _last_sunday(utc.year, 10)
    uk = utc + timedelta(hours=1 if summer else 0)
    trading = any(venues.sessions(venue, uk.date(), uk.date()) for venue in venues.RULES)
    return 2 if trading and OPEN <= uk.hour < SHUT else 1


def step(allowed: int, most: int, threads: int, free: float, busy: float, ours: float) -> int:
    """The workers allowed next: one fewer when short of memory or crowded, one more with room."""
    others, theirs = busy - ours, (threads - most) / threads
    if free < FREE_MEMORY or (busy > BUSY and others > theirs):
        return max(1, min(allowed, most) - 1)
    room = others <= theirs or busy + 1 / threads <= BUSY
    return min(most, allowed + 1 if room else allowed)


def fit(peak: int, cells: int, share: int) -> int:
    """The cells in a batch that fill half a worker's share, at peak bytes for cells."""
    return max(1, min(MOST, share * cells // (2 * peak)))


def _flag(data: Path, state: dict[str, Any]) -> None:
    fresh = data / (FLAG + ".new")
    fresh.write_text(json.dumps(state), encoding="utf-8")
    fresh.replace(data / FLAG)


@dataclass
class _Pass(Generic[T]):
    work: Callable[[Sequence[T]], None]
    machine: Machine
    threads: int
    share: int  #: bytes one worker may commit
    waiting: list[Sequence[T]]
    running: dict[BaseProcess, Sequence[T]] = field(default_factory=dict)
    died: list[T] = field(default_factory=list)
    size: int = FIRST
    allowed: int = 1
    batches: int = 0
    peak_cpu: float = 0.0
    least_free: float = 1.0
    most_workers: int = 0

    def reap(self) -> None:
        """Each finished worker measured; a dead one's batch halved, or its one cell named."""
        for worker in [w for w in self.running if not w.is_alive()]:
            batch = self.running.pop(worker)
            worker.join()
            if worker.exitcode == 0:
                self.size = fit(self.machine.spent(worker), len(batch), self.share)
            elif len(batch) > 1:
                self.waiting[:0] = [batch[: len(batch) // 2], batch[len(batch) // 2 :]]
            else:
                self.died.extend(batch)
            worker.close()

    def read(self, now: datetime) -> None:
        """The PC read once, and the workers allowed stepped down or up by it."""
        total, free = self.machine.memory()
        busy, ours = self.machine.load()
        most = max(1, self.threads - spare(now))
        self.allowed = step(self.allowed, most, self.threads, free / total, busy, ours)
        self.peak_cpu, self.least_free = (
            max(self.peak_cpu, busy),
            min(self.least_free, free / total),
        )

    def start(self) -> None:
        """Batches cut from the front of the work, each in a fresh worker under the ceiling."""
        spawn = multiprocessing.get_context("spawn")
        while self.waiting and len(self.running) < self.allowed:
            first = self.waiting.pop(0)
            if first[self.size :]:
                self.waiting.insert(0, first[self.size :])
            worker = spawn.Process(target=self.work, args=(first[: self.size],))
            worker.start()
            self.running[worker] = first[: self.size]
            self.machine.hold(worker)
            self.batches += 1
        self.most_workers = max(self.most_workers, len(self.running))

    def stop(self) -> None:
        for worker in self.running:
            worker.kill()
            worker.join()
        self.machine.close()


def run(
    todo: Sequence[T],
    work: Callable[[Sequence[T]], None],
    machine: Machine,
    data: Path,
    threads: int,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> Report[T]:
    """One pass: work (a module's function) called on every cell of todo, a batch to a worker."""
    started = clock()
    ceiling = int(machine.memory()[0] * CEILING)
    machine.limit(ceiling, ceiling // max(1, threads - 1))
    state = _Pass(work, machine, threads, ceiling // max(1, threads - 1), [todo] if todo else [])
    seen = flagged = started - REFRESH
    try:
        while state.waiting or state.running:
            now = clock()
            state.reap()
            if now - seen >= TICK:
                seen = now
                state.read(now)
            state.start()
            if now - flagged >= REFRESH:
                flagged = now
                _flag(data, {"busy": True, "at": now.isoformat()})
            if state.running:
                sentinels = [worker.sentinel for worker in state.running]
                connection.wait(sentinels, timeout=TICK.total_seconds())
        peak = machine.peak()
    finally:
        state.stop()
        _flag(data, {"busy": False})
    counts = (len(todo), state.batches, tuple(state.died), ceiling, peak)
    marks = (state.peak_cpu, state.least_free, state.most_workers)
    report = Report(started.isoformat(), clock().isoformat(), *counts, *marks)
    with (data / LOG).open("a", encoding="utf-8") as log:
        log.write(json.dumps({**asdict(report), "died": len(report.died)}) + "\n")
    return report


if sys.platform == "win32":

    class _Windows:
        """Windows's own counters and its Job Object, as 64-bit Windows lays them out: each
        structure below is read and written as its eight-byte slots."""

        def __init__(self) -> None:
            self._k = ctypes.WinDLL("kernel32", use_last_error=True)
            self._k.CreateJobObjectW.restype = ctypes.c_void_p
            self._job = ctypes.c_void_p(self._ok(self._k.CreateJobObjectW(None, None)))
            self._load = (0.0, 0.0)
            self._times = self._clocks()

        def _ok(self, result: Any) -> Any:
            if not result:
                raise ctypes.WinError(ctypes.get_last_error())
            return result

        def _job_facts(self, kind: int, slots: int) -> Any:
            facts = (ctypes.c_uint64 * slots)()
            size = ctypes.sizeof(facts)
            self._ok(self._k.QueryInformationJobObject(self._job, kind, facts, size, None))
            return facts

        def _clocks(self) -> tuple[int, int, int]:
            """Processor time so far, in 100 ns: idle, all of it, and the job's workers'."""
            idle, kernel, user = ctypes.c_uint64(), ctypes.c_uint64(), ctypes.c_uint64()
            byref = ctypes.byref
            self._ok(self._k.GetSystemTimes(byref(idle), byref(kernel), byref(user)))
            spent = self._job_facts(1, 6)  # basic accounting: user time, then kernel time
            return idle.value, kernel.value + user.value, spent[0] + spent[1]

        def memory(self) -> tuple[int, int]:
            status = (ctypes.c_uint64 * 8)(64)  # MEMORYSTATUSEX: its length, then the counts
            self._ok(self._k.GlobalMemoryStatusEx(status))
            return status[1], status[2]

        def load(self) -> tuple[float, float]:
            before, self._times = self._times, self._clocks()
            idle, total, ours = (b - a for a, b in zip(before, self._times, strict=True))
            if total:
                self._load = (1 - idle / total, ours / total)
            return self._load

        def limit(self, job: int, process: int) -> None:
            facts = (ctypes.c_uint64 * 18)()  # the extended limits: flags in slot 2, priority
            facts[2], facts[7], facts[14], facts[15] = LIMITS, BELOW_NORMAL, process, job
            size = ctypes.sizeof(facts)  # in 7, the process's bytes in 14, the job's in 15
            self._ok(self._k.SetInformationJobObject(self._job, 9, facts, size))

        def hold(self, worker: BaseProcess) -> None:
            handle = ctypes.c_void_p(worker.sentinel)
            self._ok(self._k.AssignProcessToJobObject(self._job, handle))

        def spent(self, worker: BaseProcess) -> int:
            counters = (ctypes.c_uint64 * 9)(72)  # PROCESS_MEMORY_COUNTERS: peak commit last
            handle = ctypes.c_void_p(worker.sentinel)
            self._ok(self._k.K32GetProcessMemoryInfo(handle, counters, 72))
            return int(counters[8])

        def peak(self) -> int:
            return int(self._job_facts(9, 18)[17])

        def close(self) -> None:
            self._ok(self._k.CloseHandle(self._job))

    def windows() -> Machine:
        """This PC, with a new Job Object for one pass's workers."""
        return _Windows()

else:

    def windows() -> Machine:
        """Refused: where there is no Job Object there is no ceiling, and no pass."""
        raise OSError("the pass's memory ceiling is a Windows Job Object: no pass without it")
