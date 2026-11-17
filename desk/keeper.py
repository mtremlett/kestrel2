"""keeper - THE STORE'S KEEPER: one command, `python -m desk.keeper`, that does whatever the store
is owed when called, and ends; the runner calls it every five minutes of a weekday. On a day no
venue trades it ends at once, unless the store lacks bars before a venue's next session.

THE DAILY BARS of a venue's lines, cleaned by the one store, at the first call before any open and
once its session is over and SETTLED has passed (`target`). IBKR is asked first, ROOM lines a call
(`history.daily`, R-RUNNER-276, his ruling of 17 November); the archive fills what it gives none,
each line's newest bar named by its source, a close the two differ on recorded and the broker's
held. A record says what was held and who is parked; the door (`saved`) reads no bars it does not
cover. A line refused, or the broker not asked, is asked again; one parked, for TRIES calls.

THE FIVE-MINUTE ROUND, in each venue's hours, comes from IBKR's paper gateway alone (`live`); the
archive only fills past gaps. THE REFERENCE SERIES (SPY, the pound in dollars) are kept once a day
after the US close. A venue with no line answered or clean is a miss (exit 1), as is a line whose
newest daily bar is older than its venue's last settled session (`stale`)."""

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

from desk import archive, bars, carry, history, keeper_live, live, store, venues
from desk.bars import Five
from desk.lines import ADJUSTED, DOLLARS, LINES, POUND, REFERENCE, YARDSTICK, Line
from desk.store import Bar, Parked, Refused

