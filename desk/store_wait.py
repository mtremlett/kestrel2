"""store_wait - A WAIT FOR THE STORE'S LOCK IS NAMED (R-RUNNER-329). SQLite's busy timeout
(bars.WAIT, 5 seconds, far below the 240 a job is given) ends a wait for a file another
holds; what it raises says only "database is locked". Here that end is told as it was:
who waited, for which database, how long. SQLite does not say who holds a lock, so the
holder is named as unknown. No retry: the one wait ends in the one error."""

from __future__ import annotations

import os
import sqlite3
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


class StoreWait(sqlite3.OperationalError):
    """A wait for a store's lock reached its limit: the waiter, the database, the seconds."""


@contextmanager
def named(file: Path, seconds: float) -> Iterator[None]:
    """Run a block that opens or reads the store at file, whose waits SQLite ends after
    `seconds`: if it ends in a locked database, raise StoreWait saying so."""
    try:
        yield
    except sqlite3.OperationalError as refusal:
        if "locked" not in str(refusal) and "busy" not in str(refusal):
            raise
        waiter = f"pid {os.getpid()} ({Path(sys.argv[0]).name or 'python'})"
        raise StoreWait(
            f"{waiter} waited {seconds} seconds for {file}, held by another (holder unknown): "
            f"{refusal}"
        ) from refusal
