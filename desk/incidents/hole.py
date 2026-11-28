"""incident hole: SimCity's scenario for one real night (see `git log`, DECISIONS)."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from desk import book, day_money
from desk.lines import YARDSTICK

if TYPE_CHECKING:
    from desk.simcity import _Life

HOLE = "a held line has no bar for the session"

PROMISE = "a held line with no bar for a session is named owed and the day's profit withheld"


def hole(life: _Life, on: date) -> None:
    """A held line's bar for the day is missing when the day ends. The desk must make no record
    from an older price: its record names the line owed and withholds the profit. The yardstick
    is not chosen: its own close is owed to every record, and without it the day has none."""
    bars = {x: b for x, b in life.market.items() if any(d.day == on for d in b)}
    held = [x for x in bars if x.symbol in dict(life.pretend.stops()) and x != YARDSTICK]
    if not held:
        life.live(on)
        return
    line, whole = held[0], life.market[held[0]]
    life.market[line] = tuple(bar for bar in whole if bar.day != on)
    record = life.live(on)
    life.market[line] = whole  #: the record names the line owed, or a stop or sale ended it
    owed = line.symbol + day_money.NO_CLOSE_OWED in record.mismatches and record.profit is None
    life.promise(PROMISE, owed or line.symbol not in book.positions(life.desk))
