"""keeper - THE STORE'S KEEPER: one command, `python -m desk.keeper`, that does whatever the
store is owed at the moment it is called, and ends. The runner calls it every five minutes
of a weekday. It reads the calendars itself: on a day no venue trades it ends at once, and
well, having asked nothing, unless the store does not hold the bars before its venues' next
sessions (it was never filled, or an evening was missed): those are then asked for, once.

Two things are owed on a trading day, each venue's on its own calendar.

THE DAILY BARS of a venue's lines, asked of the archive whole and cleaned by the one store,
twice: at the day's first call, before any open, for the day about to trade; and again once
the venue's session is over and SETTLED has passed (`target`), so that the day's closes are
held that evening and the day's record can be made, and again next morning (an archive
restates a close overnight). What was last held, for which day, and who is parked is a record
beside the bars, and the door (`saved`) reads no bars it does not cover.

A line the archive would not answer for is asked again at every call: for a day the store
holds it keeps its bars and standing; for a new day it is parked alone, with no bars. A line
parked for a fault in its bars is asked again for TRIES calls and then left for the next
refresh, unless no line of its venue is clean: then it is asked at every call. The pound's
closes the long database holds judge them (`pound_closes`).

THE FIVE-MINUTE ROUND, at every call from a venue's open until SETTLED after its closing
auction: its lines' ended bars of the session under way (the yardstick first) come from IBKR's
paper gateway alone (`desk/live.py`, his ruling of 16 November), through the fast store's checks.
A line the broker gives nothing for is refused, in words; the round is a miss when no line is
heard, and says how late its newest bar landed; the archive's bars of the last week only fill
past gaps, none enters the session under way.

THE REFERENCE SERIES, once a day after the US close: `lines.REFERENCE` (SPY) and the pound in
dollars (`lines.POUND`, read by `pound`), asked of the archive from their first session and kept
apart from the traded lines; one the archive refuses is told, not a miss.

THE LINES PARKED LIVE (`parked_live`), read from the fast store alone at any moment, so a line that
comes clean is back at the next look: one whose venue has been open for LATE and holds no ended
five-minute bar of the last LATE, or whose last LATE of bars has a fault (a move out of line).

A call that left a venue with no line answered or clean is a miss: the command says so and
ends with 1. One call asks the archive for SPENT seconds; a line not reached is refused."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from functools import partial
from pathlib import Path
from typing import TypeVar

from desk import archive, bars, carry, keeper_live, live, store, venues
from desk.bars import Five
from desk.lines import ADJUSTED, DOLLARS, LINES, POUND, REFERENCE, YARDSTICK, Line
from desk.store import Bar, Parked, Refused

#: In the data folder: each venue's record of its last refresh (no prices), and the short database.
DAILY, HOT = "daily", bars.LIVE
MARKS = "reference"  #: beside a venue's record, the day each reference series was last kept
CRLF = bytes((13, 10))  #: a Windows checkout's line ending, not part of the rules
RECORD = "kept.json"  #: in each venue's folder of the daily store: its last refresh
#: THE STORE RULES' VERSION: a hash of desk/store.py. A refresh records the version it cleaned
#: under; a record of another version is cleaned again whole from the archive's answers.
RULES = hashlib.sha256(Path(store.__file__).read_bytes().replace(CRLF, b"\n")).hexdigest()
#: How long after a venue's closing auction its day's bar is asked for (London shows late).
SETTLED = timedelta(minutes=30)
#: THE FIGURE THE DAY'S RECORD WAITS ON: by this long after a venue's closing auction its day's
#: closes are held, if the archive answers at the first call: the first call after SETTLED (every
#: five minutes) and that call's four minutes. `target` turns to the next day at SETTLED itself.
HELD = SETTLED + timedelta(minutes=5 + 4)
LATE = timedelta(minutes=15)  #: a line's five-minute bars are late, and it is parked, after this
TRIES = 6  #: the calls at which a line parked for a fault is asked again (half an hour)
#: The seconds of one call in which the archive is still asked: the runner allows four minutes.
SPENT = 150.0
DAY = timedelta(days=1)
ANCIENT = partial(archive.fetch, since=archive.REFERENCE_SINCE)  #: the reference series' ask
When = TypeVar("When")
Read = TypeVar("Read")
Ask = Callable[[Line, When], Read]
#: The broker's daily bars for lines before a day: the store's first source (R-RUNNER-189).
Broker = Callable[[Sequence[Line], date], Mapping[Line, store.Answer]]


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
    rules: str = ""  #: the store rules' version it was cleaned under; none in an old record


def _kept(folder: Path) -> Kept | None:
    """A venue's record, read on entry; none before its first refresh."""
    if not (folder / RECORD).is_file():
        return None
    said = json.loads((folder / RECORD).read_text(encoding="utf-8"))
    day, at = date.fromisoformat(said["day"]), datetime.fromisoformat(said["at"])
    return Kept(
        day,
        at,
        int(said["tries"]),
        dict(said["parked"]),
        frozenset(said["refused"]),
        said.get("rules", ""),
    )


