"""simcity_incidents - what a real night met, lived again as a SimCity scenario. Each is named by
the incident the runner recorded, never copied from its log: the desk is put in that situation and
its promises judged. JOB RAN OUT (job:deep:failed, 2026-11-16: no end after 21600 seconds): a
job of the desk's runs to its time limit and is ended; the desk must say so, naming the job and
how it ended, and the day it keeps goes on as before."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from typing import TYPE_CHECKING

from desk import supervisor
from desk.supervisor import Job

if TYPE_CHECKING:
    from desk.simcity import _Life

RAN_OUT = "a job runs to its time limit and is ended"
DEEP = Job("deep", "desk.simcitycmd", timedelta(days=1), timedelta(seconds=21600), False)


def ran_out(life: _Life, on: date) -> None:
    """The deep job's one run ends at its time limit; the supervisor's receipt is kept, and he is
    told by name and by how, once for the hour. The desk's day goes on beside it."""
    at = datetime.combine(on, time(8), UTC)
    root = life.desk / "supervisor"
    root.mkdir(exist_ok=True)
    supervisor.attend(
        root, (DEEP,), lambda: at, lambda job, _: supervisor.OVERRAN.format(job.limit)
    )
    told = list[tuple[str, str]]()
    later = at + timedelta(minutes=5)
    wrong = supervisor.tell(root, later, (DEEP,), lambda name, words: told.append((name, words)))
    words = " ".join(w for _, w in told)
    named = wrong and "deep" in words and "time limit" in words
    life.promise("a job that ran to its time limit is told to him, by name and how", bool(named))
    life.live(on)
