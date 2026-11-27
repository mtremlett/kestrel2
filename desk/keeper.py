"""keeper - THE STORE'S KEEPER: `python -m desk.keeper` does whatever the store is owed, and ends.

THE DAILY BARS of a venue's lines, cleaned by the one store, at the first call before any open and
once its session is settled (`target`): IBKR first, ROOM lines a call (`history.daily`); the archive
fills the rest, each newest bar named by its source, a differing close recorded, the broker's held.

THE FIVE-MINUTE ROUND is IBKR's alone (`live`); THE REFERENCE SERIES are kept daily after the US
close. A venue with no line answered or a line staler than its last session (`stale`) is a miss."""

from __future__ import annotations

import hashlib
import os
import sys
import time
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from functools import partial
from pathlib import Path
from typing import TypeVar

from desk import (
    archive,
    bars,
    carry,
    history,
    history_write,
    keeper_live,
    keeper_receipt,
    live,
    store,
    venues,
)
from desk.bars import Five
from desk.bars_form import entered
from desk.keeper_rotate import Kept, order
from desk.keeper_rotate import load as _kept
from desk.keeper_rotate import record as _record
from desk.lines import ADJUSTED, DOLLARS, LINES, POLLED_LINES, POUND, REFERENCE, YARDSTICK, Line
from desk.store import Bar, Parked, Refused
from desk.store_scope import judge as scoped_judge

DAILY, HOT = "daily", bars.LIVE
RULES = hashlib.sha256(  #: a hash of every desk/store*.py: a record of another is cleaned again
    b"\0".join(
        f.read_bytes().replace(b"\r\n", b"\n")
        for f in sorted(Path(store.__file__).parent.glob("store*.py"))
    )
).hexdigest()
SETTLED = timedelta(minutes=30)
HELD = SETTLED + timedelta(minutes=5 + 4)  #: by this long after the auction the closes are held
LATE = timedelta(minutes=15)  #: a line's five-minute bars are late, and it is parked, after this
ROOM = 6  #: lines one call asks the broker for, per venue: at its pacing, two venues fit in SPENT
TRIES = 6  #: the calls at which a line parked for a fault is asked again (half an hour)
SPENT = 150.0  #: seconds of a call in which the archive is still asked (runner: 240)
DAY = timedelta(days=1)
ANCIENT = partial(archive.fetch, since=archive.REFERENCE_SINCE)  #: the reference series
#: polled tickers by minutes: (floor, ceiling)
POLLED = {5: (27, 270), 15: (81, 810), 60: (324, 3240)}


