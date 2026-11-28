"""incident parked: SimCity's scenario for one real night (see `git log`, DECISIONS)."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from desk.lines import YARDSTICK

if TYPE_CHECKING:
    from desk.simcity import _Life

PARKED = "a yardstick with a session missing refuses the day by name"


def parked(life: _Life, on: date) -> None:
    """The yardstick's bar for the session before the day is missing (a gap in the archive, the
    line parked). The desk must refuse the day, naming the line, for the market's gain over the
    gap cannot be told; when the bar is back the same day runs."""
    whole = life.market.get(YARDSTICK, ())
    gone = [b.day for b in whole if b.day < on][-1:]
    if not gone:
        life.live(on)
        return
    life.market[YARDSTICK] = tuple(b for b in whole if b.day != gone[0])
    try:
        life.live(on)
    except ValueError as refusal:  #: the desk's own word that the day has no record
        life.promise(PARKED, YARDSTICK.symbol in str(refusal))
        life.market[YARDSTICK] = whole
        life.live(on)
    else:
        life.market[YARDSTICK] = whole
        life.promise(PARKED, False)
