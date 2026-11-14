"""The desk's processes supervised: a job run when due in a process of its own, a dated receipt
for every run and the desk's health judged from them; a job killed, or the supervisor itself,
started again, with one of each at a time held by the system; and the ledger of what the
operator did, measuring how long the desk has run without him."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Thread
from unittest.mock import Mock, call

import pytest

from desk import supervisor
from desk.supervisor import DONE, ENDED, LATE, LOGIN, NOTHING, OVERRAN, Action, Job, Receipt

REPO = Path(__file__).resolve().parents[2]
T0, MIN, HOUR = datetime(2026, 11, 16, 8, tzinfo=UTC), timedelta(minutes=1), timedelta(hours=1)
STEP = Job("step", "the_job", 5 * MIN, timedelta(seconds=30))
#: A job's program. It adds its own process's number to a file in the root it is given; then
#: it ends well (OK), fails as a lost network would make it (LOST), or does not end (STUCK).
OK = "import os, sys\nwith open(sys.argv[1] + '/ran.txt', 'a') as f:\n f.write(f'{os.getpid()} ')\n"
LOST, STUCK = OK + "raise SystemExit('the broker is gone')\n", OK + "import time\ntime.sleep(30)\n"
#: A supervisor of that one job in a process of its own, as Windows would start it.
RUN = f"import datetime, pathlib, sys; from desk.supervisor import Job, supervise; supervise(pathlib.Path(sys.argv[1]), [{STEP!r}])"  # noqa: E501
GONE = ENDED.format(1, "the broker is gone")


class _Enough(Exception):
    """Raised by a test's wait, to end a supervisor that would otherwise look for ever."""


def _program(patch: pytest.MonkeyPatch, tmp_path: Path, code: str) -> Path:
    """The job's program, written where a process of the desk's finds it. Given back: a root."""
    (tmp_path / "the_job.py").write_text(code, encoding="utf-8")
    patch.setenv("PYTHONPATH", os.pathsep.join([str(tmp_path), str(REPO)]))
    patch.setenv("PYTHONDONTWRITEBYTECODE", "1")
    return tmp_path / "desk"


def _ran(root: Path) -> list[int]:
    """The number of each process the job's program has run in, in order."""
    said = root / "ran.txt"
    return [int(number) for number in said.read_text().split()] if said.exists() else []


def _kill(root: Path, nth: int = 1) -> None:
    """From outside, kill the nth process the job's program ran in, once it says it runs."""
    until = time.monotonic() + 30
    while len(_ran(root)) < nth and time.monotonic() < until:
        time.sleep(0.05)
    os.kill(_ran(root)[nth - 1], signal.SIGTERM)


