"""keeper - THE STORE'S KEEPER: one command, `python -m desk.keeper`, that does whatever the
store is owed at the moment it is called, and ends. The runner calls it every five minutes
of a weekday. It reads the calendars itself: on a day no venue trades it ends at once, and
well, having asked nothing, unless the store does not hold the bars before its venues' next
sessions (it was never filled, or an evening was missed): those are then asked for, once.

Two things are owed on a trading day, each venue's on its own calendar.

THE DAILY BARS of a venue's lines, asked of the archive whole and cleaned by the one store,
twice: at the day's first call, before any open, for the day about to trade; and again once
the venue's session is over and SETTLED has passed (`target`), so that the day's closes are
held that evening and the day's record can be made. The evening's bars are asked again in
the morning, for an archive restates a close overnight. What was last held, for which day,
and who is parked is a record beside the bars, and the door (`saved`) reads no bars it does
not cover.

A line the archive would not answer for is asked again at every call. Asked for a day the
store already holds, it keeps the bars and the standing it has; asked for a new day it is
parked alone, with no bars, for bars a day short are not that day's. A line parked for a
fault in its bars is asked again for TRIES calls and then left for the next refresh, unless
no line of its venue is clean: then it is asked at every call.

THE FIVE-MINUTE ROUND, at every call from a venue's open until SETTLED after its closing
auction, for the archive shows a session's last bars late: its lines' bars of the last
RECENT, through the fast store's checks, so a round missed heals at the next.

A call that left a venue with no line answered, or with no line clean, is a miss: the
command says so and ends with 1. One call asks the archive for SPENT seconds and no longer;
a line not reached by then is refused as any other."""

from __future__ import annotations

import json
import os
import sys
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import TypeVar

from desk import archive, bars, store, venues
from desk.bars import Five
from desk.lines import LINES, Line
from desk.store import Bar, Refused

DAILY, HOT = "daily", "bars.db"  #: in the data folder: the daily store's folder, the fast store
RECORD = "kept.json"  #: in each venue's folder of the daily store: its last refresh
#: How long after a venue's closing auction its day's bar is asked for: the archive shows
#: London a quarter of an hour late, and an official close is printed minutes after its bell.
SETTLED = timedelta(minutes=30)
TRIES = 6  #: the calls at which a line parked for a fault is asked again: half an hour's
RECENT = timedelta(days=7)  #: how far back a five-minute round asks: the week kept hot
#: The seconds of one call in which the archive is still asked: an answer then waited for
#: its thirty seconds, and the bars written, still end within the runner's four minutes.
SPENT = 150.0
DAY = timedelta(days=1)
When = TypeVar("When")
Read = TypeVar("Read")
Ask = Callable[[Line, When], Read]


class Stale(LookupError):
    """The daily store does not hold what was asked of it: a venue never refreshed, or one
    with a session since its last refresh."""


@dataclass(frozen=True)
class Kept:
    """A venue's last refresh of its daily bars, as its record keeps it."""

    day: date  #: the day it readied: every session of the venue before it was asked for
    at: datetime  #: when the archive was last asked
    tries: int  #: how many calls have asked for this day on this date
    parked: Mapping[str, str]  #: each parked line's symbol, and why
    refused: frozenset[str]  #: those of them the archive would not answer for


def _kept(folder: Path) -> Kept | None:
    """A venue's record, read on entry; none before its first refresh."""
    if not (folder / RECORD).is_file():
        return None
    said = json.loads((folder / RECORD).read_text(encoding="utf-8"))
    day, at = date.fromisoformat(said["day"]), datetime.fromisoformat(said["at"])
    return Kept(day, at, int(said["tries"]), dict(said["parked"]), frozenset(said["refused"]))


def _record(folder: Path, kept: Kept) -> None:
    """The record written whole, then swapped in, after the bars it speaks of."""
    said = {"day": kept.day.isoformat(), "at": kept.at.isoformat(), "tries": kept.tries}
    said |= {"parked": dict(kept.parked), "refused": sorted(kept.refused)}
    part = folder / f"{RECORD}.part"
    part.write_text(json.dumps(said, indent=1), encoding="utf-8")
    part.replace(folder / RECORD)


def _symbol(line: Line) -> str:
    return line.symbol


def target(venue: str, now: datetime) -> date:
    """The day a venue's daily bars are readied for at a moment: today, until its session is
    over and SETTLED has passed; from then, and all through a day it does not trade, tomorrow."""
    day = now.date()
    trades = venues.sessions(venue, day, day) == (day,)
    if trades and now < venues.hours(venue, day).auction + SETTLED:
        return day
    return day + DAY


def _short(venue: str, last: Kept | None, day: date) -> bool:
    """The venue's last refresh does not hold every session before a day: there was none, or
    the venue has traded since the day it readied."""
    return last is None or bool(venues.sessions(venue, last.day, day - DAY))


