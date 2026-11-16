"""streak - FIRST-LIGHT counted by the desk itself (NS-10): ten consecutive clean days."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from desk import day
from desk.day import Record

NEEDED = 10  #: the consecutive clean days that are FIRST-LIGHT


def clean(records: Sequence[Record]) -> int:
    """The clean days at the end of the records, unbroken. A day counts only by its own
    verdict (Record.counts): reconciled, no halt, and its orders sent. A day that sent
    nothing (stopped None) is not clean, and it breaks the run."""
    run = 0
    for record in reversed(records):
        if not record.counts:
            break
        run += 1
    return run


def first_light(root: Path) -> bool:
    """True once the desk's own published records end in ten consecutive clean days."""
    return clean(day.records(root)) >= NEEDED
