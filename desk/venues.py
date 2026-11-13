"""venues - THE ONE CALENDAR. A venue trades on weekdays less its own holidays; a UK holiday
is not a US holiday. A year or a venue it does not know is refused, never guessed."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from datetime import date, timedelta
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


def _us(year: int) -> set[date]:
    thanksgiving = date(year, 11, 1) + timedelta((3 - date(year, 11, 1).weekday()) % 7 + 21)
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
