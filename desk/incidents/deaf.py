"""incident deaf: SimCity's scenario for one real night (see `git log`, DECISIONS)."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from itertools import count
from typing import TYPE_CHECKING

from desk import bars, halt, messenger, venues, watch
from desk.bars import Five
from desk.lines import YARDSTICK

if TYPE_CHECKING:
    from desk.simcity import _Life

DEAF = "the market goes unheard for an hour: he is told once in each hour, and nothing is halted"


def deaf(life: _Life, on: date) -> None:
    """The market's last bar of the session ended an hour ago and no bar since has come. The
    crash watch looks at three moments (two in one hour, one in the next): it must tell him it
    is blind once in each of the two hours, and call no halt for that alone."""
    if YARDSTICK not in life.market or on not in venues.sessions(YARDSTICK.venue, on, on):
        life.live(on)
        return
    daily = {x: [b for b in bars_ if b.day < on] for x, bars_ in life.market.items()}
    daily[YARDSTICK] = daily[YARDSTICK][-1:]  #: a calm month, so only the deafness can halt
    session, price = venues.hours(YARDSTICK.venue, on), Decimal(daily[YARDSTICK][-1].close)
    hot, post = life.desk / "deaf-bars.db", count(1).__next__
    with bars.writing(hot) as round_:
        round_.five(YARDSTICK, [Five(session.open + timedelta(hours=1), *(price,) * 4, 1)])
    first = session.open + timedelta(hours=2)
    kept = halt.kept(life.desk)
    for at in (first, first + timedelta(minutes=20), first + timedelta(minutes=65)):
        watch.look(life.desk, hot, daily, at, lambda _words: post())
    told = [d.name for d in messenger.deliveries(life.desk) if d.name.endswith("h blind")]
    hours = {f"watch {on:%Y-%m-%d} {at:%H}h blind" for at in (first, first + timedelta(hours=1))}
    life.promise(
        DEAF, hours <= set(told) and len(told) == len(set(told)) and kept == halt.kept(life.desk)
    )
    life.live(on)
