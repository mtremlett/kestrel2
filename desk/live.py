"""live - THE LIVE SESSION'S ONLY SOURCE OF BARS: a line's newest ended five-minute bars asked
of IB Gateway's paper port through the desk's one door (desk/paper.py), read-only, as its own
client (CLIENT, never 222, 223 or 225), one line at a time PACING seconds apart. His ruling of
16 November 2026: live prices are IBKR's only; the archive (Yahoo, a quarter of an hour late)
only backfills a past day. A line the broker gives nothing for is refused with words that say
so, never filled from anywhere else."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path

from desk import listing, paper, venues
from desk.bars import Five
from desk.lines import LINES, Line

CLIENT = 226  #: the live reader's own client id at the gateway
PACING = (
    3.0  #: seconds between asks: 20 lines a round, 40 asks in ten minutes, inside the limit of 60
)
HEAL = 24  #: bars asked, two hours: a round missed heals at the next
BAR = timedelta(minutes=5)
Newest = Callable[[Line, str, str, int], tuple[Five, ...]]
Wait = Callable[[float], object]  #: what lets time pass between asks


def ibkr(
    home: Path,
    wait: Wait = time.sleep,
    newest: Newest = paper.newest,
    listed: Callable[..., dict[str, listing.Listing | listing.Unlisted]] = listing.kept,
) -> Callable[[Line, datetime], tuple[Five, ...]]:
    """The question of a line's ended bars at a moment, in the line's own currency. The broker's
    listings are read once, from the desk's kept ones in home. Its words are the refusal when the
    broker gives no bar: no real-time data on paper is said, never replaced."""
    known: dict[str, listing.Listing | listing.Unlisted] = {}
    asked: list[str] = []

    def ask(line: Line, now: datetime) -> tuple[Five, ...]:
        paper.CLIENT = CLIENT  #: this process is the live reader, at the door
        if not known:
            known.update(listed(home, now, LINES))
        if (one := known.get(line.symbol)) is None:
            raise ValueError(f"{line.symbol} is not a line of the desk: the broker was not asked")
        if isinstance(one, listing.Unlisted):
            raise ValueError(f"no IBKR real-time data on paper for {line.symbol}: {one.reason}")
        if asked:
            wait(PACING)
        asked.append(line.symbol)
        try:
            got = newest(line, one.contract, one.exchange, HEAL)
        except (OSError, ValueError) as fault:
            raise ValueError(
                f"no IBKR real-time data on paper for {line.symbol}: {fault}"
            ) from fault
        if not got:
            raise ValueError(f"no IBKR real-time data on paper for {line.symbol}: no bars")
        scale = one.magnifier
        return tuple(
            replace(
                b,
                open=b.open / scale,
                high=b.high / scale,
                low=b.low / scale,
                close=b.close / scale,
            )
            for b in got
            if b.start + BAR <= now
            and (session := venues.open_at(line.venue, b.start))
            and b.start < session.close
        )

    return ask
