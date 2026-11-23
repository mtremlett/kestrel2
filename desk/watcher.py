"""watcher - THE SUPERVISOR'S WATCHER, independent of it (OPS-03). The supervisor is restarted
weekly and may die between; `health` judges the jobs by their receipts, and a supervisor that
is gone is seen there only once a job is late. The watcher asks the system itself: the lock the
supervisor holds for its whole life is held, or the supervisor is not running. It reads no
receipt and runs no job, and is run from outside (whatever Windows starts beside the supervisor).

A restart is no fault: the first look that finds no supervisor is written down (`watched`), and
only a supervisor still gone RESTART later is told, once in each UTC hour, through the
messenger's one door. One that is back clears the note."""

from __future__ import annotations

import os
import sys
from collections.abc import Callable, Sequence
from datetime import UTC, datetime, timedelta
from functools import partial
from pathlib import Path

from desk.supervisor import Held, _only

NOTE = "watcher.since"  #: when a look first found no supervisor, in UTC; gone when one is found
RESTART = timedelta(minutes=10)  #: the longest a restart of the supervisor may take, untold
GONE = "The desk's supervisor has not been running since {:%a %d %b %H:%M} UTC: nothing runs the desk. Please look at the PC."  # noqa: E501
USAGE = "python -m desk.watcher ROOT"
Clock = Callable[[], datetime]
_now: Clock = partial(datetime.now, UTC)


def running(root: Path) -> bool:
    """Whether a supervisor holds its lock in the desk's root: the system's word, not a file's."""
    try:
        with _only(root, "supervisor"):
            return False
    except Held:
        return True


def watched(root: Path, now: datetime, say: Callable[[str, str], object]) -> bool:
    """ONE LOOK. Given back: whether the supervisor is gone longer than a restart takes, in
    which case it is told (the hour is the message's name). A supervisor found running clears
    the note of its absence."""
    if now.utcoffset() != timedelta(0):
        raise ValueError(f"{now} is no moment in UTC: the watcher's note is in UTC alone")
    note = root / NOTE
    if running(root):
        note.unlink(missing_ok=True)
        return False
    if not note.exists():
        note.write_text(now.isoformat())
    since = datetime.fromisoformat(note.read_text())
    if now - since < RESTART:
        return False
    say(f"supervisor {now:%Y-%m-%d %H}", GONE.format(since))
    return True


def main(argv: Sequence[str], clock: Clock = _now) -> int:
    """THE COMMAND LINE (USAGE): one look; 1 when the supervisor is gone and he is told."""
    match argv:
        case [root]:
            from desk import (
                messenger,  # noqa: PLC0415 - the door is opened only for a look that tells
            )

            post, now = messenger.telegram(os.environ), clock()
            return int(
                watched(Path(root), now, partial(messenger.send, Path(root), now, post=post))
            )
        case _:
            raise SystemExit(USAGE)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
