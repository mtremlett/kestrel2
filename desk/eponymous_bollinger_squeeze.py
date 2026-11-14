"""eponymous_bollinger_squeeze - John Bollinger's band squeeze, ported as a rule under the one
template (SET 1 of the eponymous strategies, R-RUNNER-66; family: bands). The paper desk does
not trade it.

AUTHOR: John Bollinger. SOURCE: Bollinger on Bollinger Bands (McGraw-Hill, 2001), the chapter on
the squeeze. The book's idea: when the bands (20-day average, 2 standard deviations) are at their
narrowest, volatility is at a low and a large move is coming; the band width is "the lowest in
six months" (about 126 sessions) marks the squeeze, and a close out of the bands gives its
direction. This port, long only: buy at the close when the bands were in a squeeze on the day
before (their width, upper minus lower over the average, the lowest of the last 126 sessions,
ties included) and the close is over the upper band; sell at the close that is under the
20-day average (the middle band).

AUTHOR'S TEST: stocks and indices, daily bars, the book's examples of the late 1990s. The book
gives the squeeze as a pattern, not a tested rule with a published figure, and this session had
no copy of it to read from: NO figure is written here, and the exit on the middle band is this
port's reading, not a quotation. Secondary sources (blogs and forums, undated here) take the
squeeze from the lowest width in 100 to 150 sessions, so the RANGE of the look-back is 100 to
150; the book's six months, 126, is taken. The ladder measures the rule itself, after costs.

The old desk is a quarry for the reading only; none of its code is copied.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal, localcontext
from typing import ClassVar

from desk.lines import LINES
from desk.store import Bar
from desk.strategy import ARITHMETIC, CLOSES, Decision, Declared, Timeframe, _run, _Window

NAME = "bollinger_squeeze"
#: the book's days of average, standard deviations either side, and sessions in six months
PERIOD, WIDTH, SIX_MONTHS = 20, Decimal(2), 126


class BollingerSqueeze:
    """The book's rule: in over the upper band after the narrowest bands in six months."""

    declared: ClassVar[Declared] = Declared(Timeframe.DAILY, None, LINES, CLOSES)

    def __init__(self) -> None:
        self._closes, self._widths = _Window(PERIOD), _Window(SIX_MONTHS)
        self._squeezed = False

    def step(self, bar: Bar, holding: bool) -> bool:
        """Shown the next bar after its close: whether to be in the market from here."""
        self._closes.add(bar.close)
        if not self._closes.full:
            return False
        mean, deviation = self._closes.mean(), self._closes.deviation()
        squeezed, self._squeezed = self._squeezed, self._widen(2 * WIDTH * deviation / mean)
        if holding:
            return bar.close >= mean
        return squeezed and bar.close > mean + WIDTH * deviation

    def _widen(self, width: Decimal) -> bool:
        """Take in today's band width; whether it is the narrowest of the last six months."""
        self._widths.add(width)
        return self._widths.full and width <= self._widths.low()


def decide(bars: Mapping[str, Sequence[Bar]]) -> tuple[Decision, ...]:
    """The rule's decision for every line and every day the bars cover."""
    with localcontext(ARITHMETIC):
        return tuple(
            d
            for symbol, series in bars.items()
            for d in _run(NAME, BollingerSqueeze(), symbol, series)
        )