def _record(folder: Path, kept: Kept) -> None:
    """The record written whole, then swapped in, after the bars it speaks of."""
    said = {"day": kept.day.isoformat(), "at": kept.at.isoformat(), "tries": kept.tries}
    said |= {"parked": dict(kept.parked), "refused": sorted(kept.refused), "rules": kept.rules}
    folder.mkdir(parents=True, exist_ok=True)
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


def _shelf(folder: Path, line: Line) -> tuple[Bar, ...] | None:
    """The older bars the head start shelved for a line, joined to the archive's; none if it
    never shelved any. They wait in the old daily folder until the import takes them in."""
    try:
        return store.read(folder / store.HISTORY, line.symbol)
    except FileNotFoundError:  # a line the head start never shelved
        return None


def pound_closes(hot: Path) -> store.Rates:
    """The pound's closes in dollars the long database holds (none while it is not yet kept):
    by them the store tells a bar in dollars among pounds from a move (R-RUNGS-16)."""
    try:
        held = bars.daily(hot, POUND)
    except (LookupError, FileNotFoundError):  # never kept: no close is held
        held = ()
    return {bar.day: bar.close for bar in held if DOLLARS[0] < bar.close < DOLLARS[1]}


def _kept_in(
    hot: Path,
    folder: Path,
    answers: Mapping[Line, store.Answer],
    day: date,
    first: Mapping[Line, store.Answer],
) -> list[Parked]:
    """The answers judged by the one store and kept in its long database as one round; the
    lines parked. A line is kept whole: its archive bars replace those the archive gave before."""
    parked, rates = [], pound_closes(hot)
    with bars.writing(hot) as round_:
        for line, answer in answers.items():
            shelf = _shelf(folder, line)
            kept, _faults, park = store.judge(
                line, answer, day, rates, shelf=shelf, broker=first.get(line)
            )
            round_.daily(line, kept)
            parked += [park] if park else []
    return parked


def _refresh(
    hot: Path,
    folder: Path,
    lines: Sequence[Line],
    now: datetime,
    ask: Ask[date, tuple[Bar, ...]],
    idle: bool,
    broker: Broker | None = None,
) -> Kept | None:
    """A venue's daily bars refreshed as far as they are owed at now, and the record of it;
    None when nothing was owed, and nothing asked. On an idle day, when no venue trades,
    only what the store does not yet hold is owed: bars before the next session, a refused
    line, and every line of a venue none of whose lines is clean. A day the store already
    holds is any whose sessions before it are all in the last refresh, across a weekend too."""
    readied, last = target(lines[0].venue, now), _kept(folder)
    if last is not None and last.rules != RULES:
        last = None  # kept under other store rules: cleaned again whole, as a first refresh
    same = last is not None and not _short(lines[0].venue, last, readied)
    if idle and same and last and not last.refused and len(last.parked) < len(lines):
        return None
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
    first = broker(asked, readied) if broker else {}
    refused = {
        line.symbol
        for line, answer in answers.items()
        if isinstance(answer, Refused) and isinstance(first.get(line, answer), Refused)
    }
    given = {line: answer for line, answer in answers.items() if line.symbol not in refused}
    found = _kept_in(hot, folder, given if same else answers, readied, first)
    parked = {symbol: why for symbol, why in before.items() if symbol not in map(_symbol, given)}
    parked |= {line.symbol: line.reason for line in found}
    kept = Kept(readied, now, tries, parked, frozenset(refused), RULES)
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
        last = _kept(home / DAILY / line.venue)
        if last is None or _short(line.venue, last, day):
            had = "never refreshed" if last is None else f"last readied for {last.day}"
            raise Stale(f"{line.symbol}: no {line.venue} bars before {day} are held: {had}")
        try:
            held[line] = tuple(bar for bar in bars.daily(home / HOT, line) if bar.day < day)
        except (LookupError, FileNotFoundError) as gone:  # never held, or no round has landed
            raise Stale(
                f"{line.symbol}: the long database holds no {line.venue} bars: {gone}"
            ) from gone
        parked |= {line.symbol} & set(last.parked)
    return held, frozenset(parked)


def pound(home: Path, day: date) -> Decimal:
    """THE DAY'S POUNDS PER DOLLAR, for any session, from the pound's closes kept before the day
    (desk.carry's one rule: one over the last close, carried over a UK-only holiday). Stale where
    the store holds none fresh enough: no dollar line is priced on it."""
    closes = pound_closes(home / HOT)
    last = venues.sessions("LSE", day - 10 * DAY, day - DAY)[-1:]
    known = {d: r for d in (day, *last) if (r := carry.pounds_per_dollar(closes, d))}
    if (rate := carry.carried(known, day)) is None:
        raise Stale(f"no pound in dollars is held fresh for {day}: {len(closes)} closes kept")
    return rate


