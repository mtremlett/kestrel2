"""incident unbarred: SimCity's scenario for one real night (see `git log`, DECISIONS)."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

from desk import bars, conformance_parts, keeper, venues
from desk.keeper_rotate import Kept, record
from desk.lines import YARDSTICK

if TYPE_CHECKING:
    from desk.simcity import _Life

UNBARRED = "a conformance plan with no bar of the session before the day refuses, naming the line"


def unbarred(life: _Life, on: date) -> bool:
    """The store holds a London line's daily bars but not the session before the day (17 November,
    the conformance job). The plan of the run must refuse, naming the line and the session, and
    never size an order from an older close. False on a day London is shut: still owed."""
    if on not in venues.sessions(YARDSTICK.venue, on, on):
        life.live(on)  #: London keeps a holiday on a US session: no run is planned, still owed
        return False
    line = next(x for x in life.begun(on) if x.venue == YARDSTICK.venue)
    before = venues.sessions(line.venue, on - timedelta(days=9), on)[-2]
    home = life.desk / "unbarred"
    with bars.writing(home / keeper.HOT) as round_:
        round_.daily(line, [b for b in life.market[line] if b.day < before])
    past = Kept(on, datetime.combine(on, time(), UTC), 1, {}, frozenset())
    record(home / keeper.DAILY / line.venue, past)
    try:
        conformance_parts.plan([line], line, on, {line.currency: Decimal(1)}, "0000", home)
    except ValueError as refusal:  #: the plan's own word that the session has no bar
        life.promise(UNBARRED, line.symbol in str(refusal) and f"{before}" in str(refusal))
    else:
        life.promise(UNBARRED, False)
    life.live(on)
    return True
