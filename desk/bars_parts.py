"""bars_parts - what lets a five-minute bar into the fast store, split from desk/bars.py: each
bar judged on its own against its venue's calendar, then the line's bars against one another
and the closes held (DAT-11). desk/bars.py imports `checked` and passes it on."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import replace
from datetime import datetime
from decimal import Decimal
from statistics import median_low

from desk import venues
from desk.lines import Line
from desk.spans import Five
from desk.store import FAR, JUMP, STRETCH


def _entered(line: Line, bar: Five) -> Five | str:
    """The bar as it enters the store, or why it cannot be true on its own: the daily store's
    checks, made at five minutes. A bar belongs to a session's continuous trading: one that
    starts before the open, or at the close or after it, is no bar of that session."""
    prices, at = (bar.open, bar.high, bar.low, bar.close), f"{bar.start:%Y-%m-%d %H:%M}"
    known = bar.start.year in venues.HOURS_YEARS
    session = venues.open_at(line.venue, bar.start) if known else None
    if bar.start.date() in line.suspended:
        return f"{at} has a bar, yet {line.symbol} records the day as suspended"
    if session is None or bar.start >= session.close:
        return f"{at} is outside the trading hours of the {line.venue} calendar"
    if not all(p.is_finite() and p > 0 for p in prices) or bar.volume < 0:
        return f"{at} has a price or volume that cannot be"
    ends = (bar.open, bar.close)
    reach = (bar.low * (1 - STRETCH), bar.high * (1 + STRETCH))
    if not bar.low <= bar.high or not reach[0] <= min(ends) <= max(ends) <= reach[1]:
        return f"{at} has an open or close outside its high and low"
    return replace(bar, high=max(bar.high, *ends), low=min(bar.low, *ends))


def _near(bar: Five, other: Five) -> bool:
    """The bar's whole range lies within a market's move of the other's close."""
    return other.close / JUMP <= bar.low and bar.high <= other.close * JUMP


def checked(
    line: Line, bars: Iterable[Five], held: Sequence[Decimal] = ()
) -> tuple[list[Five], list[str]]:
    """The bars of one line that can be true, oldest first, and every fault found on the way.
    A moment given twice differently keeps neither bar. A bar a hundredfold from the middle
    of the closes held, or with none held the middle close of all that was given, is in a
    wrong unit, and is not kept. Any other move further
    than the store believes a market makes may be real: its bar is kept, and the move is a
    fault. Five minutes in which nothing traded have no bar, and that is no fault."""
    faults: list[str] = []
    given: dict[datetime, set[Five]] = {}
    for bar in bars:
        given.setdefault(bar.start, set()).add(bar)
    sound: list[Five] = []
    for start, said in sorted(given.items()):
        entered = _entered(line, next(iter(said))) if len(said) == 1 else None
        if isinstance(entered, Five):
            sound.append(entered)
        else:
            faults.append(entered or f"{start:%Y-%m-%d %H:%M} given {len(said)} ways; none kept")
    if not sound:
        return [], faults
    middle = median_low(held or [bar.close for bar in sound])
    kept: list[Five] = []
    for bar in sound:
        at = f"{bar.start:%Y-%m-%d %H:%M}"
        if any(p >= middle * FAR or p * FAR <= middle for p in (bar.high, bar.low)):
            faults.append(f"{at} is a hundredfold from the bars around it: a wrong unit")
            continue
        if kept and not (_near(bar, kept[-1]) and _near(kept[-1], bar)):
            faults.append(f"{at} moved from {kept[-1].close} to {bar.close}")
        kept.append(bar)
    return kept, faults


#: A held day a fresh bar changes is copied here, with who replaced it, before the bar takes it.
NOTE = (
    "INSERT INTO correction SELECT venue, symbol, span, at, open, high, low, close, volume,"
    " source, ? FROM bar WHERE venue = ? AND symbol = ? AND span = ? AND at = ?"
)
HOLDING = (
    "SELECT at, open, high, low, close, volume, source FROM bar"
    " WHERE venue = ? AND symbol = ? AND span = ? AND at >= ? AND at <= ?"
)
#: A day the desk judged untrue: its raw row stays in `bar`, but no reader is given it.
WITHDRAW = "INSERT OR IGNORE INTO withdrawn VALUES (?, ?, ?, ?)"
RESTORE = "DELETE FROM withdrawn WHERE venue = ? AND symbol = ? AND span = ? AND at = ?"
OTHERS = (
    "SELECT at, open, high, low, close FROM bar WHERE venue = ? AND symbol = ? AND span = ?"
    " AND source != ? AND at >= ? AND at <= ?"
)
SOURCES = (
    "SELECT source, count(*) FROM bar"
    " WHERE venue = ? AND symbol = ? AND span = ? AND at >= ? AND at < ? GROUP BY source"
)
NEWEST = (
    "SELECT at, source FROM bar WHERE venue = ? AND symbol = ? AND span = ? AND at >= ? AND at < ?"
    " ORDER BY at DESC LIMIT 1"
)
CLOSES = "SELECT close FROM bar WHERE venue = ? AND symbol = ? AND span = ? AND at >= ?"
READ = (
    "SELECT at, open, high, low, close, volume FROM bar"
    " WHERE venue = ? AND symbol = ? AND span = ? AND at >= ? AND at < ?"
    " AND NOT EXISTS (SELECT 1 FROM withdrawn w WHERE w.venue = bar.venue AND"
    " w.symbol = bar.symbol AND w.span = bar.span AND w.at = bar.at) ORDER BY at"
)