def _reference(
    home: Path, now: datetime, ask: Ask[date, tuple[Bar, ...]], series: Sequence[Line]
) -> list[str]:
    """Each reference series kept from its first session once the US day has settled, and told
    in words; one the record already holds for the day is not asked, nor one refused kept."""
    day, told = target("US", now), list[str]()
    if day == now.date() or venues.sessions("US", now.date(), now.date()) != (now.date(),):
        return told
    for line in series:
        folder = home / DAILY / line.venue
        mark = folder / MARKS / f"{line.symbol}.kept"
        if mark.is_file() and mark.read_text(encoding="utf-8") == day.isoformat():
            continue
        answer = archive.gather([line], day, ask)[line]
        if isinstance(answer, Refused):
            told.append(f"{line.symbol}: reference series not kept: {answer.reason}")
            continue
        faults = archive.keep_reference(home / HOT, line, answer)
        mark.parent.mkdir(parents=True, exist_ok=True)
        mark.write_text(day.isoformat(), encoding="utf-8")
        told.append(f"{line.symbol}: reference kept before {day}, {len(faults)} faults listed")
    return told


def parked_live(hot: Path, lines: Sequence[Line], now: datetime) -> dict[str, str]:
    """EACH LINE NOT TO BE TRADED NOW, and why: a line in session for LATE or more with no ended
    five-minute bar in the last LATE (late or missing), or whose bars there are out of line."""
    parked = {}
    for line in lines:
        session = venues.open_at(line.venue, now)
        if session is None or now - session.open < LATE:
            continue
        try:
            held = bars.five(hot, line, now - LATE, now)
        except LookupError:  # the store never held a bar of the line: it is missing
            held = ()
        ended = [bar for bar in held if bar.start + live.BAR <= now]
        if faults := bars.checked(line, ended)[1] if ended else ["no ended bar"]:
            parked[line.symbol] = f"{faults[0]} in the last {LATE.seconds // 60} minutes"
    return parked


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


def keep(
    home: Path,
    now: datetime,
    lines: Sequence[Line] = LINES,
    daily: Ask[date, tuple[Bar, ...]] = archive.fetch,
    five: Ask[datetime, tuple[Five, ...]] | None = None,
    clock: Callable[[], float] = time.monotonic,
    ancient: Ask[date, tuple[Bar, ...]] = ANCIENT,
    series: Sequence[Line] = (*REFERENCE, *ADJUSTED, POUND),
    broker: Broker | None = None,
    back: Ask[datetime, tuple[Five, ...]] = keeper_live.recent,
) -> tuple[list[str], list[str]]:
    """WHATEVER IS OWED AT NOW, done once: what was done, in words, and of those the misses.
    Nothing is asked, and nothing said, on a day no venue trades and the store is whole."""
    if now.utcoffset() != timedelta(0):
        raise ValueError(f"{now!r} is not a moment in UTC")
    idle = not any(venues.sessions(venue, now.date(), now.date()) for venue in venues.RULES)
    ends, told = clock() + SPENT, []
    five = live.ibkr(home) if five is None else five
    for venue in sorted({line.venue for line in lines}):
        mine = [line for line in lines if line.venue == venue]
        kept = _refresh(
            home / HOT, home / DAILY / venue, mine, now, _within(daily, clock, ends), idle, broker
        )
        if kept is not None:
            told.append(_told(kept, mine))
            if YARDSTICK.symbol in kept.parked and YARDSTICK.symbol not in kept.refused:
                why = kept.parked[YARDSTICK.symbol]
                told.append(
                    (f"FIRST-LIGHT FAULT: the yardstick {YARDSTICK.symbol} is parked: {why}", True)
                )
        if venues.open_at(venue, now) or venues.open_at(venue, now - SETTLED):
            told.append(
                keeper_live.round_(
                    home / HOT, mine, now, _within(five, clock, ends), _within(back, clock, ends)
                )
            )
    spoken = [words for words, _ in told]
    spoken += _reference(home, now, _within(ancient, clock, ends), series)
    return spoken, [words for words, miss in told if miss]


def main(home: Path, now: datetime, args: Sequence[str] = ()) -> int:
    """THE COMMAND: what was done on one line each, a miss on the error stream, and 1 for it.
    `--live` takes one run of one-minute bars instead, `--roll` copies the live day's bars into
    the long database (R-RUNNER-12)."""
    missed: list[str] = []
    if args == ["--roll"]:
        done = [keeper_live.roll(home / HOT)]
    elif args == ["--live"]:
        ask = live.minutes(home, home / HOT)
        words, missed = keeper_live.minute_round(home / HOT, LINES, now, ask)
        done = [words]
    else:
        done, missed = keep(home, now)
        if stopped := parked_live(home / HOT, LINES, now):
            done.append(f"parked live, not traded: {stopped}")
    sys.stdout.write("".join(f"{line}\n" for line in done))
    sys.stderr.write("".join(f"MISSED: {line}\n" for line in missed))
    return int(bool(missed))


if __name__ == "__main__":
    sys.exit(main(Path(os.environ["KESTREL2_DATA"]), datetime.now(UTC), sys.argv[1:]))
