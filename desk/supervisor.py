"""supervisor - THE DESK'S OWN PROCESSES, KEPT ALIVE BY ONE SUPERVISOR. Everything the desk
runs unattended is a job on one register (JOBS): its name, the module that is its program,
how often it is due and how long it may take. The one supervisor (`supervise`) looks every
few seconds and runs each job that is due, one at a time, each in a process of its own in a
window nobody sees. It remembers nothing: a job is due when its last receipt began its own
interval ago, so a supervisor started again, after a kill or a reboot, simply carries on.

ONE OF EACH, held by the system and not by a note in a file. The supervisor holds a lock in
the desk's root for its whole life, and so does each job's process (`work`). The system lets
go of a lock when its process is gone, however it went. So a second supervisor leaves at
once; and a job left running by a supervisor that was killed is never joined by a second of
the same job: the next is refused, and its receipt says so, until that one has ended. A
job's process ends itself at its time limit, with nobody there to kill it (all but one stuck
where Python itself cannot run: only the supervisor that started it can kill that).

A DATED RECEIPT for every run the supervisor sees end: the job, when it began and ended, and
how: done, or the code it ended with and its last words, or that it ran to its time limit.
A job that fails is run again when next due and not before. The supervisor dials nothing, so
a dropped network or a lost broker is one bad receipt after another, and then a good one.

HEALTH IS JUDGED FROM OUTSIDE (`health`), by the receipts alone, by whoever asks: a job with
no receipt in the time one must come is not being run (the supervisor is dead, or stuck), and
a job whose last runs ended badly is named with how. No job registered is itself not well.

THE LEDGER OF WHAT HE DID (`acted`): each thing the operator does for the desk is written
here by whoever does or sees it. `unattended` measures how long the desk has run without
him: back to the last thing he did other than the paper Gateway's weekly login (his by
ruling, docs/DECISIONS.md), or to the last hour in which some job had no run that ended
well, whichever is the later. A desk not running proves nothing. Seven days are owed (NS-01).

Not built (docs/STATUS.md): the register is empty, for the desk's step has no command yet;
nobody is told what `health` finds; and the supervisor's own start, once, by Windows."""

from __future__ import annotations

import os
import runpy
import sqlite3
import subprocess
import sys
import time
from collections.abc import Callable, Iterator, Sequence
from contextlib import closing, contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import partial
from pathlib import Path
from threading import Timer
from typing import NamedTuple

RECORD = "supervisor.db"
TABLES = ("receipts (job, began, ended, how)", "actions (at, what)")
READ = "SELECT job, began, ended, how FROM receipts"
LAST = f"{READ} WHERE job = ? ORDER BY rowid DESC LIMIT 1"
#: A job's bad endings since it last ended well, oldest first.
BAD = (
    f"{READ} WHERE job = :job AND rowid > (SELECT COALESCE(MAX(rowid), 0) "  # noqa: S608 - fixed
    "FROM receipts WHERE job = :job AND how = :done) ORDER BY rowid"
)
HIS = "SELECT COALESCE(MAX(at), '') FROM actions WHERE what != ?"
RAN = "SELECT job, began FROM receipts WHERE how = ? AND began > ? AND began <= ? ORDER BY 2 DESC"
WORK = ("-m", "desk.supervisor", "work")  #: a job's own process, as the supervisor starts it
WAIT = 5  #: seconds one process waits for another's write of the record
LOOK = 15  #: seconds between the supervisor's looks at what is due
GRACE = 2  #: seconds past its time limit a job has to end itself before the supervisor kills it
OVERRUN = 124  #: the code a job's process ends itself with at its time limit
SAID = 200  #: the most of a job's last words its receipt keeps
SPELT = "backslashreplace"  #: what of a job's words cannot be read is spelt out, never dropped
SILENCE = timedelta(hours=1)  #: this long with no job ending well, and the desk was not running
OWED = timedelta(days=7)  #: how long the desk is to run without him (NS-01)
HIDDEN = getattr(subprocess, "CREATE_NO_WINDOW", 0)  #: on Windows, no window for a process
DONE, ENDED = "done", "ended {}: {}"
OVERRAN = "was still running at its time limit, {}, and was ended"
NOTHING = "No job is registered with the supervisor: nothing of the desk runs under it."
LATE = "No receipt of the desk's {} {}: nothing is running it. Please look at the PC."
BADLY = "The desk's {} has not ended well since {:%a %d %b %H:%M} UTC ({} in a row). The latest {}."
ALONE = "The desk has run {} days {} hours without him: {} days are owed (NS-01)."
LOGIN = "the paper Gateway's weekly login"
USAGE = "python -m desk.supervisor run ROOT | health ROOT | login ROOT | acted ROOT WHAT HE DID"
Clock = Callable[[], datetime]
_now: Clock = partial(datetime.now, UTC)


