"""watcher - AN INDEPENDENT WATCHER OF THE SUPERVISOR (OPS-03). The supervisor is restarted
weekly, and a dead one leaves no receipt to say so: `health` sees a job that is late, not
that nothing is there to run it. The watcher is a process of its own, started by whatever
Windows starts beside the supervisor, never by it. It looks at the supervisor's lock, which
the system holds for the supervisor's whole life: free means no supervisor is alive. A
restart frees it for a moment, so it looks twice, LOOKS apart, and only both free is a fault.
It tells what it finds, and what `health` finds, through the same door, once an hour."""

from __future__ import annotations

import os
import time
from collections.abc import Callable, Sequence
from datetime import datetime
from functools import partial
from pathlib import Path

from desk import supervisor
from desk.supervisor import Held, Job

LOOKS = 20  #: seconds between the two looks: longer than a restart takes
DEAD = "No supervisor is alive in {}: nothing runs the desk. Please look at the PC."
USAGE = "python -m desk.watcher ROOT"


def alive(root: Path, wait: Callable[[float], None] = time.sleep) -> bool:
    """Whether a supervisor holds its lock, at either of two looks LOOKS apart."""
    for look in range(2):
        try:
            with supervisor._only(root, "supervisor"):  # noqa: SLF001 - the one lock, one door
                pass
        except Held:
            return True
        if look == 0:
            wait(LOOKS)
    return False


def watch(
    root: Path,
    now: datetime,
    jobs: Sequence[Job],
    say: Callable[[str, str], object],
    wait: Callable[[float], None] = time.sleep,
) -> bool:
    """What is wrong with the supervisor, or with what it runs, told once in each UTC hour
    by say (name, words). Given back: whether anything was wrong."""
    wrong = [] if alive(root, wait) else [DEAD.format(root)]
    wrong += supervisor.health(root, now, jobs)
    if wrong:
        say(f"watch {supervisor._utc(now):%Y-%m-%d %H}", supervisor.NL.join(wrong))  # noqa: SLF001
    return bool(wrong)


def main(argv: Sequence[str]) -> int:
    """THE COMMAND LINE (USAGE): one look; 1 when anything is wrong and told."""
    from desk import (
        messenger,  # noqa: PLC0415 - it imports WAIT from the supervisor: no cycle at load
    )

    if len(argv) != 1:
        raise SystemExit(USAGE)
    root, now = Path(argv[0]), supervisor._now()  # noqa: SLF001
    post = messenger.telegram(os.environ)
    return int(watch(root, now, supervisor.JOBS, partial(messenger.send, root, now, post=post)))


if __name__ == "__main__":
    import sys

    raise SystemExit(main(sys.argv[1:]))
