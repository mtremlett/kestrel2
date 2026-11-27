"""keeper_parts - the keeper's live-day judgement and its rounds: the polled round's pace, the lines
parked for late or faulty five-minute bars, each source's delay, and the roll-up round."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import date, datetime, timedelta
from pathlib import Path

from desk import archive, bars, history_write, keeper_live, live, venues
from desk.bars import Five
from desk.keeper_rotate import Kept
from desk.lines import LINES, POLLED_LINES, Line
from desk.store import Bar, Refused

DAILY, HOT = "daily", bars.LIVE
SETTLED = timedelta(minutes=30)
DAY = timedelta(days=1)
LATE = timedelta(minutes=15)  #: a line's five-minute bars are late, and it is parked, after this
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


def target(venue: str, now: datetime) -> date:
    """The day a venue's bars are readied for: today until its session is settled, else tomorrow."""
    day = now.date()
    trades = venues.sessions(venue, day, day) == (day,)
    return day if trades and now < venues.hours(venue, day).auction + SETTLED else day + DAY


def _short(venue: str, last: Kept | None, day: date) -> bool:
    """The venue's last refresh lacks a session before a day: none was made, or it traded since."""
    return last is None or bool(venues.sessions(venue, last.day, day - DAY))


def _reference(
    home: Path, now: datetime, ask: Callable[[Line, date], tuple[Bar, ...]], series: Sequence[Line]
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


def _told(kept: Kept, mine: Sequence[Line]) -> tuple[str, bool]:
    """A venue's refresh in words, and whether it was a miss."""
    clean, venue = len(mine) - len(kept.parked), mine[0].venue
    words = (
        f"{venue}: daily bars before {kept.day}: {clean} of {len(mine)} lines clean, "
        f"{len(kept.refused)} refused by the archive (asked {kept.tries} times today)"
        f"{''.join('; ' + note for note in kept.notes)}"
    )
    return words, len(mine) in (len(kept.refused), len(kept.parked))
