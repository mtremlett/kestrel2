"""The desk supervisor proved in SimCity: a week lived at the pretend broker, as the supervisor's
step, is killed mid-run and run again, with a dated receipt and nothing done by the operator."""

from __future__ import annotations

import os
import signal
import sqlite3
from datetime import timedelta
from pathlib import Path
from threading import Thread
from unittest.mock import Mock

import pytest
from test_supervisor import MIN, REPO, T0, _Enough, _program, _ran, _receipts, _until

from desk import supervisor
from desk.supervisor import DONE, Job

WEEK = Job("step", "the_job", 5 * MIN, timedelta(seconds=120))
#: The step's program: SimCity's one world over the scenes' first six sessions, the week. The
#: first process says it is midway after the first day and waits to be killed; the next lives it.
PROGRAM = f"""
import sys, time
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
sys.path.insert(0, {str(REPO / "tests" / "scenes")!r})
from rehearsal import CLEAN, LINES, SESSIONS
from desk import simcity
from desk.lines import YARDSTICK
from desk.orders import Settings
root = Path(sys.argv[1])
with open(root / "ran.txt", "a") as f:
    f.write(f"{{__import__('os').getpid()}} ")
first = len((root / "ran.txt").read_text().split()) < 2
live = simcity._Life.live
def midway(self, on):
    record = live(self, on)
    if first and len(self.records) == 1:
        (root / "midway.txt").write_text("1")
        time.sleep(60)
    return record
simcity._Life.live = midway
market = {{**CLEAN, YARDSTICK: CLEAN[LINES[1]]}}
week = {{x: [b for b in bars if b.day <= SESSIONS[5]] for x, bars in market.items()}}
rates = {{"GBP": Decimal(1), "USD": Decimal("0.79")}}
at = datetime(2025, 11, 17, 22, tzinfo=UTC)
night = simcity.run(root, week, Settings(Decimal(10_000)), rates, at, (0,))
(root / "week.txt").write_text(f"{{night.worlds}} {{night.days}}")
"""


def _kill_midway(root: Path) -> None:
    """From outside, kill the first process once it says it is midway through the week."""
    _until(lambda: (root / "midway.txt").exists())
    os.kill(_ran(root)[0], signal.SIGTERM)


def test_a_simcity_week_under_the_supervisor_restarts_a_killed_step_without_the_operator(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root, clock = _program(monkeypatch, tmp_path, PROGRAM), Mock()
    killer, wait = Thread(target=_kill_midway, args=(root,)), Mock(side_effect=[None, _Enough])
    killer.start()
    clock.side_effect = [T0, T0, *[T0 + 5 * MIN] * 2]  # a began and an ended for each look
    with pytest.raises(_Enough):
        supervisor.supervise(root, [WEEK], clock, wait)
    killer.join()
    (_, began, _, how), (_, again, _, last) = _receipts(root)
    assert how.startswith("ended ") and last == DONE  # killed in the week, then lived to its end
    assert (began, again) == (T0.isoformat(), (T0 + 5 * MIN).isoformat())  # each run dated
    assert len(_ran(root)) == 2 and _ran(root)[0] != _ran(root)[1]  # the step, in a new process
    assert (root / "week.txt").read_text().startswith("1 5")  # one world, the week's five days
    assert supervisor.health(root, T0 + 5 * MIN, [WEEK]) == ()
    with sqlite3.connect(root / supervisor.RECORD) as record:
        assert record.execute("SELECT COUNT(*) FROM actions").fetchone() == (0,)  # not him
