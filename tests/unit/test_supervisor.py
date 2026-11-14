"""The desk's processes supervised: jobs run when due, each in its own process, one of each
at a time; receipts, and health judged by them; and the ledger of what the operator did."""

from __future__ import annotations

import contextlib
import os
import signal
import sqlite3
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Thread
from unittest.mock import Mock

import pytest

from desk import supervisor
from desk.supervisor import DONE, ENDED, LATE, LOGIN, NOTHING, OVERRAN, Held, Job, Receipt

REPO = Path(__file__).resolve().parents[2]
T0, MIN, HOUR = datetime(2026, 11, 16, 8, tzinfo=UTC), timedelta(minutes=1), timedelta(hours=1)
STEP = Job("step", "the_job", 5 * MIN, timedelta(seconds=60))
OFTEN = replace(STEP, every=40 * MIN)
BRIEF, KEEPER = replace(STEP, limit=timedelta(seconds=0.5)), Job("keeper", "x", 5 * MIN, 10 * MIN)
#: A job's program adds its own process's number to a file in the root it is given. Then it
#: ends well (OK); fails as a lost network would, with words nobody can read and more than a
#: receipt keeps (LOST); does not end (STUCK); or cannot even end itself at its limit (FROZEN).
OK = "import os, sys\nwith open(sys.argv[1] + '/ran.txt', 'a') as f:\n f.write(f'{os.getpid()} ')\n"
LOST = OK + "sys.stderr.buffer.write(b'\\x81\\n')\nraise SystemExit('the broker is gone ' * 20)\n"
STUCK = OK + "import threading as t, time\ntime.sleep(60)\n"
FROZEN = STUCK.replace("\nti", "\n[x.cancel() for x in t.enumerate()[1:]]\nti")
#: A supervisor of that one job in a process of its own, as Windows would start it.
RUN = f"import datetime, pathlib, sys; from desk.supervisor import Job, supervise; supervise(pathlib.Path(sys.argv[1]), [{STEP!r}])"  # noqa: E501
GONE = ENDED.format(1, ("the broker is gone " * 20)[: supervisor.SAID])
MINUTES, SINCE = [T0 + n * MIN for n in range(4)], "since Mon 16 Nov 08:0{} UTC"
BADLY = "The desk's {} has not ended well since Mon 16 Nov {} UTC ({} in a row). The latest {}."


class _Enough(Exception):
    """Raised by a test's wait, to end a supervisor that would otherwise look for ever."""


def _program(patch: pytest.MonkeyPatch, tmp_path: Path, code: str) -> Path:
    """The job's program, written where a process of the desk's finds it. Given back: a root."""
    (tmp_path / "the_job.py").write_text(code, encoding="utf-8")
    patch.setenv("PYTHONPATH", os.pathsep.join([str(tmp_path), str(REPO)]))
    patch.setenv("PYTHONDONTWRITEBYTECODE", "1")
    (tmp_path / "desk").mkdir(exist_ok=True)
    return tmp_path / "desk"


def _ran(root: Path) -> list[int]:
    """The number of each process the job's program has run in, in order."""
    said = root / "ran.txt"
    return [int(number) for number in said.read_text().split()] if said.exists() else []


def _until(done: Callable[[], bool]) -> None:
    """Wait, thirty seconds at most, for what another process is doing."""
    until = time.monotonic() + 30
    while not done() and time.monotonic() < until:
        time.sleep(0.05)


def _kill(root: Path) -> None:
    """From outside, kill the first process the job's program ran in, once it says it runs."""
    _until(lambda: bool(_ran(root)))
    os.kill(_ran(root)[0], signal.SIGTERM)


