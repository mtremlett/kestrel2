"""simcity_incidents - SCENARIOS SimCity lives because a night met them: each is a morning the
desk was put in, a promise it must keep there, and the day it then runs. R-RUNNER-246: a held
line has no bar for a session (a hole in the saved data), so the day has no record."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from desk import book

if TYPE_CHECKING:
    from desk.simcity import _Life

HOLE = "a held line has no bar for the session"
PROMISE = "a held line with no bar for a session is named when the day is refused"


def hole(life: _Life, on: date) -> None:
    """A held line's bar for the day is missing when the day ends. The desk must refuse to make
    a record from an older price, naming the line; when the bar arrives it runs the same day."""
    bars = {x: b for x, b in life.market.items() if any(d.day == on for d in b)}
    held = [x for x in bars if x.symbol in dict(life.pretend.stops())]
    if not held:
        life.live(on)
        return
    line, whole = held[0], life.market[held[0]]
    life.market[line] = tuple(bar for bar in whole if bar.day != on)
    try:
        life.live(on)
    except ValueError as refusal:  #: the desk's own word that the day has no record
        life.promise(PROMISE, line.symbol in str(refusal))
        life.market[line] = whole
        life.live(on)
    else:  #: a stop or a sale ended the holding that day: no close was owed
        life.market[line] = whole
        life.promise(PROMISE, line.symbol not in book.positions(life.desk))
