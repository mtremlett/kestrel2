"""venues - THE ONE CALENDAR. A venue trades on weekdays less its own holidays; a UK holiday
is not a US holiday. Each session has its hours: the open, the end of continuous trading and
the closing auction, in UTC, earlier on a half-day. A year or a venue it does not know is
refused, never guessed."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta, timezone
from functools import cache

KNOWN = range(2010, 2028)  #: the years whose closures below are complete

#: Closures no rule predicts: royal occasions, state funerals, a storm.
EXTRA = {
    "LSE": {
        date(2011, 4, 29),
        date(2012, 6, 5),
        date(2022, 6, 3),
        date(2022, 9, 19),
        date(2023, 5, 8),
    },
    "US": {date(2012, 10, 29), date(2012, 10, 30), date(2018, 12, 5), date(2025, 1, 9)},
}
#: UK bank holidays moved by proclamation: the rule's day -> the day actually shut.
MOVED = {
    date(2012, 5, 28): date(2012, 6, 4),
    date(2020, 5, 4): date(2020, 5, 8),
    date(2022, 5, 30): date(2022, 6, 2),
}


def _easter(year: int) -> date:
    """Western Easter Sunday, by the anonymous Gregorian algorithm."""
    a, b, c = year % 19, year // 100, year % 100
    d, e = divmod(b, 4)
    g = (8 * b + 13) // 25
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    m = (32 + 2 * e + 2 * i - h - k) % 7
    n = (a + 11 * h + 22 * m) // 451
    month, day = divmod(h + m - 7 * n + 114, 31)
    return date(year, month, day + 1)


def _monday(year: int, month: int, nth: int) -> date:
    """The nth Monday of a month; nth -1 is the last one."""
    if nth > 0:
        first = date(year, month, 1)
        return first + timedelta((7 - first.weekday()) % 7 + 7 * (nth - 1))
    last = date(year + month // 12, month % 12 + 1, 1) - timedelta(1)
    return last - timedelta(last.weekday())


def _substituted(days: Iterable[date]) -> set[date]:
    """UK rule: a holiday on a weekend, or on a day already taken, moves to the next free
    weekday."""
    taken: set[date] = set()
    for day in days:
        while day.weekday() >= 5 or day in taken:
            day += timedelta(1)
        taken.add(day)
    return taken


def _lse(year: int) -> set[date]:
    easter = _easter(year)
    fixed = {easter - timedelta(2), easter + timedelta(1)}
    fixed |= {_monday(year, 5, 1), _monday(year, 5, -1), _monday(year, 8, -1)}
    fixed = {MOVED.get(day, day) for day in fixed}
    christmas = _substituted([date(year, 12, 25), date(year, 12, 26)])
    return fixed | christmas | _substituted([date(year, 1, 1)])


def _observed(day: date) -> date:
    """US rule: a Saturday holiday is kept the Friday before, a Sunday one the Monday after."""
    return {5: day - timedelta(1), 6: day + timedelta(1)}.get(day.weekday(), day)


def _thanksgiving(year: int) -> date:
    """The fourth Thursday of November."""
    return date(year, 11, 1) + timedelta((3 - date(year, 11, 1).weekday()) % 7 + 21)


def _us(year: int) -> set[date]:
    thanksgiving = _thanksgiving(year)
    fixed = {_monday(year, 1, 3), _monday(year, 2, 3), _monday(year, 5, -1), _monday(year, 9, 1)}
    fixed |= {_easter(year) - timedelta(2), thanksgiving}
    #: A Saturday New Year falls back to the old year's 31 December, which is only ever looked
    #: up in the old year's own list, so the exchange stays open that day, as it does.
    dated = [date(year, 1, 1), date(year, 7, 4), date(year, 12, 25)]
    return fixed | {_observed(day) for day in dated + [date(year, 6, 19)] * (year >= 2022)}


RULES: dict[str, Callable[[int], set[date]]] = {"LSE": _lse, "US": _us}


@cache
def _shut(venue: str, year: int) -> frozenset[date]:
    if venue not in RULES or year not in KNOWN:
        raise ValueError(
            f"no calendar for venue {venue!r} in {year}: known {sorted(RULES)}, "
            f"{KNOWN.start}-{KNOWN.stop - 1}"
        )
    extra = {day for day in EXTRA[venue] if day.year == year}
    return frozenset(RULES[venue](year) | extra)


def sessions(venue: str, first: date, last: date) -> tuple[date, ...]:
    """Every day the venue trades from first to last, both included, oldest first."""
    days = (first + timedelta(n) for n in range((last - first).days + 1))
    return tuple(d for d in days if d.weekday() < 5 and d not in _shut(venue, d.year))


@dataclass(frozen=True)
class Clock:
    """A venue's local clock and trading day, as its exchange publishes them."""

    winter: int  #: hours ahead of UTC in winter; one more in summer
    summer: tuple[tuple[int, int], tuple[int, int]]
    """(month, day) twice: the clocks go forward on the first Sunday on or after the first,
    and back on the first Sunday on or after the second. No session is on a Sunday."""
    open: time  #: the opening auction uncrosses and continuous trading begins
    close: time  #: continuous trading ends
    early: time  #: the same, on a half-day
    auction: timedelta  #: from then to the closing auction's uncrossing: the official close
    half_days: Callable[[int], set[date]]  #: a year's candidates; one that is no session is none


