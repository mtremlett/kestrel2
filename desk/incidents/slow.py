"""incident slow: SimCity's scenario for one real night (see `git log`, DECISIONS)."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from desk import paper

if TYPE_CHECKING:
    from desk.simcity import _Life

SLOW = "a broker that fills nothing cannot keep the desk's day past the step's time"


def slow(life: _Life, on: date) -> None:
    """The broker fills nothing, so each order sent is given the whole wait (19 November: 120 s
    each, the step killed at 240 s). The day's worst case, every order waiting out its time
    (paper.FILL_SECONDS) and the knock (paper.SECONDS), must end inside the step's time."""
    seen = len(life.pretend.submitted())
    life.live(on)
    sent = len(life.pretend.submitted()) - seen
    life.promise(SLOW, sent * paper.FILL_SECONDS + paper.SECONDS <= paper.STEP_SECONDS)