def test_a_job_runs_when_due_in_a_process_of_its_own_and_every_run_leaves_a_dated_receipt(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root, clock = _program(monkeypatch, tmp_path, OK), Mock(return_value=T0)
    spy = Mock(wraps=subprocess.run)
    monkeypatch.setattr(subprocess, "run", spy)
    assert supervisor.health(root, T0, [STEP]) == (LATE.format("step", "at all"),)
    first, began = Receipt("step", T0, T0 + MIN, DONE), time.monotonic()  # dated at both ends
    assert supervisor.attend(root, [STEP], Mock(side_effect=[T0, T0 + MIN])) == (first,)
    assert time.monotonic() - began < 30  # a run that is done does not wait out its time limit
    assert len(_ran(root)) == 1 and _ran(root) != [os.getpid()]  # its own process, given the root
    hidden = getattr(subprocess, "CREATE_NO_WINDOW", 0)  # on Windows, in a window nobody sees
    assert spy.call_args.kwargs["creationflags"] == hidden and spy.call_args.args[0][-1] == "60.0"
    clock.return_value += 4 * MIN  # due again in a minute: nothing is run, and all is well
    assert supervisor.attend(root, [STEP], clock) == () and len(_ran(root)) == 1
    assert supervisor.health(root, clock(), [STEP]) == ()
    # THE NETWORK DROPS: the job fails, its code and the last of its words on its receipt, and
    # is simply run again when next due. Health names the bad endings, how many and since when
    _program(monkeypatch, tmp_path, LOST)
    for n in (5, 10):
        clock.return_value = T0 + n * MIN
        assert supervisor.attend(root, [STEP], clock) == (Receipt("step", clock(), clock(), GONE),)
    assert supervisor.health(root, clock(), [STEP]) == (BADLY.format("step", "08:05", 2, GONE),)
    # it is back: the next run is good, and nothing is wrong
    _program(monkeypatch, tmp_path, OK)
    clock.return_value = T0 + 15 * MIN
    good = Receipt("step", clock(), clock(), DONE)
    assert supervisor.attend(root, [STEP], clock) == (good,) and len(set(_ran(root))) == 4
    assert supervisor.health(root, clock(), [STEP]) == ()


def test_a_job_killed_from_outside_or_still_running_at_its_time_limit_is_run_again_when_due(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root, clock = _program(monkeypatch, tmp_path, STUCK), Mock(return_value=T0)
    # THE KILL DRILL: the job's process is killed from outside as it runs, and its receipt
    # says how it ended
    killer = Thread(target=_kill, args=(root,))
    killer.start()
    (killed,) = supervisor.attend(root, [STEP], clock)
    killer.join()
    assert killed.how in {ENDED.format(code, "it said nothing") for code in (15, -15)}
    assert supervisor.health(root, T0, [STEP]) == (BADLY.format("step", "08:00", 1, killed.how),)
    # stuck again, with nobody watching it at all: at its time limit the process ends itself
    alone = [sys.executable, *supervisor.WORK, str(root), "step", "the_job", "0.5"]
    assert subprocess.run(alone, cwd=REPO, check=False).returncode == supervisor.OVERRUN  # noqa: S603
    # and under the supervisor the receipt says so; one too far gone even for that is killed
    # by the supervisor soon after, and its receipt says the same
    for n, program in ((5, STUCK), (10, FROZEN)):
        _program(monkeypatch, tmp_path, program)
        clock.return_value = T0 + n * MIN
        over = Receipt("step", clock(), clock(), OVERRAN.format(BRIEF.limit))
        assert supervisor.attend(root, [BRIEF], clock) == (over,)
    # none left anything behind: the next run is a new process, and it ends well
    _program(monkeypatch, tmp_path, OK)
    clock.return_value = T0 + 15 * MIN
    assert supervisor.attend(root, [STEP], clock)[0].how == DONE
    assert supervisor.health(root, clock(), [STEP]) == () and _ran(root)[-1] != _ran(root)[0]


def test_one_supervisor_at_a_time_and_a_job_its_death_orphans_is_never_joined_by_a_second(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root, clock = _program(monkeypatch, tmp_path, STUCK), Mock(return_value=T0)
    monkeypatch.setattr(supervisor, "JOBS", [STEP])
    first = subprocess.Popen([sys.executable, "-c", RUN, str(root)], cwd=REPO)  # noqa: S603
    try:
        _until(lambda: bool(_ran(root)))  # its job is running
        # a second supervisor leaves at once, saying why, and that is no fault; started hidden
        # there is nobody to say it to. Were the lock broken it would look: an error, not a hang
        with monkeypatch.context() as second:
            second.setattr(supervisor, "attend", Mock(side_effect=_Enough))
            assert supervisor.main(["run", str(root)]) == 0
            said = f"another supervisor is running in {root}: one at a time\n"
            assert capsys.readouterr().out == said
            second.setattr(sys, "stdout", None)
            assert supervisor.main(["run", str(root)]) == 0
    finally:
        first.kill()
        first.wait()
    # THE SUPERVISOR IS KILLED, its job still running. The next takes its place as soon as the
    # system lets go of the lock, and does not run the job a second time beside the one left
    # running: the receipt says why
    wait = Mock(side_effect=_Enough)

    def takes_over() -> bool:
        with contextlib.suppress(Held), pytest.raises(_Enough):
            supervisor.supervise(root, [STEP], clock, wait)
        return wait.called

    _until(takes_over)
    wait.assert_called_once_with(supervisor.LOOK)
    (refused,) = supervisor.health(root, T0, [STEP])
    assert "(1 in a row). The latest ended 1: Held: another job-step is running in " in refused
    assert len(_ran(root)) == 1
    # once the job left running has ended, however it ended, the job is run again
    _program(monkeypatch, tmp_path, OK)
    _kill(root)
    for turn in range(1, 50):  # the system lets go of a killed process's lock when it is gone
        clock.return_value = T0 + turn * 5 * MIN
        if supervisor.attend(root, [STEP], clock)[0].how == DONE:
            break
    assert supervisor.health(root, clock(), [STEP]) == () and len(_ran(root)) == 2


def test_health_is_judged_by_the_receipts_alone_whatever_the_clock_has_done(tmp_path: Path) -> None:
    clock, run, both = Mock(return_value=T0), Mock(return_value=DONE), [STEP, KEEPER]
    assert supervisor.health(tmp_path, T0, []) == (NOTHING,)  # no job: nothing of the desk runs
    for refused in ([], [STEP, STEP]):  # and no supervisor for no job, or for one named twice
        with pytest.raises(ValueError, match="No job is registered|on the register twice"):
            supervisor.supervise(tmp_path, refused, clock, Mock(side_effect=_Enough))
    # each job due is run in the register's order, one at a time
    ran = (Receipt("step", T0, T0 + MIN, DONE), Receipt("keeper", MINUTES[2], MINUTES[3], DONE))
    assert supervisor.attend(tmp_path, both, Mock(side_effect=MINUTES), run) == ran
    assert [given.args for given in run.call_args_list] == [(STEP, tmp_path), (KEEPER, tmp_path)]
    # SILENCE: a job waits for every job before it, so a receipt is late only past its own
    # interval, every job's time limit and a minute; then nobody is running it
    late = ran[0].ended + STEP.every + STEP.limit + KEEPER.limit + MIN
    silent = (LATE.format("step", SINCE.format(1)), LATE.format("keeper", SINCE.format(3)))
    assert supervisor.health(tmp_path, late, both) == ()
    # a clock a second behind the last receipt is no alarm, and runs nothing again
    assert supervisor.health(tmp_path, MINUTES[3] - timedelta(seconds=1), both) == ()
    assert (
        supervisor.attend(tmp_path, both, Mock(return_value=T0 - timedelta(seconds=1)), run) == ()
    )
    assert supervisor.health(tmp_path, late + timedelta(seconds=1), both) == silent[:1]
    assert supervisor.health(tmp_path, late + 2 * MIN + timedelta(seconds=1), both) == silent
    # THE PC'S CLOCK RAN A DAY AHEAD and was put right: a receipt from tomorrow is not all
    # well, and its job is due now, not tomorrow
    clock.return_value = T0 + 24 * HOUR
    supervisor.attend(tmp_path, [STEP], clock, run)
    ahead = LATE.format("step", "since Tue 17 Nov 08:00 UTC")
    clock.return_value = T0 + 6 * MIN
    assert supervisor.health(tmp_path, clock(), [STEP]) == (ahead,)
    assert supervisor.attend(tmp_path, [STEP], clock, run)[0].began == clock()
    assert supervisor.health(tmp_path, clock(), [STEP]) == ()
    for minute, how in ((8, GONE), (11, DONE)):  # a failing job is named though another is well
        clock.return_value, run.return_value = T0 + minute * MIN, how
        supervisor.attend(tmp_path, both, clock, run)
    assert supervisor.health(tmp_path, clock(), both) == (BADLY.format("keeper", "08:08", 1, GONE),)
    naive = datetime(2026, 11, 17, 8)  # noqa: DTZ001 - a clock not UTC judges and runs nothing
    with pytest.raises(ValueError, match="no moment in UTC"):
        supervisor.health(tmp_path / "new", naive, [STEP])
    with pytest.raises(ValueError, match="no moment in UTC"):
        supervisor.attend(tmp_path, [STEP], Mock(return_value=naive), run)


def test_the_ledger_of_what_he_did_measures_how_long_the_desk_has_run_without_him(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    clock, run, jobs = Mock(return_value=T0), Mock(return_value=DONE), [OFTEN]
    monkeypatch.setattr(supervisor, "JOBS", jobs)

    def live(since: datetime, looks: int) -> datetime:
        """The supervisor looking every forty minutes from a moment: its last look's moment."""
        for look in range(looks + 1):
            clock.return_value = since + look * 40 * MIN
            supervisor.attend(tmp_path, jobs, clock, run)
        return since + looks * 40 * MIN

    assert supervisor.unattended(tmp_path, T0, jobs) == timedelta(0)  # nothing ran: no proof
    supervisor.acted(tmp_path, T0 + MIN, "set the desk up")
    now = live(T0, 18)
    assert supervisor.unattended(tmp_path, now, jobs) == timedelta(hours=11, minutes=20)
    assert supervisor.unattended(tmp_path, T0 + 6 * HOUR, jobs) == timedelta(minutes=320)  # then
    # he restarts the PC: the count starts again at the first good run after the last he did
    supervisor.acted(tmp_path, now + MIN, "restarted the PC after an update")
    now = live(now + 40 * MIN, 108)
    assert supervisor.unattended(tmp_path, now, jobs) == timedelta(days=3)
    # the Gateway's weekly login is his by ruling: on the ledger, and no break in the count
    supervisor.acted(tmp_path, now + MIN, LOGIN)
    now = live(now + 40 * MIN, 143)
    assert supervisor.unattended(tmp_path, now, jobs) == timedelta(days=7) == supervisor.OWED
    assert supervisor.main(["health", str(tmp_path)], clock) == 0
    proven = "The desk has run 7 days 0 hours without him: 7 days are owed (NS-01).\n"
    assert capsys.readouterr().out == proven
    # the count runs to the last good run and no later; an hour and more with none, and the
    # desk was not running: a dead desk proves nothing, and neither does one whose runs fail
    assert supervisor.unattended(tmp_path, now + 60 * MIN, jobs) == timedelta(days=7)
    assert supervisor.unattended(tmp_path, now + 61 * MIN, jobs) == timedelta(0)
    run.return_value = GONE
    live(now + 40 * MIN, 3)
    run.return_value = DONE
    now = live(now + 200 * MIN, 6)
    assert supervisor.unattended(tmp_path, now, jobs) == timedelta(hours=4)
    assert supervisor.unattended(tmp_path, now, [OFTEN, KEEPER]) == timedelta(0)  # by the least
    for at, what in ((now.replace(tzinfo=None), "moved the PC"), (now, " ")):
        with pytest.raises(ValueError, match="no moment in UTC|no words"):
            supervisor.acted(tmp_path, at, what)


def test_the_command_line_keeps_his_ledger_and_refuses_a_desk_with_no_job_registered(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root, clock, run = str(tmp_path), Mock(return_value=T0), Mock(return_value=DONE)
    # nothing is registered yet, and the desk is not well
    assert supervisor.JOBS == () and supervisor.main(["health", root], clock) == 1
    alone = "The desk has run {} days {} hours without him: 7 days are owed (NS-01).\n"
    assert capsys.readouterr().out == f"{NOTHING}\n{alone.format(0, 0)}"
    # his login goes on the ledger in its own words, and anything else he did in his: after
    # five hours of good runs, a login two hours in breaks nothing, and the other thing does
    for look in range(31):
        supervisor.attend(tmp_path, [STEP], Mock(return_value=T0 + look * 10 * MIN), run)
    clock.return_value = T0 + 2 * HOUR + MIN
    assert supervisor.main(["login", root], clock) == 0
    clock.return_value = T0 + 5 * HOUR
    monkeypatch.setattr(supervisor, "JOBS", [STEP])
    assert supervisor.main(["health", root], clock) == 0
    assert capsys.readouterr().out == alone.format(0, 5)
    clock.return_value = T0 + 3 * HOUR + MIN
    assert supervisor.main(["acted", root, "moved", "the", "PC"], clock) == 0
    assert supervisor.unattended(tmp_path, T0 + 5 * HOUR, [STEP]) == timedelta(minutes=110)
    with contextlib.closing(sqlite3.connect(tmp_path / supervisor.RECORD)) as record:
        ledger = record.execute("SELECT at, what FROM actions").fetchall()
    his = [(T0 + 2 * HOUR + MIN, LOGIN), (T0 + 3 * HOUR + MIN, "moved the PC")]
    assert ledger == [(at.isoformat(), what) for at, what in his]
    # words that are no command are refused, and so is a root that is not there
    for words in (["acted", root], ["health"], ["work", root], ["login", f"{root}/typo"], []):
        with pytest.raises((SystemExit, sqlite3.OperationalError), match="supervisor run|unable"):
            supervisor.main(words)
