"""incident stale: SimCity's scenario for one real night (see `git log`, DECISIONS)."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from typing import TYPE_CHECKING

from desk import keeper
from desk.keeper_rotate import Kept, record

if TYPE_CHECKING:
    from desk.simcity import _Life

STALE = "a venue's daily bars are a session short at the keeper's last refresh"

REFUSED = "the price store's door refuses a venue short of a session, naming its line"


def stale(life: _Life, on: date) -> None:
    """The keeper's last refresh of every venue readied a week before the day, so a session is
    lacking. The price store's door must refuse, naming a line, never serve the older bars."""
    lines = sorted(life.market, key=lambda x: x.symbol)
    stored = life.desk / "keeper"
    for venue in {x.venue for x in lines}:
        past = Kept(on - timedelta(days=7), datetime.combine(on, time(), UTC), 1, {}, frozenset())
        record(stored / keeper.DAILY / venue, past)
    try:
        keeper.saved(stored, on, lines)
    except keeper.Stale as refusal:  #: the keeper's own word that the store is not fresh
        life.promise(REFUSED, lines[0].symbol in str(refusal))
    else:
        life.promise(REFUSED, False)
    life.live(on)
