"""incident locked: SimCity's scenario for one real night (see `git log`, DECISIONS)."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

from desk import bars, keeper_live
from desk.bars import Five
from desk.lines import YARDSTICK, Line
from desk.spans import Timed

if TYPE_CHECKING:
    from desk.simcity import _Life

LOCKED = "a store another writer holds refuses the round by name, loses nothing, serves the next"


def locked(life: _Life, on: date) -> None:
    """Another writer holds the live store when the keeper's one-minute round begins (17 November,
    "database is locked"). The round must be refused by name (NoRound) with nothing of it landed,
    and the next run, the store free, must go through."""
    lines = sorted((x for x in life.market if x.venue == YARDSTICK.venue), key=lambda x: x.symbol)
    opened = datetime.combine(on, time(9), UTC)  #: any day will do; the store ignores the calendar
    hot, now = life.desk / "locked-bars.db", opened + timedelta(hours=1)
    with bars.writing(hot) as round_:
        round_.five(YARDSTICK, [Five(opened, *(Decimal(1),) * 4, 1)])

    def ask(line: Line, at: datetime) -> tuple[Timed, ...]:
        return bars.timed(hot, line, keeper_live.MINUTES, at - timedelta(hours=1), at)

    refused, wait = False, bars.WAIT
    bars.WAIT = 0.05  #: the world will not wait the five seconds a real night does
    try:
        with closing(sqlite3.connect(hot, isolation_level=None)) as other:
            other.execute("BEGIN IMMEDIATE")
            try:
                keeper_live.minute_round(hot, lines, now, ask)
            except bars.NoRound as busy:  #: the store's own word that the round was not begun
                refused = str(hot) in str(busy)
    finally:
        bars.WAIT = wait
    keeper_live.minute_round(hot, lines, now, ask)
    life.promise(LOCKED, refused and bool(bars.five(hot, YARDSTICK, opened, now)))
    life.live(on)