@dataclass(frozen=True)
class Job:
    """One thing the desk runs unattended, as the register holds it."""

    name: str
    module: str  #: its program, run as `python -m` runs one, the desk's root its one word
    every: timedelta  #: due again this long after its last run began
    limit: timedelta  #: a run still going after this long is ended


#: THE ONE REGISTER of what the desk runs unattended. Empty (docs/STATUS.md): the desk's step
#: has no command yet, and a module that only imports would end "done" with nothing done.
JOBS: tuple[Job, ...] = ()
Run = Callable[[Job, Path], str]


class Receipt(NamedTuple):
    """One run of a job, as the record keeps it."""

    job: str
    began: datetime
    ended: datetime
    how: str  #: DONE, or how else it ended


class Held(Exception):
    """Another process holds the lock: one supervisor, and one of each job, at a time."""


def _utc(moment: datetime) -> datetime:
    if moment.utcoffset() != timedelta(0):
        raise ValueError(f"{moment} is no moment in UTC: the supervisor's record is in UTC alone")
    return moment


@contextmanager
def _only(root: Path, name: str) -> Iterator[None]:
    """The lock of that name in the desk's root, held until left or until this process is
    gone, when the system lets go of it. Held by another, it is refused at once."""
    with closing(sqlite3.connect(root / f"{name}.lock", timeout=0, isolation_level=None)) as lock:
        try:
            lock.execute("BEGIN IMMEDIATE")
        except sqlite3.OperationalError as refused:
            if refused.sqlite_errorcode != sqlite3.SQLITE_BUSY:
                raise
            raise Held(f"another {name} is running in {root}: one at a time") from None
        yield


@contextmanager
def _record(root: Path) -> Iterator[sqlite3.Connection]:
    """The receipts and the ledger, opened: one file, each write whole or not at all, read
    and written by the supervisor and by whoever judges it from outside. A root that is
    not there is an error, never a new and empty record."""
    with closing(sqlite3.connect(root / RECORD, timeout=WAIT, isolation_level=None)) as record:
        for table in TABLES:
            record.execute(f"CREATE TABLE IF NOT EXISTS {table}")
        yield record


def _receipt(row: tuple[str, str, str, str]) -> Receipt:
    return Receipt(row[0], datetime.fromisoformat(row[1]), datetime.fromisoformat(row[2]), row[3])


def _run(job: Job, root: Path) -> str:
    """A job's own process (work), in a window nobody sees, to its end. One that has not
    ended itself GRACE after its time limit is killed. Given back: how it ended, as its
    receipt keeps it."""
    limit = job.limit.total_seconds()
    command = [sys.executable, *WORK, str(root), job.name, job.module, str(limit)]
    try:
        ended = subprocess.run(  # noqa: S603 - the desk's own python, on a registered module
            command, capture_output=True, errors=SPELT, timeout=limit + GRACE, creationflags=HIDDEN
        )
    except subprocess.TimeoutExpired:
        return OVERRAN.format(job.limit)
    last = (ended.stderr.strip().splitlines() or ["it said nothing"])[-1][:SAID]
    how = {0: DONE, OVERRUN: OVERRAN.format(job.limit)}
    return how.get(ended.returncode) or ENDED.format(ended.returncode, last)


def attend(
    root: Path, jobs: Sequence[Job], clock: Clock = _now, run: Run = _run
) -> tuple[Receipt, ...]:
    """ONE LOOK: each job due at its moment is run to its end, one at a time in the
    register's order, and its receipt kept. A job whose last receipt began an interval or
    more after now, by a clock since put right, is due. Given back: this look's receipts."""
    kept = []
    for job in jobs:
        began = _utc(clock())
        with _record(root) as record:
            last = record.execute(LAST, (job.name,)).fetchone()
        if last is None or abs(began - _receipt(last).began) >= job.every:
            how = run(job, root)
            receipt = Receipt(job.name, began, _utc(clock()), how)
            row = (job.name, began.isoformat(), receipt.ended.isoformat(), how)
            with _record(root) as record:
                record.execute("INSERT INTO receipts VALUES (?, ?, ?, ?)", row)
            kept.append(receipt)
    return tuple(kept)


def work(root: Path, name: str, module: str, limit: float) -> None:
    """A JOB'S OWN PROCESS: the job's lock held for the whole of its life, and its module run
    as the program, the desk's root its one word. While a run before it holds the lock (one
    a dead supervisor left running), this one is refused and runs nothing. At its time limit
    the process ends itself, watched or not, and the system lets go of its lock."""
    with _only(root, f"job-{name}"):
        code = [OVERRUN]
        ends = Timer(limit, lambda: os._exit(code[0]))
        ends.daemon = True
        ends.start()
        sys.argv = [module, str(root)]
        runpy.run_module(module, run_name="__main__", alter_sys=True)
        code[0] = 0  #: done: whatever of it lingers still ends at the limit, and as done


