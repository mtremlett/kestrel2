"""incident halted: SimCity's scenario for one real night (see `git log`, DECISIONS)."""

from __future__ import annotations

from datetime import UTC, date, datetime, time
from typing import TYPE_CHECKING

from desk import halt

if TYPE_CHECKING:
    from desk.simcity import _Life

HALTED = "a halt is in force while the day's buys are asked for"

STILL = "with a halt in force nothing is bought"


def halted(life: _Life, on: date) -> None:
    """A halt is called before the day: no buy may reach the broker, and the day's list names it."""
    at, reached = datetime.combine(on, time(7), UTC), life.pretend.buys
    called = halt.call(life.desk, at, "SimCity halts a day")
    life.live(on)
    life.promise(STILL, life.pretend.buys == reached)
    halt.lift(life.desk, called, at, "SimCity lifts it")