#: In the data folder: each venue's record of its last refresh (no prices), and the short database.
DAILY, HOT = "daily", bars.LIVE
MARKS = "reference"  #: beside a venue's record, the day each reference series was last kept
RECEIPTS = "receipts"  #: in the data folder: a file a day, a line for each call that did anything
RECORD = "kept.json"  #: in each venue's folder of the daily store: its last refresh
#: THE STORE RULES' VERSION (a hash of desk/store.py): a record of another is cleaned again.
RULES = hashlib.sha256(Path(store.__file__).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
SETTLED = timedelta(minutes=30)
HELD = SETTLED + timedelta(minutes=5 + 4)  #: by this long after the auction the closes are held
LATE = timedelta(minutes=15)  #: a line's five-minute bars are late, and it is parked, after this
ROOM = 6  #: lines one call asks the broker for, per venue: at its pacing, two venues fit in SPENT
TRIES = 6  #: the calls at which a line parked for a fault is asked again (half an hour)
SPENT = 150.0  #: seconds of a call in which the archive is still asked (runner: 240)
DAY = timedelta(days=1)
ANCIENT = partial(archive.fetch, since=archive.REFERENCE_SINCE)  #: the reference series
When = TypeVar("When")
Read = TypeVar("Read")
Ask = Callable[[Line, When], Read]
#: The broker's daily bars for lines before a day: the store's first source (R-RUNNER-189).
Broker = Callable[[Sequence[Line], date], Mapping[Line, store.Answer]]


class Stale(LookupError):
    """The daily store lacks what was asked: a venue never refreshed, or a session since."""


@dataclass(frozen=True)
class Kept:
    """A venue's last refresh of its daily bars, as its record keeps it."""

    day: date  #: the day it readied: every session of the venue before it was asked for
    at: datetime  #: when the archive was last asked
    tries: int  #: how many calls have asked for this day on this date
    parked: Mapping[str, str]  #: each parked line's symbol, and why
    refused: frozenset[str]  #: those of them the archive would not answer for
    rules: str = ""  #: the store rules' version it was cleaned under; none in an old record
    unasked: frozenset[str] = frozenset()  #: lines the broker was not asked or refused: asked again
    notes: tuple[str, ...] = ()  #: each source of a newest bar, and each disagreement of sources


def _kept(folder: Path) -> Kept | None:
    """A venue's record; none before its first refresh."""
    if not (folder / RECORD).is_file():
        return None
    said = json.loads((folder / RECORD).read_text(encoding="utf-8"))
    day, at = date.fromisoformat(said.pop("day")), datetime.fromisoformat(said.pop("at"))
    for names in ("refused", "unasked"):  # an old record has no unasked
        said[names] = frozenset(said.get(names, ()))
    return Kept(day, at, **said)


def _record(folder: Path, kept: Kept) -> None:
    """The record written whole, then swapped in, after the bars."""
    said = {"day": kept.day.isoformat(), "at": kept.at.isoformat(), "tries": kept.tries}
    said |= {"parked": dict(kept.parked), "refused": sorted(kept.refused), "rules": kept.rules}
    said["unasked"] = sorted(kept.unasked)
    folder.mkdir(parents=True, exist_ok=True)
    part = folder / f"{RECORD}.part"
    part.write_text(json.dumps(said, indent=1), encoding="utf-8")
    part.replace(folder / RECORD)


def target(venue: str, now: datetime) -> date:
    """The day a venue's bars are readied for: today until its session is over and SETTLED has
    passed, else tomorrow."""
    day = now.date()
    trades = venues.sessions(venue, day, day) == (day,)
    return day if trades and now < venues.hours(venue, day).auction + SETTLED else day + DAY


def _short(venue: str, last: Kept | None, day: date) -> bool:
    """The venue's last refresh lacks a session before a day: none was made, or it traded since."""
    return last is None or bool(venues.sessions(venue, last.day, day - DAY))


def _shelf(folder: Path, line: Line) -> tuple[Bar, ...] | None:
    """The older bars the head start shelved for a line; none if none."""
    try:
        return store.read(folder / store.HISTORY, line.symbol)
    except FileNotFoundError:
        return None  # a line the head start never shelved


def pound_closes(hot: Path) -> store.Rates:
    """The pound's closes in dollars held (R-RUNGS-16): a bar in dollars is told from a move."""
    try:
        held = bars.daily(hot, POUND)
    except (LookupError, FileNotFoundError):  # never kept: no close is held
        held = ()
    return {bar.day: bar.close for bar in held if DOLLARS[0] < bar.close < DOLLARS[1]}


def _source(kept: Sequence[Bar], answer: store.Answer, broker: store.Answer | None) -> str:
    """Who gave a line's newest kept bar: the broker, else the archive (and why not the broker)."""
    gave = [{b.day for b in a} if isinstance(a, list | tuple) else None for a in (broker, answer)]
    day = kept[-1].day if kept else None
    if day in (gave[0] or ()):
        return "IBKR"
    why = "not asked" if gave[0] is None else "gave none"
    return f"archive (IBKR {why})" if day in (gave[1] or ()) else "the shelf, or none"


def _kept_in(
    hot: Path,
    folder: Path,
    answers: Mapping[Line, store.Answer],
    day: date,
    first: Mapping[Line, store.Answer],
) -> tuple[list[Parked], tuple[str, ...]]:
    """The answers judged by the one store and kept as one round, whole; the lines parked, and in
    words each source of a newest bar and each close the broker and the archive differ on."""
    parked, rates, named, said = [], pound_closes(hot), dict[str, list[str]](), []
    with bars.writing(hot) as round_:
        for line, answer in answers.items():
            broker = first.get(line)
            shelf = bars.bridged(hot, line, day, _shelf(folder, line), answer, broker)
            kept, faults, park = store.judge(line, answer, day, rates, shelf=shelf, broker=broker)
            round_.daily(line, kept)
            parked += [park] if park else []
            named.setdefault(_source(kept, answer, broker), []).append(line.symbol)
            said += [f"{line.symbol}: {f.what}, held" for f in faults if "(broker)" in f.what]
    return parked, (*(f"newest bar from {k}: {', '.join(v)}" for k, v in named.items()), *said)


def _refresh(
    hot: Path,
    folder: Path,
    lines: Sequence[Line],
    now: datetime,
    ask: Ask[date, tuple[Bar, ...]],
    idle: bool,
    broker: Broker | None = None,
) -> Kept | None:
    """A venue's daily bars refreshed as far as owed, and the record; None when nothing was owed."""
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
        again = last.refused
        if last.tries < TRIES or len(last.parked) == len(lines):  # as a parked line: TRIES calls
            again |= last.unasked | set(last.parked)
        asked, tries = [line for line in lines if line.symbol in again], last.tries + 1
    if not asked:
        return None
    answers = archive.gather(asked, readied, ask)
    first = broker(asked[:ROOM], readied) if broker else {}  # IBKR first
    heard = {ln for ln, got in first.items() if isinstance(got, list | tuple)}
    unasked = frozenset(ln.symbol for ln in asked if broker and ln not in heard)
    refused = {ln.symbol for ln, a in answers.items() if isinstance(a, Refused) and ln not in heard}
    given = {line: answer for line, answer in answers.items() if line.symbol not in refused}
    found, notes = _kept_in(hot, folder, given if same else answers, readied, first)
    parked = {
        symbol: why for symbol, why in before.items() if symbol not in {ln.symbol for ln in given}
    }
    parked |= {line.symbol: line.reason for line in found}
    kept = Kept(
        readied, now, tries, parked, frozenset(refused), RULES, unasked, notes if broker else ()
    )
    _record(folder, kept)
    return kept


def saved(
    home: Path, day: date, lines: Sequence[Line] = LINES
) -> tuple[dict[Line, tuple[Bar, ...]], frozenset[str]]:
    """THE PRICE STORE'S DOOR: every line's daily bars before a day, as last refreshed, and the
    symbols parked. A venue with a session its last refresh did not ask for is Stale."""
    held: dict[Line, tuple[Bar, ...]] = {}
    parked: set[str] = set()
    for line in lines:
        last = _kept(home / DAILY / line.venue)
        if last is None or _short(line.venue, last, day):
            had = "never refreshed" if last is None else f"last readied for {last.day}"
            raise Stale(f"{line.symbol}: no {line.venue} bars before {day} are held: {had}")
        try:
            held[line] = tuple(bar for bar in bars.daily(home / HOT, line) if bar.day < day)
        except (LookupError, FileNotFoundError) as e:  # never held, or no round has landed
            raise Stale(f"{line.symbol}: the long database holds no {line.venue} bars: {e}") from e
        parked |= {line.symbol} & set(last.parked)
    return held, frozenset(parked)


def pound(home: Path, day: date) -> Decimal:
    """THE DAY'S POUNDS PER DOLLAR from the closes kept (desk.carry's rule); Stale if none."""
    closes = pound_closes(home / HOT)
    last = venues.sessions("LSE", day - 10 * DAY, day - DAY)[-1:]
    known = {d: r for d in (day, *last) if (r := carry.pounds_per_dollar(closes, d))}
    if (rate := carry.carried(known, day)) is None:
        raise Stale(f"no pound in dollars is held fresh for {day}: {len(closes)} closes kept")
    return rate


def _reference(
    home: Path, now: datetime, ask: Ask[date, tuple[Bar, ...]], series: Sequence[Line]
) -> list[str]:
    """Each reference series kept once the US day has settled, in words; not asked twice a day."""
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


def _ended(hot: Path, line: Line, now: datetime) -> list[Five] | None:
    """A line's ended bars of the last LATE; none until its venue has been open for LATE."""
    session = venues.open_at(line.venue, now)
    if session is None or now - session.open < LATE:
        return None
    try:
        held = bars.five(hot, line, now - LATE, now)
    except LookupError:  # the store never held a bar of the line: it is missing
        return []
    return [bar for bar in held if bar.start + live.BAR <= now]


def parked_live(hot: Path, lines: Sequence[Line], now: datetime) -> dict[str, str]:
    """EACH LINE NOT TO BE TRADED NOW, and why: in session for LATE with no ended bar in the last
    LATE, or whose bars there are out of line."""
    parked = {}
    for line in lines:
        ended = _ended(hot, line, now)
        if ended is not None and (
            faults := bars.checked(line, ended)[1] if ended else ["no ended bar"]
        ):
            parked[line.symbol] = f"{faults[0]} in the last {LATE.seconds // 60} minutes"
    return parked


def delays(hot: Path, lines: Sequence[Line], now: datetime) -> dict[str, int]:
    """THE SOURCE'S DELAY: minutes since each line's newest ended bar ended; parked lines absent."""
    found = {line.symbol: _ended(hot, line, now) for line in lines}
    return {s: (now - (e[-1].start + live.BAR)).seconds // 60 for s, e in found.items() if e}


def stale(hot: Path, lines: Sequence[Line], now: datetime) -> list[str]:
    """EACH LINE STALER THAN ONE SESSION: its newest daily bar precedes its venue's last session."""
    told = []
    for line in lines:
        ready = target(line.venue, now)
        due = venues.sessions(line.venue, ready - 10 * DAY, ready - DAY)[-1:]
        try:
            last = bars.daily(hot, line)[-1].day
        except (LookupError, FileNotFoundError, IndexError):  # none held: stale
            last = None
        if due and (last is None or last < due[0]):
            told.append(f"{line.symbol}: daily bars end {last}, not the {line.venue} {due[0]}")
    return told


def receipt(home: Path, now: datetime, done: list[str], missed: list[str]) -> None:
    """The call's dated receipt: one line appended to the day's file in `receipts`."""
    (folder := home / RECEIPTS).mkdir(exist_ok=True)
    with (folder / f"{now.date()}.jsonl").open("a", encoding="utf-8") as out:
        out.write(json.dumps({"at": now.isoformat(), "done": done, "missed": missed}) + chr(10))


def _within(ask: Ask[When, Read], clock: Callable[[], float], ends: float) -> Ask[When, Read]:
    """The question, asked while the call's time lasts."""

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
        f"{''.join('; ' + note for note in kept.notes)}"
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
    """WHATEVER IS OWED AT NOW, done once: what was done, in words, and the misses among it."""
    if now.utcoffset() != timedelta(0):
        raise ValueError(f"{now!r} is not a moment in UTC")
    idle = not any(venues.sessions(venue, now.date(), now.date()) for venue in venues.RULES)
    ends, told = clock() + SPENT, []
    five = live.ibkr(home) if five is None else five
    for venue in sorted({line.venue for line in lines}):
        mine = [line for line in lines if line.venue == venue]
        ask = _within(daily, clock, ends)
        kept = _refresh(home / HOT, home / DAILY / venue, mine, now, ask, idle, broker)
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


def main(home: Path, now: datetime, args: Sequence[str] = (), broker: Broker | None = None) -> int:
    """THE COMMAND: what was done, a line each; a miss on stderr, and exit 1. `--live`: one run of
    one-minute bars; `--roll`: the live day copied to the long database."""
    missed: list[str] = []
    if args == ["--roll"]:
        done = [keeper_live.roll(home / HOT)]
    elif args == ["--live"]:
        ask = live.minutes(home, home / HOT)
        words, missed = keeper_live.minute_round(home / HOT, LINES, now, ask)
        done = [words]
    else:
        done, missed = keep(home, now, broker=broker or history.daily(now))
        if stopped := parked_live(home / HOT, LINES, now):
            done.append(f"parked live, not traded: {stopped}")
        if late := delays(home / HOT, LINES, now):
            done.append(f"five-minute delay in minutes, by line: {late}")
        missed += [f"stale: {words}" for words in stale(home / HOT, LINES, now)]
    if done or missed:
        receipt(home, now, done, missed)
    sys.stdout.write("".join(f"{line}\n" for line in done))
    sys.stderr.write("".join(f"MISSED: {line}\n" for line in missed))
    return int(bool(missed))


if __name__ == "__main__":
    sys.exit(main(Path(os.environ["KESTREL2_DATA"]), datetime.now(UTC), sys.argv[1:]))
