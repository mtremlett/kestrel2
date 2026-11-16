"""store_fx - when a step in a London line's close is the pound's rate, a change of currency.

A step is a change of currency only for a line quoted in pounds (the archive refuses any other
unit, so a line's currency is the instrument master's), and only if it lasts: every close
after it stays at the new level. A fall that recovers is the market's, however near the rate."""

from __future__ import annotations

from bisect import bisect_right
from collections.abc import Mapping, Sequence
from datetime import date, timedelta
from decimal import Decimal
from types import MappingProxyType

from desk.lines import Line

#: A one-for-one line's neighbouring closes in the ratio of that day's pound in dollars, within
#: this fraction, are a bar in dollars beside one in pounds, not a market move (IITU x0.662,
#: VUAG x0.791, each below JUMP). A leveraged line's real crashes sit as near the rate (5QQQ
#: x0.770), so only a stray bar of one is tested; one past JUMP is taken so within FX_FAR.
FX_STEP, FX_FAR = Decimal("0.05"), Decimal("0.10")
#: The newest pound in dollars a day may be judged on is at most this old.
RATE_AGE = timedelta(days=7)
#: A step lasts if each of this many closes after it stays at the new level (18 March 2020).
FX_LAST = 10
Rates = Mapping[date, Decimal]  #: the pound's close in dollars, by day
NO_RATES: Rates = MappingProxyType({})


def pound(line: Line, rates: Rates, day: date) -> Decimal | None:
    """The pound's newest close in dollars on or before day, if no older than RATE_AGE, for a
    plain line quoted in pounds; None for any other, which no pound's step can judge."""
    days = sorted(rates)
    at = bisect_right(days, day)
    fresh = at and day - days[at - 1] <= RATE_AGE
    return rates[days[at - 1]] if fresh and line.leverage == 1 and line.currency == "GBP" else None


def near_rate(ratio: Decimal, rate: Decimal | None, near: Decimal) -> bool:
    """The ratio of two closes is the pound's rate, or one over it, within near."""
    return rate is not None and any(abs(ratio / r - 1) <= near for r in (rate, 1 / rate))


def lasting_step(
    step: Decimal, earlier: Sequence[Decimal], later: Sequence[Decimal], rate: Decimal | None
) -> bool:
    """A close's ratio to the one before it (step) is the pound's rate or one over it, each of
    the next FX_LAST closes' ratios stays there, and it is no return to where one of the last
    FX_LAST closes before stood: that is the end of a fall, which is the market's."""
    if rate is None or any(abs(step / e - 1) <= FX_STEP for e in earlier[-FX_LAST:]):
        return False
    return any(
        abs(step / r - 1) <= FX_STEP and all(abs(c / r - 1) <= FX_FAR for c in later[:FX_LAST])
        for r in (rate, 1 / rate)
    )