def _refresh(
    folder: Path, lines: Sequence[Line], now: datetime, ask: Ask[date, tuple[Bar, ...]], idle: bool
) -> Kept | None:
    """A venue's daily bars refreshed as far as they are owed at now, and the record of it;
    None when nothing was owed, and nothing asked. On an idle day, when no venue trades,
    only bars the store does not yet hold are owed."""
    readied, last = target(lines[0].venue, now), _kept(folder)
    if idle and not _short(lines[0].venue, last, readied):
        return None
    same = last is not None and last.day == readied
    before = dict(last.parked) if last is not None and same else {}
    if last is None or not same or last.at.date() != now.date():
        asked, tries = list(lines), 1
    else:
        blind = len(last.parked) == len(lines)
        again = last.refused | (set(last.parked) if last.tries < TRIES or blind else set())
        asked, tries = [line for line in lines if line.symbol in again], last.tries + 1
    if not asked:
        return None
    answers = archive.gather(asked, readied, ask)
    refused = {line.symbol for line, answer in answers.items() if isinstance(answer, Refused)}
    given = {line: answer for line, answer in answers.items() if line.symbol not in refused}
    found = store.prepare(folder, given if same else answers, readied)
    parked = {symbol: why for symbol, why in before.items() if symbol not in map(_symbol, given)}
    parked |= {line.symbol: line.reason for line in found}
    kept = Kept(readied, now, tries, parked, frozenset(refused))
    _record(folder, kept)
    return kept


def saved(
    home: Path, day: date, lines: Sequence[Line] = LINES
) -> tuple[dict[Line, tuple[Bar, ...]], frozenset[str]]:
    """THE PRICE STORE'S DOOR: every line's daily bars before a day, as last refreshed, and
    the symbols of the lines parked. A line whose venue has had a session before that day
    which its last refresh did not ask for is refused (Stale), never read a day short."""
    held: dict[Line, tuple[Bar, ...]] = {}
    parked: set[str] = set()
    for line in lines:
        folder = home / DAILY / line.venue
        last = _kept(folder)
        if last is None or _short(line.venue, last, day):
            had = "never refreshed" if last is None else f"last readied for {last.day}"
            raise Stale(f"{line.symbol}: no {line.venue} bars before {day} are held: {had}")
        held[line] = tuple(bar for bar in store.read(folder, line.symbol) if bar.day < day)
        parked |= {line.symbol} & set(last.parked)
    return held, frozenset(parked)


def _recent(line: Line, now: datetime) -> tuple[Five, ...]:
    return archive.fetch_five(line, now, RECENT)


def _within(ask: Ask[When, Read], clock: Callable[[], float], ends: float) -> Ask[When, Read]:
    """The question, asked only while the call's time lasts."""

    def asking(line: Line, when: When) -> Read:
        if clock() > ends:
            raise TimeoutError(f"the keeper's {SPENT:.0f} seconds were spent before it was asked")
        return ask(line, when)

    return asking


def _told(kept: Kept, mine: Sequence[Line]) -> tuple[str, bool]:
    """A venue's refresh in words, and whether it was a miss."""
    clean, venue = len(mine) - len(kept.parked), mine[0].venue
    words = (
        f"{venue}: daily bars before {kept.day}: {clean} of {len(mine)} lines clean, "
        f"{len(kept.refused)} refused by the archive (asked {kept.tries} times today)"
    )
    return words, len(mine) in (len(kept.refused), len(kept.parked))


def _round(
    hot: Path, mine: Sequence[Line], now: datetime, ask: Ask[datetime, tuple[Five, ...]]
) -> tuple[str, bool]:
    """A venue's five-minute round into the fast store, in words, and whether it was a miss."""
    answers = archive.gather(mine, now, ask)
    faults = bars.keep(hot, answers)
    refused = sum(isinstance(answer, Refused) for answer in answers.values())
    faulted = sum(bool(found) for found in faults.values()) - refused
    words = (
        f"{mine[0].venue}: five-minute round: {len(mine) - refused} of {len(mine)} lines "
        f"kept, {faulted} of them with faults listed, {refused} refused by the archive"
    )
    return words, refused == len(mine)


def keep(
    home: Path,
    now: datetime,
    lines: Sequence[Line] = LINES,
    daily: Ask[date, tuple[Bar, ...]] = archive.fetch,
    five: Ask[datetime, tuple[Five, ...]] = _recent,
    clock: Callable[[], float] = time.monotonic,
) -> tuple[list[str], list[str]]:
    """WHATEVER IS OWED AT NOW, done once: what was done, in words, and of those the misses.
    Nothing is asked, and nothing said, on a day no venue trades and the store is whole."""
    if now.utcoffset() != timedelta(0):
        raise ValueError(f"{now!r} is not a moment in UTC")
    idle = not any(venues.sessions(venue, now.date(), now.date()) for venue in venues.RULES)
    ends, told = clock() + SPENT, []
    for venue in sorted({line.venue for line in lines}):
        mine = [line for line in lines if line.venue == venue]
        kept = _refresh(home / DAILY / venue, mine, now, _within(daily, clock, ends), idle)
        if kept is not None:
            told.append(_told(kept, mine))
        if venues.open_at(venue, now) or venues.open_at(venue, now - SETTLED):
            told.append(_round(home / HOT, mine, now, _within(five, clock, ends)))
    return [words for words, _ in told], [words for words, miss in told if miss]


def main(home: Path, now: datetime) -> int:
    """THE COMMAND: what was done on one line each, a miss on the error stream, and 1 for it."""
    done, missed = keep(home, now)
    sys.stdout.write("".join(f"{line}\n" for line in done))
    sys.stderr.write("".join(f"MISSED: {line}\n" for line in missed))
    return int(bool(missed))


if __name__ == "__main__":
    sys.exit(main(Path(os.environ["KESTREL2_DATA"]), datetime.now(UTC)))
