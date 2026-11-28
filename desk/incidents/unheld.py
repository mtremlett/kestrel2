"""incident unheld: SimCity's scenario for one real night (see `git log`, DECISIONS)."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

from desk import bars, keeper_live, venues
from desk.bars import Five
from desk.lines import YARDSTICK, Line
from desk.spans import Timed

if TYPE_CHECKING:
    from desk.simcity import _Life

UNHELD = (
    "the live keeper asks for one-minute bars of lines the store never held: each is named stale"
)


def unheld(life: _Life, on: date) -> None:
    """The live keeper's store holds five-minute bars but never a one-minute bar of any line, and
    a venue is in session. The run must finish, never die on the store's LookupError, and name
    each line it could get no bar for as stale."""
    if on not in venues.sessions(YARDSTICK.venue, on, on):
        life.live(on)
        return
    session = venues.hours(YARDSTICK.venue, on)
    lines = sorted((x for x in life.market if x.venue == YARDSTICK.venue), key=lambda x: x.symbol)
    hot, now = life.desk / "unheld-bars.db", session.open + timedelta(hours=1)
    with bars.writing(hot) as round_:
        round_.five(YARDSTICK, [Five(session.open, *(Decimal(1),) * 4, 1)])

    def ask(line: Line, at: datetime) -> tuple[Timed, ...]:
        return bars.timed(hot, line, keeper_live.MINUTES, at - timedelta(hours=1), at)

    try:
        _, stale_ = keeper_live.minute_round(hot, lines, now, ask)
    except LookupError:  #: the store's own word that it never held the span
        life.promise(UNHELD, False)
    else:
        life.promise(UNHELD, bool(stale_))
    life.live(on)