def pace(minutes: int, rate: int, refusals: int) -> int:
    """The next round's tickers: a refusal halves the rate, a clean round adds a quarter."""
    floor, ceiling = POLLED[minutes]
    return max(floor, rate // 2) if refusals else min(ceiling, max(rate + 1, int(rate * 1.25)))


def polled(home: Path, now: datetime, minutes: int, ask: keeper_live.Minutes) -> str:
    """One `--polled <minutes>` run at the kept rate (floor first); keeps pace()'s next rate."""
    kept = home / f"polled_{minutes}.rate"
    rate = int(kept.read_text()) if kept.is_file() else POLLED[minutes][0]  # bounded: one integer
    words, _, refusals = keeper_live.polled_round(home / HOT, POLLED_LINES, now, ask, minutes, rate)
    (tmp := kept.with_suffix(".tmp")).write_text(str(pace(minutes, rate, refusals)))
    tmp.replace(kept)
    return words


When = TypeVar("When")
Read = TypeVar("Read")
Ask = Callable[[Line, When], Read]
Broker = Callable[[Sequence[Line], date], Mapping[Line, store.Answer]]  #: the first source


class Stale(LookupError):
    """The daily store lacks what was asked: a venue never refreshed, or a session since."""


def target(venue: str, now: datetime) -> date:
    """The day a venue's bars are readied for: today until its session is settled, else tomorrow."""
    day = now.date()
    trades = venues.sessions(venue, day, day) == (day,)
    return day if trades and now < venues.hours(venue, day).auction + SETTLED else day + DAY


def _short(venue: str, last: Kept | None, day: date) -> bool:
    """The venue's last refresh lacks a session before a day: none was made, or it traded since."""
    return last is None or bool(venues.sessions(venue, last.day, day - DAY))


def pound_closes(hot: Path) -> store.Rates:
    """The pound's closes in dollars held (R-RUNGS-16): a bar in dollars is told from a move."""
    return {bar.day: bar.close for bar in _held(hot, POUND) if DOLLARS[0] < bar.close < DOLLARS[1]}


def _source(kept: Sequence[Bar], answer: store.Answer, broker: store.Answer | None) -> str:
    """Who gave a line's newest kept bar: the broker, else the archive (and why not the broker)."""
    gave = [{b.day for b in a} if isinstance(a, list | tuple) else None for a in (broker, answer)]
    day = kept[-1].day if kept else None
    if day in (gave[0] or ()):
        return "IBKR"
    why = "not asked" if gave[0] is None else "gave none"
    return f"archive (IBKR {why})" if day in (gave[1] or ()) else "the shelf, or none"


def _dropped(held: Sequence[Bar], *answers: store.Answer | None) -> set[date]:
    """Days answered whose held bar is the answered one itself (R-DATA-77): an older one stays."""
    shown = {b.day: entered(b) for b in held}
    given = [b for a in answers if not isinstance(a, Refused | None) for b in a]
    return {b.day for b in given if shown.get(b.day, entered(b)) == entered(b)}


def _held(hot: Path, line: Line) -> tuple[Bar, ...]:
    """The daily bars the store shows for a line, none if never kept."""
    try:
        return tuple(bars.daily(hot, line))
    except (LookupError, FileNotFoundError):  # never kept: nothing stands over the archive
        return ()


def _standing(hot: Path, line: Line, day: date, broker: store.Answer | None) -> store.Answer | None:
    """The bars standing first: the broker's if given, else those the store holds (R-RUNNER-341)."""
    held = tuple(b for b in _held(hot, line) if b.day >= day - history.RECENT)
    return broker if isinstance(broker, list | tuple) else held or broker


def _kept_in(
    hot: Path,
    answers: Mapping[Line, store.Answer],
    day: date,
    first: Mapping[Line, store.Answer],
    standing: bool = True,
) -> tuple[list[Parked], tuple[str, ...]]:
    """Answers judged by the one store, kept as one round: lines parked, sources in words."""
    parked, rates, named, said, ibkr, judged = (
        [],
        pound_closes(hot),
        dict[str, list[str]](),
        [],
        [],
        [],
    )
    for line, answer in answers.items():  # every line judged first, outside any round
        broker = first.get(line)
        shelf = bars.bridged(hot, line, day, None, answer, broker)
        stands = _standing(hot, line, day, broker) if standing else broker
        kept, faults, park = scoped_judge(line, answer, day, rates, shelf=shelf, broker=stands)
        held, gave = _held(hot, line), broker if isinstance(broker, list | tuple) else ()
        theirs = {(g.day, entered(g)) for g in gave}
        ibkr.append((line, [b for b in kept if (b.day, entered(b)) in theirs]))
        standing_bars = frozenset(held)
        fresh = [b for b in kept if b not in standing_bars]  # a held bar keeps its label
        judged.append((line, fresh, _dropped(held, answer, broker) - {b.day for b in kept}))
        parked += [park] if park else []
        named.setdefault(_source(kept, answer, broker), []).append(line.symbol)
        said += [f"{line.symbol}: {f.what}, held" for f in faults if "(broker)" in f.what]
    with bars.writing(hot) as round_:  # the round holds the lock only while it writes
        for line, fresh, withdrawn in judged:
            round_.daily(line, fresh, withdrawn=withdrawn)
    with bars.writing(hot, bars.Source.IBKR) as round_:  # the broker's own bars, so labelled
        for line, own in ibkr:
            round_.days(line, own)
    return parked, (*(f"newest bar from {k}: {', '.join(v)}" for k, v in named.items()), *said)


def _due(last: Kept | None, lines: Sequence[Line], now: datetime) -> tuple[list[Line], int]:
    """The lines asked on this call and its number: all on a date's first, else those still owed."""
    if last is None or last.at.date() != now.date():
        return list(lines), 1
    again = last.refused
    if last.tries < TRIES or len(last.parked) == len(lines):  # as a parked line: TRIES calls
        again |= last.unasked | set(last.parked)
    return [line for line in lines if line.symbol in again], last.tries + 1


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
    asked, tries = _due(last if same else None, lines, now)
    if not asked:
        return None
    answers = archive.gather(asked, readied, ask)
    ordered = order(asked, last.tried if last and same else ())
    first = broker(ordered[:ROOM], readied) if broker else {}  # IBKR first, the yardstick first
    heard = {ln for ln, got in first.items() if isinstance(got, list | tuple)}
    unasked = frozenset(ln.symbol for ln in asked if broker and ln not in heard)
    refused = {ln.symbol for ln, a in answers.items() if isinstance(a, Refused) and ln not in heard}
    given = {line: answer for line, answer in answers.items() if line.symbol not in refused}
    found, notes = _kept_in(hot, given if same else answers, readied, first, last is not None)
    parked = {
        symbol: why for symbol, why in before.items() if symbol not in {ln.symbol for ln in given}
    }
    parked |= {line.symbol: line.reason for line in found}
    kept = Kept(
        readied,
        now,
        tries,
        parked,
        frozenset(refused),
        RULES,
        unasked,
        frozenset(ln.symbol for ln in first),
        notes if broker else (),
    )
    _record(folder, kept)
    return kept


def saved(
    home: Path, day: date, lines: Sequence[Line] = LINES
) -> tuple[dict[Line, tuple[Bar, ...]], frozenset[str]]:
    """THE PRICE STORE'S DOOR: every line's daily bars before a day, and the symbols parked;
    Stale if a venue's last refresh missed a session."""
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
        mark = folder / "reference" / f"{line.symbol}.kept"
        if mark.is_file() and mark.read_text(encoding="utf-8") == day.isoformat():
            continue
        answer = archive.gather([line], day, ask)[line]
        if isinstance(answer, Refused):
            told.append(f"{line.symbol}: reference series not kept: {answer.reason}")
            continue
        faults = archive.keep_reference(home / HOT, line, answer, only_new=line in LINES)
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
    """EACH LINE NOT TO BE TRADED NOW, and why: no ended bar for LATE, or bars out of line."""
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
        last = (days := _held(hot, line)) and days[-1].day or None  # none held: stale
        if due and (last is None or last < due[0]):
            told.append(f"{line.symbol}: daily bars end {last}, not the {line.venue} {due[0]}")
    return told


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
    told += keeper_live.rounds(  # the fast round first, under half the call's time
        home / HOT, lines, now, _within(five, clock, clock() + SPENT / 2), back, SETTLED
    )
    if (home / HOT).is_file():
        keeper_live.roll(home / HOT)  # the long database holds this round's bars, not tonight's
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
    again = _within(ancient, clock, ends)
    spoken = [words for words, _ in told] + _reference(home, now, again, series)
    return spoken, [words for words, miss in told if miss]


def rolled(hot: Path, lines: Sequence[Line], now: datetime) -> list[str]:
    """THE ROLL-UP ROUND: each line's held five-minute bars built into 15m, 30m, 1h and 4h bars
    and its daily bars into weekly ones, through the one writer, marked rollup:<from>; a partial
    span writes nothing, and a round that built nothing says nothing.
    Twice: the 30m bars of the first pass are the second's 1h and 4h."""
    long = bars.files(hot)[bars.DAILY]
    if not (hot.is_file() and long.is_file()):
        return []
    since = history_write.recent(now)  # the whole history is rolled and judged nightly (quality)
    landed = sum(history_write.roll(hot, line, now, since) for line in lines for _ in range(2))
    faults = [f"FAULT {f}" for line in lines for f in history_write.clashes(hot, line, now, since)]
    return faults + [
        f"roll-up: {landed} coarser bars built from the five-minute and daily bars"
    ] * bool(landed)


def main(home: Path, now: datetime, args: Sequence[str] = (), broker: Broker | None = None) -> int:
    """THE COMMAND: what was done, a line each; a miss on stderr, exit 1. `--live`: one-minute bars;
    `--polled 5|15|60`: a ramped round; `--roll`: the live day copied to the long database."""
    missed: list[str] = []
    if args == ["--roll"]:
        done = [keeper_live.roll(home / HOT)]
    elif args == ["--live"]:
        ask = live.minutes(home, home / HOT)
        words, missed = keeper_live.minute_round(home / HOT, LINES, now, ask)
        done = [words]
    elif len(args) == 2 and args[0] == "--polled":
        done = [polled(home, now, int(args[1]), live.minutes(home, home / HOT))]
    else:
        done, missed = keep(home, now, broker=broker or history.daily(now, home=home))
        done += rolled(home / HOT, LINES, now)
        if stopped := parked_live(home / HOT, LINES, now):
            done.append(f"parked live, not traded: {stopped}")
        if late := delays(home / HOT, LINES, now):
            done.append(f"five-minute delay in minutes, by line: {late}")
        missed += [f"stale: {words}" for words in stale(home / HOT, LINES, now)]
    if done or missed:
        keeper_receipt.write(home, now, done, missed, keeper_receipt.newest(home / HOT, LINES))
    sys.stdout.write("".join(f"{line}\n" for line in done))
    sys.stderr.write("".join(f"MISSED: {line}\n" for line in missed))
    return int(bool(missed))


if __name__ == "__main__":
    sys.exit(main(Path(os.environ["KESTREL2_DATA"]), datetime.now(UTC), sys.argv[1:]))