def test_a_job_runs_when_due_in_a_process_of_its_own_and_health_is_judged_by_its_receipts(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root, clock = _program(monkeypatch, tmp_path, OK), Mock(return_value=T0)
    assert supervisor.health(root, T0, [STEP]) == (LATE.format("step", "at all"),)
    assert supervisor.health(root, T0, []) == (NOTHING,)  # no job: nothing of the desk runs
    first = Receipt("step", T0, T0 + MIN, DONE)  # dated at both ends
    assert supervisor.attend(root, [STEP], Mock(side_effect=[T0, T0 + MIN])) == (first,)
    assert len(_ran(root)) == 1 and _ran(root) != [os.getpid()]  # its own process, given the root
    clock.return_value += 4 * MIN  # due again in a minute: nothing is run, and all is well
    assert supervisor.attend(root, [STEP], clock) == () and len(_ran(root)) == 1
    assert supervisor.health(root, clock(), [STEP]) == ()
    # THE NETWORK DROPS: the job fails, its code and last words on its receipt, and is simply
    # run again when next due. Health names the bad endings, how many and since when
    _program(monkeypatch, tmp_path, LOST)
    bad = [Receipt("step", T0 + n * MIN, T0 + n * MIN, GONE) for n in (5, 10)]
    for receipt in bad:
        clock.return_value = receipt.began
        assert supervisor.attend(root, [STEP], clock) == (receipt,)
    words = (
        "The desk's step has not ended well since Mon 16 Nov 08:05 UTC (2 in a row). "
        "The latest ended 1: the broker is gone."
    )
    assert supervisor.health(root, clock(), [STEP]) == (words,)
    # it is back: the next run is good, and nothing is wrong
    _program(monkeypatch, tmp_path, OK)
    clock.return_value = T0 + 15 * MIN
    good = Receipt("step", clock(), clock(), DONE)
    assert supervisor.attend(root, [STEP], clock) == (good,) and len(set(_ran(root))) == 4
    assert supervisor.health(root, clock(), [STEP]) == ()
    assert supervisor.receipts(root) == (first, *bad, good)
    # SILENCE: past the job's interval, its time limit and one look, nobody is running it
    late = good.began + STEP.every + STEP.limit + timedelta(seconds=supervisor.LOOK)
    silent = LATE.format("step", "since Mon 16 Nov 08:15 UTC")
    assert supervisor.health(root, late, [STEP]) == ()
    assert supervisor.health(root, late + timedelta(seconds=1), [STEP]) == (silent,)
    with pytest.raises(ValueError, match="no moment in UTC"):  # a clock not UTC runs nothing
        supervisor.attend(root, [STEP], Mock(return_value=datetime(2026, 11, 17, 8)))  # noqa: DTZ001


def test_a_job_killed_from_outside_or_overrunning_its_time_is_run_again_when_next_due(
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
    assert supervisor.health(root, T0, [STEP]) == (
        f"The desk's step has not ended well since Mon 16 Nov 08:00 UTC (1 in a row). "
        f"The latest {killed.how}.",
    )
    # stuck again at its next turn with nobody to kill it: at its time limit the supervisor does
    clock.return_value, brief = T0 + 5 * MIN, replace(STEP, limit=timedelta(seconds=2))
    over = Receipt("step", clock(), clock(), OVERRAN.format("0:00:02"))
    assert supervisor.attend(root, [brief], clock) == (over,)
    # neither left anything behind: the next run is a new process, and it ends well
    _program(monkeypatch, tmp_path, OK)
    clock.return_value = T0 + 10 * MIN
    assert supervisor.attend(root, [STEP], clock)[0].how == DONE
    assert supervisor.health(root, clock(), [STEP]) == () and _ran(root)[-1] != _ran(root)[0]


def test_one_supervisor_at_a_time_and_a_job_its_death_orphans_is_never_joined_by_a_second(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root, clock = _program(monkeypatch, tmp_path, STUCK), Mock(return_value=T0)
    monkeypatch.setattr(supervisor, "JOBS", [STEP])
    first = subprocess.Popen([sys.executable, "-c", RUN, str(root)], cwd=REPO)  # noqa: S603
    until = time.monotonic() + 30
    while not _ran(root) and time.monotonic() < until:  # its job is running
        time.sleep(0.05)
    # a second supervisor leaves at once, saying why, and that is no fault
    assert supervisor.main(["run", str(root)]) == 0
    assert capsys.readouterr().out == f"another supervisor is running in {root}: one at a time\n"
    # THE SUPERVISOR IS KILLED, its job still running. The next takes its place at once, and
    # does not run the job a second time beside the one left running: the receipt says why
    first.kill()
    first.wait()
    wait = Mock(side_effect=[None, _Enough])
    with pytest.raises(_Enough):
        supervisor.supervise(root, [STEP], clock, wait)
    (refused,) = supervisor.receipts(root)
    assert refused.how.startswith(ENDED.format(1, "Held: another job-step is running in "))
    assert len(_ran(root)) == 1 and wait.call_args_list == [call(supervisor.LOOK)] * 2
    # once the job left running has ended, however it ended, the job is run again
    _program(monkeypatch, tmp_path, OK)
    _kill(root)
    for turn in range(1, 50):  # the system lets go of a killed process's lock when it is gone
        clock.return_value = T0 + turn * 5 * MIN
        if supervisor.attend(root, [STEP], clock)[0].how == DONE:
            break
    assert supervisor.receipts(root)[-1].how == DONE and len(_ran(root)) == 2


def test_the_ledger_of_what_he_did_measures_how_long_the_desk_has_run_without_him(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    hourly, clock, run = Job("step", "the_job", HOUR, MIN), Mock(return_value=T0), Mock()
    run.return_value = DONE
    monkeypatch.setattr(supervisor, "JOBS", [hourly])

    def live(since: datetime, hours: int) -> datetime:
        """The supervisor looking each hour from a moment, so many hours on: its last look."""
        for hour in range(hours + 1):
            clock.return_value = since + hour * HOUR
            supervisor.attend(tmp_path, [hourly], clock, run)
        return since + hours * HOUR

    assert supervisor.unattended(tmp_path, T0) == timedelta(0)  # nothing ran: nothing is proven
    now = live(T0, 48)
    assert supervisor.unattended(tmp_path, now) == timedelta(days=2)
    # he restarts the PC: the count starts again at the first receipt after it
    did = supervisor.acted(tmp_path, now + MIN, "restarted the PC after an update")
    now = live(now + HOUR, 72)
    assert supervisor.unattended(tmp_path, now) == timedelta(days=3)
    # the Gateway's weekly login is his by ruling: on the ledger, and no break in the count
    login = supervisor.acted(tmp_path, now + MIN, LOGIN, ruled=True)
    now = live(now + HOUR, 95)
    assert supervisor.unattended(tmp_path, now) == timedelta(days=7) == supervisor.OWED
    assert (
        supervisor.actions(tmp_path)
        == (did, login)
        == (
            Action(T0 + 48 * HOUR + MIN, "restarted the PC after an update", False),
            Action(T0 + 121 * HOUR + MIN, LOGIN, True),
        )
    )
    assert supervisor.main(["health", str(tmp_path)], clock) == 0
    proven = "The desk has run 7 days 0 hours without him: 7 days are owed (NS-01).\n"
    assert capsys.readouterr().out == proven
    # over an hour with no receipt: the desk was not running, and a dead desk proves nothing
    assert supervisor.unattended(tmp_path, now + 61 * MIN) == timedelta(0)
    now = live(now + 61 * MIN, 5)
    assert supervisor.unattended(tmp_path, now) == timedelta(hours=5)
    for at, what in ((now.replace(tzinfo=None), "moved the PC"), (now, " ")):
        with pytest.raises(ValueError, match="no moment in UTC|no words"):
            supervisor.acted(tmp_path, at, what)


def test_the_command_line_keeps_his_ledger_and_refuses_a_desk_with_no_job_registered(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root, clock = str(tmp_path), Mock(return_value=T0)
    assert supervisor.main(["acted", root, "moved", "the", "PC"], clock) == 0
    assert supervisor.main(["login", root], clock) == 0
    kept = (Action(T0, "moved the PC", False), Action(T0, LOGIN, True))
    assert supervisor.actions(tmp_path) == kept
    # nothing is registered yet: the desk is not well, and a supervisor refuses to start
    assert supervisor.JOBS == () and supervisor.main(["health", root], clock) == 1
    alone = "The desk has run 0 days 0 hours without him: 7 days are owed (NS-01).\n"
    assert capsys.readouterr().out == f"{NOTHING}\n{alone}"
    with pytest.raises(ValueError, match="No job is registered"):
        supervisor.main(["run", root])
    for words in (["acted", root], ["health"], ["work", root], []):
        with pytest.raises(SystemExit, match="python -m desk.supervisor run ROOT"):
            supervisor.main(words)