def _lse_half(year: int) -> set[date]:
    """The last session before Christmas Day and the last of the year: Christmas Eve and New
    Year's Eve, or the working day before each."""
    spans = ((1, 24), (25, 31))
    return {sessions("LSE", date(year, 12, a), date(year, 12, b))[-1] for a, b in spans}


def _us_half(year: int) -> set[date]:
    """The day after Thanksgiving; 3 July and Christmas Eve, when they are sessions at all."""
    return {_thanksgiving(year) + timedelta(1), date(year, 7, 3), date(year, 12, 24)}


#: London is SETS, with a five-minute closing auction; New York's closing auction is at the
#: bell, and its clock rule is the one in force since 2007.
CLOCKS = {
    "LSE": Clock(
        winter=0,
        summer=((3, 25), (10, 25)),
        open=time(8),
        close=time(16, 30),
        early=time(12, 30),
        auction=timedelta(minutes=5),
        half_days=_lse_half,
    ),
    "US": Clock(
        winter=-5,
        summer=((3, 8), (11, 1)),
        open=time(9, 30),
        close=time(16),
        early=time(13),
        auction=timedelta(0),
        half_days=_us_half,
    ),
}


@dataclass(frozen=True)
class Hours:
    """One session of one venue: its moments, each timezone-aware UTC."""

    open: datetime  #: continuous trading begins
    close: datetime  #: continuous trading ends
    auction: datetime  #: the closing auction uncrosses; the session is over
    early: bool  #: a half-day


def _sunday(day: date) -> date:
    """The first Sunday on or after a day."""
    return day + timedelta((6 - day.weekday()) % 7)


def zone(venue: str, day: date) -> timezone:
    """The venue's wall clock on a day: how far it stands from UTC, summer or winter."""
    clock = CLOCKS[venue]
    forward, back = (_sunday(date(day.year, month, n)) for month, n in clock.summer)
    return timezone(timedelta(hours=clock.winter + (forward <= day < back)))


@cache
def hours(venue: str, day: date) -> Hours:
    """The hours of the venue's session on a day; a day it does not trade has none."""
    if sessions(venue, day, day) != (day,):
        raise ValueError(f"{venue} does not trade on {day}: it has no hours")
    clock = CLOCKS[venue]
    early = day in clock.half_days(day.year)
    opens, close = (
        datetime.combine(day, at, zone(venue, day)).astimezone(UTC)
        for at in (clock.open, clock.early if early else clock.close)
    )
    return Hours(opens, close, close + clock.auction, early)


def open_at(venue: str, moment: datetime) -> Hours | None:
    """The session the venue is in at a moment, from its open to its closing auction, both
    included: the round that falls on the auction collects the day's last bar. None when shut."""
    if moment.tzinfo is None:
        raise ValueError(f"{moment} has no time zone: the calendar cannot place it")
    day = moment.astimezone(UTC).date()  #: both venues' sessions lie within one UTC day
    if sessions(venue, day, day) != (day,):
        return None
    found = hours(venue, day)
    return found if found.open <= moment <= found.auction else None
