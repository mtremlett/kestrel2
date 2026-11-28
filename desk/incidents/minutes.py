"""incident minutes: SimCity's scenario for one real night (see `git log`, DECISIONS)."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

from desk import keeper_live, venues
from desk.lines import YARDSTICK, Line
from desk.spans import Timed

if TYPE_CHECKING:
    from desk.simcity import _Life

LIVE = "lines in session whose one-minute bar has just ended are none of them stale"


def minutes(life: _Life, on: date) -> None:
    """Two hours into the session every line of the yardstick's venue is due, and the broker
    answers each with the one-minute bar that has just ended. The keeper's live run must call
    none of them stale (else its job fails for a market that is whole), and keep the bars."""
    if venues.sessions(YARDSTICK.venue, on, on) != (on,):
        life.live(on)  #: the venue keeps a holiday: it has no hours to be stale in
        return
    now = venues.hours(YARDSTICK.venue, on).open + timedelta(hours=2)
    lines = sorted((x for x in life.market if x.venue == YARDSTICK.venue), key=lambda x: x.symbol)
    price = Decimal(1)

    def ask(_line: Line, at: datetime) -> tuple[Timed, ...]:
        return (Timed(keeper_live.MINUTES, at - timedelta(minutes=1), *(price,) * 4, 1),)

    hot = life.desk / "minutes-bars.db"
    words, missed = keeper_live.minute_round(hot, lines, now, ask)
    life.promise(LIVE, bool(lines) and not missed and ", 0 stale," in words)
    life.live(on)
