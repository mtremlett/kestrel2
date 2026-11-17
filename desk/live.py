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
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import BinaryIO

from desk import bars, listing, paper, venues
from desk.bars import Five
from desk.lines import LINES, Line
from desk.spans import Timed

CLIENT = 226  #: the live reader's own client id at the gateway
PACING = (
    3.0  #: seconds between asks: 20 lines a round, 40 asks in ten minutes, inside the limit of 60
)
HEAL = 24  #: bars asked, two hours: a round missed heals at the next
BAR = timedelta(minutes=5)
MINUTE = timedelta(minutes=1)
Newest = Callable[[Line, str, str, int, paper.Door], tuple[Five, ...]]
Wait = Callable[[float], object]  #: what lets time pass between asks
NewestMinutes = Callable[[Line, str, str, int, paper.Door], tuple[Timed, ...]]
MINUTES = "1m"  #: the span of the one-minute bars
FIRST = 3600  #: seconds of one-minute bars asked of a line with none held
MOST = 86400  #: the most one question of one-minute bars may reach back


def ibkr(
    home: Path,
    wait: Wait = time.sleep,
    newest: Newest = paper.newest,
    listed: Callable[..., dict[str, listing.Listing | listing.Unlisted]] = listing.kept,
) -> Callable[[Line, datetime], tuple[Five, ...]]:
    """The question of a line's ended bars at a moment, in the line's own currency. The broker's
    listings are read once, from the desk's kept ones in home. Its words are the refusal when the
    broker gives no bar: no real-time data on paper is said, never replaced."""
    door = _door(home, wait, listed, mine := paper.Door(CLIENT))

    def ask(line: Line, now: datetime) -> tuple[Five, ...]:
        one = door(line, now)
        try:
            got = newest(line, one.contract, one.exchange, HEAL, mine)
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


def _door(
    home: Path,
    wait: Wait,
    listed: Callable[..., dict[str, listing.Listing | listing.Unlisted]],
    mine: paper.Door,
) -> Callable[[Line, datetime], listing.Listing]:
    """The one way to the gateway for a line: the live reader's door, the line's listing
    (read once from home's kept ones) and PACING seconds between one ask and the next."""
    known: dict[str, listing.Listing | listing.Unlisted] = {}
    asked: list[str] = []

    def door(line: Line, now: datetime) -> listing.Listing:
        if not known:
            known.update(listed(home, now, LINES, mine))
        if (one := known.get(line.symbol)) is None:
            raise ValueError(f"{line.symbol} is not a line of the desk: the broker was not asked")
        if isinstance(one, listing.Unlisted):
            raise ValueError(f"no IBKR real-time data on paper for {line.symbol}: {one.reason}")
        if asked:
            wait(PACING)
        asked.append(line.symbol)
        return one

    return door


def _minute(fields: list[str]) -> Timed:
    """One one-minute bar of an answer, its price and volume checked by the one parser of a bar's
    fields (`paper._five`, given a start that is a five-minute mark so only the rest is judged);
    the start is then read as any minute."""
    checked = paper._five(["0", *fields[1:]])
    at = datetime.fromtimestamp(int(paper.number(fields[0], fields)), UTC)
    return Timed(
        MINUTES, at, checked.open, checked.high, checked.low, checked.close, checked.volume
    )


def newest_minutes(
    line: Line, contract: str, route: str, seconds: int, mine: paper.Door
) -> tuple[Timed, ...]:
    """The line's one-minute bars of the last `seconds` (the last may still be forming) from the
    paper gateway, oldest first, trades only: `paper.newest`'s question at a minute's size."""
    asked = (contract, line.symbol, "STK", "", "0.0", "", "", route, "", line.currency, "", "", 0)
    ask = paper.message(
        paper.ASK_BARS, 1, *asked, "", "1 min", f"{seconds} S", 0, "TRADES", 2, 0, ""
    )

    def talk(wire: BinaryIO, send: paper.Send) -> tuple[Timed, ...]:
        paper.start(wire, send, mine)
        send(ask)
        while (fields := paper.receive(wire))[:2] != [paper.BARS, "1"]:
            paper.other(fields)
        count = fields[4] if len(fields) > 4 else ""
        if not (count.isascii() and count.isdigit()) or len(fields) != 5 + 8 * int(count):
            raise ValueError(f"bars of a shape the desk does not read: {fields}")
        return tuple(_minute(fields[n : n + 6]) for n in range(5, len(fields), 8))

    return paper.dial(talk)


def minutes(
    home: Path,
    hot: Path,
    wait: Wait = time.sleep,
    newest: NewestMinutes = newest_minutes,
    listed: Callable[..., dict[str, listing.Listing | listing.Unlisted]] = listing.kept,
) -> Callable[[Line, datetime], tuple[Timed, ...]]:
    """The question of a line's ended one-minute bars since the last held in hot (an hour's if
    none), in the line's own currency. Refusals are worded as the five-minute question's."""
    door = _door(home, wait, listed, mine := paper.Door(CLIENT))

    def ask(line: Line, now: datetime) -> tuple[Timed, ...]:
        one = door(line, now)
        back = now - timedelta(seconds=MOST)
        held = bars.timed(hot, line, MINUTES, back, now) if hot.is_file() else ()
        since = int((now - held[-1].start).total_seconds()) + 60 if held else FIRST
        try:
            got = newest(line, one.contract, one.exchange, min(max(since, 120), MOST), mine)
        except (OSError, ValueError) as fault:
            raise ValueError(
                f"no IBKR real-time data on paper for {line.symbol}: {fault}"
            ) from fault
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
            if b.start + MINUTE <= now
            and (session := venues.open_at(line.venue, b.start))
            and b.start < session.close
        )

    return ask
