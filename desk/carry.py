"""carry - THE POUND'S RATE ON A DAY LONDON IS SHUT: the one rule. A rate known for the day is
the day's. Else, on a day the US trades and London does not (a UK-only holiday: Easter Monday,
Boxing Day), the rate of the last London session is carried across, for at most
CARRIED US sessions. No other day is given a rate that is not its own (canon B3)."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date, timedelta
from decimal import Decimal

from desk.venues import sessions

CARRIED = 3  #: the most US sessions one London close is carried over


def carried(known: Mapping[date, Decimal], day: date) -> Decimal | None:
    """The rate for the day among those known by day, carried over a UK-only holiday as above;
    None where the rule gives none."""
    if day in known:
        return known[day]
    if not sessions("US", day, day) or sessions("LSE", day, day):
        return None
    last = sessions("LSE", day - timedelta(days=10), day - timedelta(days=1))[-1]
    if len(sessions("US", last + timedelta(days=1), day)) > CARRIED:
        return None
    return known.get(last)


def pounds_per_dollar(closes: Mapping[date, Decimal], day: date) -> Decimal | None:
    """One over the pound's last close in dollars before the day, to six places; fresh while no
    session shared by London and New York lies between that close and the day (a long holiday
    weekend is not a stale rate, a missing week is). None where there is none, or it is stale."""
    before = [d for d in closes if d < day]
    if not before:
        return None
    last = max(before)
    gap = timedelta(days=1)
    if set(sessions("LSE", last + gap, day - gap)) & set(sessions("US", last + gap, day - gap)):
        return None
    return (1 / closes[last]).quantize(Decimal("0.000001"))
