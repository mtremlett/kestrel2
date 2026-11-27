"""eponymous_minervini_breakout - Minervini's breakout from a Stage 2 uptrend, ported as one rule
under the one template (SET 1 of the eponymous strategies, R-RUNNER-69). The family is breakouts.
The paper desk does not trade it.

AUTHOR: Mark Minervini. SOURCE: Trade Like a Stock Market Wizard (2013), the "Trend Template"
chapter and the chapters on the pivot buy point and on selling. The book's rule, long only:
buy at the close when the stock is in the Trend Template and the close breaks above the pivot
(the top of the base just built); sell at the close under the 50-day simple average.
  Trend Template, all of: close over the 150-day and 200-day averages; the 150-day over the
  200-day; the 200-day higher than a month (21 sessions) ago; the 50-day over both; close over
  the 50-day; close at least 30% above the 52-week low; close within 25% of the 52-week high.
  (The book's eighth point, a relative-strength rank of 70 or more, needs the whole market and
  is not in a rule that sees one line; the ladder's own ranking is where it belongs.)

AUTHOR'S TEST: US stocks, daily bars, his trading of the 1990s onward (the book's account of
his US Investing Championship wins is of discretion, not of this rule). NO published figure for
the rule is written here: this session had no copy of the book, and a number quoted from memory
would be a guess.
RANGE of the setting: sources (the book; secondary blogs and forums, undated here) put the
pivot's base at 3 to 65 weeks and the sell at the 50-day average or a stop of 7 to 8% under the
buy; this port takes a 15-session pivot (three weeks, the tightest base he calls a pivot) and
the 50-day sell, since the template's rules carry no entry price for a stop.

Holding period: none; the book's sell is the 50-day average (or a stop), not a count of sessions.

The old desk is a quarry for the reading only; none of its code is copied.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping, Sequence
from decimal import Decimal, localcontext
from typing import ClassVar

from desk.lines import LINES
from desk.store import Bar
from desk.strategy import ARITHMETIC, RANGES, Decision, Declared, Rule, Timeframe, _run, _Window

NAME = "minervini_breakout"
#: sessions in a year, in the 200-day's month, and in the pivot's base
YEAR, MONTH, PIVOT = 252, 21, 15
#: the close's least rise over the year's low, and its greatest fall from the year's high
ABOVE_LOW, NEAR_HIGH = Decimal("1.30"), Decimal("0.75")


class MinerviniBreakout:
    """In on a close over the pivot while in the Trend Template; out under the 50-day average."""

    declared: ClassVar[Declared] = Declared(Timeframe.DAILY, None, LINES, RANGES)

    def __init__(self) -> None:
        self._avg = {n: _Window(n) for n in (50, 150, 200)}
        self._year_high, self._year_low = _Window(YEAR), _Window(YEAR)
        self._pivot = _Window(PIVOT)
        self._slow: deque[Decimal] = deque(maxlen=MONTH + 1)

    def _trend_template(self, close: Decimal) -> bool:
        fifty, hundred50, slow = (self._avg[n].mean() for n in (50, 150, 200))
        return (
            self._year_high.full
            and len(self._slow) == self._slow.maxlen
            and close > hundred50 > slow
            and fifty > hundred50
            and close > fifty
            and slow > self._slow[0]
            and close >= ABOVE_LOW * self._year_low.low()
            and close >= NEAR_HIGH * self._year_high.high()
        )

    def step(self, bar: Bar, holding: bool) -> bool:
        """Shown the next bar after its close: whether to be in the market from here."""
        for window in self._avg.values():
            window.add(bar.close)
        if self._avg[200].full:
            self._slow.append(self._avg[200].mean())
        self._year_high.add(bar.high)
        self._year_low.add(bar.low)
        broke = self._pivot.full and bar.close > self._pivot.high()
        self._pivot.add(bar.high)
        if holding:
            return bar.close >= self._avg[50].mean()
        return broke and self._trend_template(bar.close)


def decide(bars: Mapping[str, Sequence[Bar]]) -> tuple[Decision, ...]:
    """The rule's decision for every line and every day the bars cover."""
    with localcontext(ARITHMETIC):
        return tuple(
            d
            for symbol, series in bars.items()
            for d in _run(NAME, MinerviniBreakout(), symbol, series)
        )


EPONYMOUS: Mapping[str, type[Rule]] = {NAME: MinerviniBreakout}
