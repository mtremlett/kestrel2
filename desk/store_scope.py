"""store_scope - THE KEEPER'S JUDGING, SCOPED TO THE WINDOW THE DESK DECIDES ON (R-RUNNER-327).

The one judgement (`store.judge`) parks a line for a lasting fault of any age: a real crash in
2000 parks a line the desk trades on its last two years. The keeper judges through here: a fault
dated before the window is named, on its own day, and parks nothing; one inside it parks as ever.
`store.judge` and every research read are untouched."""

from __future__ import annotations

from dataclasses import replace
from datetime import date, timedelta

from desk import store, venues
from desk.coverage import NEED
from desk.lines import Line
from desk.store import Answer, Bar, Fault, Older, Parked
from desk.store_parts import NO_RATES, Rates

REACH = timedelta(days=900)  #: calendar days looked back to count the window's sessions


def window_start(line: Line, day: date) -> date:
    """The first session of the window the desk decides on: the NEED sessions before day."""
    return venues.sessions(line.venue, day - REACH, day - timedelta(1))[-NEED]


def judge(
    line: Line,
    answer: Answer,
    day: date,
    rates: Rates = NO_RATES,
    shelf: Older = None,
    broker: Answer | None = None,
) -> tuple[list[Bar], list[Fault], Parked | None]:
    """store.judge, but a fault dated before the window is only named (noted), never parks."""
    kept, faults, _ = store.judge(line, answer, day, rates, shelf, broker)
    start = window_start(line, day)
    scoped = [replace(f, noted=True) if f.day < start else f for f in faults]
    since = venues.sessions(line.venue, day - timedelta(100), day - timedelta(1))[-store.RECENT]
    recent = [f.what for f in scoped if not f.noted and (f.lasting or f.day >= since)]
    return kept, scoped, Parked(line.symbol, "; ".join(recent), day) if recent else None
