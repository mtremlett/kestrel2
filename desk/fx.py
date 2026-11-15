"""fx - THE POUND IN DOLLARS, AS THE STORE JUDGES A CHANGE OF CURRENCY BY IT. A step in a
line's close as large as that day's rate is a change of unit only if it lasts; a move the
market made, a crash that recovers, is kept."""

from __future__ import annotations

from bisect import bisect_right
from collections.abc import Mapping
from datetime import date, timedelta
from decimal import Decimal
from itertools import pairwise
from types import MappingProxyType

from desk.lines import Line

#: A one-for-one line's neighbouring closes in the ratio of that day's pound in dollars, within
#: this fraction, are one bar quoted in dollars beside one in pounds, if the step lasts (seen
#: 14 November 2026: IITU x0.662, VHYG x0.808, VUAG x0.791, IB1T x0.733, each below JUMP). A
#: leveraged line's real crashes sit as near the rate (5QQQ x0.770), so none of them is tested;
#: a bar already past JUMP is taken so within the wider FX_FAR.
FX_STEP, FX_FAR = Decimal("0.05"), Decimal("0.10")
#: The newest pound in dollars a day may be judged on is at most this old: a longer silence in
#: the rate is no rate.
RATE_AGE = timedelta(days=7)
Rates = Mapping[date, Decimal]  #: the pound's close in dollars, by day
NO_RATES: Rates = MappingProxyType({})


def rate_on(rates: Rates, day: date) -> Decimal | None:
    """The pound's newest close in dollars on or before day, if no older than RATE_AGE."""
    days = sorted(rates)
    at = bisect_right(days, day)
    return rates[days[at - 1]] if at and day - days[at - 1] <= RATE_AGE else None


def near_rate(ratio: Decimal, pound: Decimal | None, near: Decimal) -> bool:
    """The ratio of two closes is the pound's rate, or one over it, within near."""
    return pound is not None and any(abs(ratio / r - 1) <= near for r in (pound, 1 / pound))


def unit_steps(line: Line, closes: Mapping[date, Decimal], rates: Rates) -> frozenset[date]:
    """The days a plain line's close (by day, in order) steps by the day's pound in dollars, or
    its inverse, and stays there: every later close nearer the new close than the old. A crash
    that recovers (19% in March 2020) is the market's move."""
    if line.leverage != 1:
        return frozenset()
    steps = set()
    days = list(closes)
    for n, (before, day) in enumerate(pairwise(days), 1):
        ratio = closes[day] / closes[before]
        later = (closes[d] / closes[before] for d in days[n:])
        if near_rate(ratio, rate_on(rates, day), FX_STEP) and all(
            (x * x < ratio) if ratio < 1 else (x * x > ratio) for x in later
        ):
            steps.add(day)
    return frozenset(steps)