def health(root: Path, now: datetime, jobs: Sequence[Job]) -> tuple[str, ...]:
    """THE DESK'S HEALTH, JUDGED FROM OUTSIDE its processes by the receipts alone: what is
    wrong, in words for him; nothing, and all is well. A job is not being run when its last
    receipt ended longer ago than its interval, every job's time limit and a minute, the
    longest a supervisor that lives can leave it; or ended well after now. A job that is run
    is named while its last receipt ended badly, with how many have since it last ended well."""
    if not jobs:
        return (NOTHING,)
    patience, now = sum((job.limit for job in jobs), timedelta(seconds=4 * LOOK)), _utc(now)
    wrong = []
    with _record(root) as record:
        for job in jobs:
            bad = [*map(_receipt, record.execute(BAD, {"job": job.name, "done": DONE}))]
            last = [*map(_receipt, record.execute(LAST, (job.name,)))]
            if not last or not -patience <= now - last[0].ended <= job.every + patience:
                since = f"since {last[0].ended:%a %d %b %H:%M} UTC" if last else "at all"
                wrong.append(LATE.format(job.name, since))
            elif bad:
                wrong.append(BADLY.format(job.name, bad[0].began, len(bad), bad[-1].how))
    return tuple(wrong)


def acted(root: Path, at: datetime, what: str) -> None:
    """ONE THING HE DID FOR THE DESK, onto the ledger, with the moment in UTC and what it was.
    The Gateway's weekly login goes on in its own words (LOGIN): the one thing a ruling of
    his makes his own to do, and so no break in the desk's running without him."""
    if not what.strip():
        raise ValueError(f"the operator's action at {at} has no words for what he did")
    with _record(root) as record:
        record.execute("INSERT INTO actions VALUES (?, ?)", (_utc(at).isoformat(), what))


def unattended(root: Path, now: datetime, jobs: Sequence[Job]) -> timedelta:
    """HOW LONG THE DESK HAS RUN WITHOUT HIM, by the job that says least. For each job: up to
    its last run that ended well, back through such runs for as long as each began within
    SILENCE of the next, and no further than the last thing he did other than the Gateway's
    login. No run that ended well within SILENCE of now, or no job, is no time at all."""
    with _record(root) as record:
        his = record.execute(HIS, (LOGIN,)).fetchone()[0]
        ran = record.execute(RAN, (DONE, his, _utc(now).isoformat())).fetchall()
    spans = []
    for job in jobs:
        marks, since = [datetime.fromisoformat(at) for name, at in ran if name == job.name], now
        for mark in marks:
            if since - mark > SILENCE:
                break
            since = mark
        spans.append(marks[0] - since if since != now else timedelta(0))
    return min(spans, default=timedelta(0))


def supervise(
    root: Path, jobs: Sequence[Job], clock: Clock = _now, wait: Callable[[float], None] = time.sleep
) -> None:
    """THE ONE SUPERVISOR, for as long as it lives: the supervisor's lock taken (Held, and
    another is alive), then a look at what is due every LOOK seconds. Nothing registered is
    refused, and so is a name registered twice. An error of its own ends it: whatever
    started it starts it again."""
    names = [job.name for job in jobs]
    if not jobs or len(set(names)) < len(names):
        raise ValueError(NOTHING if not jobs else f"a job is on the register twice: {names}")
    with _only(root, "supervisor"):
        while True:
            attend(root, jobs, clock)
            wait(LOOK)


def main(argv: Sequence[str], clock: Clock = _now) -> int:
    """THE COMMAND LINE (USAGE). run: the supervisor, which leaves at once and without fault
    when another is alive. health: what is wrong and how long the desk has run without him,
    1 when anything is wrong. acted, login: a thing he did, onto the ledger, at this moment.
    work is the supervisor's own. Started hidden there is nobody to tell, and nothing is said."""
    match argv:
        case ["run", root]:
            try:
                supervise(Path(root), JOBS)
            except Held as other:
                print(other)  # noqa: T201 - the command's answer to whoever typed it
        case ["work", root, name, module, limit]:
            work(Path(root), name, module, float(limit))
        case ["health", root]:
            wrong, alone = health(Path(root), clock(), JOBS), unattended(Path(root), clock(), JOBS)
            told = ALONE.format(alone.days, alone.seconds // 3600, OWED.days)
            print(*wrong, told, sep="\n")  # noqa: T201 - the command's answer to whoever typed it
            return int(bool(wrong))
        case ["acted", root, *words] if words:
            acted(Path(root), clock(), " ".join(words))
        case ["login", root]:
            acted(Path(root), clock(), LOGIN)
        case _:
            raise SystemExit(USAGE)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
