"""eponymous_keltner_channel_trend - Keltner's channel trend rule, ported as a rule under the one
template (SET 1 of the eponymous strategies, R-RUNNER-65). Its family is bands. The paper desk
does not trade it.

AUTHOR: Chester W. Keltner. SOURCE: How to Make Money in Commodities (1960). The book's rule: the
centre line is the 10-day simple average of the typical price (high plus low plus close, over
three); the band is the 10-day simple average of the daily range (high less low) either side of
it. Buy when the close is over the upper band; sell when the close is under the lower band; in
between, stay as you were.

AUTHOR'S TEST: grain futures, daily bars, the 1950s. No published return figure was found, and
none is claimed here. The book's own text was not read by this session: the rule is the one
secondary accounts give (Linda Raschke's later re-working on an exponential average and the
average true range is a different rule, not this one). The ladder measures the rule on the
desk's data.

Where sources differ: the 10-day windows are the book's; later sources use 20 days. Some close
the position at the centre line and not the lower band; this port takes the book's lower band.
Long only (the template has no short). The window includes the day of the close judged.

The old desk is a quarry for the reading only; none of its code is copied.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal, localcontext
from typing import ClassVar

from desk.lines import LINES
from desk.store import Bar
from desk.strategy import (
    ARITHMETIC,
    CLOSES,
    Decision,
    Declared,
    Timeframe,
    _run,
    _Window,
)

NAME = "keltner_channel_trend"
#: the book's days of both averages
DAYS = 10
_THREE = Decimal(3)


class KeltnerChannelTrend:
    """The book's rule: in over the upper band, out under the lower band, else as before."""

    declared: ClassVar[Declared] = Declared(Timeframe.DAILY, None, LINES, CLOSES)

    def __init__(self) -> None:
        self._typical = _Window(DAYS)
        self._range = _Window(DAYS)

    def step(self, bar: Bar, holding: bool) -> bool:
        """Shown the next bar after its close: whether to be in the market from here."""
        self._typical.add((bar.high + bar.low + bar.close) / _THREE)
        self._range.add(bar.high - bar.low)
        if not self._typical.full:
            return False
        centre, width = self._typical.mean(), self._range.mean()
        if bar.close > centre + width:
            return True
        if bar.close < centre - width:
            return False
        return holding


def decide(bars: Mapping[str, Sequence[Bar]]) -> tuple[Decision, ...]:
    """The rule's decision for every line and every day the bars cover."""
    with localcontext(ARITHMETIC):
        return tuple(
            d
            for symbol, series in bars.items()
            for d in _run(NAME, KeltnerChannelTrend(), symbol, series)
        )
