"""store_fx - when a step in a line's close is a change of currency, not a move of the market.

A step as large as the pound's rate in dollars is a bar quoted in the other currency only if it
lasts: a crash that recovers (18 March 2020, the gilt crisis) is the market's, and is kept."""

from __future__ import annotations

from bisect import bisect_right
from collections.abc import Iterable, Mapping
from datetime import date, timedelta
from decimal import Decimal

#: A one-for-one line's neighbouring closes in the ratio of that day's pound in dollars, within
#: this fraction, are a bar in dollars beside one in pounds, if the step lasts (IITU x0.662,
#: VUAG x0.791, each below JUMP). A leveraged line's real crashes sit as near the rate (5QQQ
#: x0.770), so only a stray bar of one is tested; one past JUMP is taken so within FX_FAR.
FX_STEP, FX_FAR = Decimal("0.05"), Decimal("0.10")
#: The newest pound in dollars a day may be judged on is at most this old.
RATE_AGE = timedelta(days=7)


def pound_on(rates: Mapping[date, Decimal], day: date) -> Decimal | None:
    """The pound's newest close in dollars on or before day, if no older than RATE_AGE."""
    days = sorted(rates)
    at = bisect_right(days, day)
    return rates[days[at - 1]] if at and day - days[at - 1] <= RATE_AGE else None


def same_as_pound(ratio: Decimal, pound: Decimal | None, within: Decimal) -> bool:
    """The ratio of two closes is the pound's rate, or one over it, within the given fraction."""
    return pound is not None and any(abs(ratio / r - 1) <= within for r in (pound, 1 / pound))


def lasting(base: Decimal, later: Iterable[Decimal], pound: Decimal | None) -> bool:
    """Every later close stays in the new unit, still the pound's rate from the close before the
    step: one that comes back is a move the market made and recovered from."""
    return all(same_as_pound(close / base, pound, FX_FAR) for close in later)
