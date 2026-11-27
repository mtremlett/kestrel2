"""eponymous_williams_r - Larry Williams's %R, ported as a rule under the one template (SET 1 of
the eponymous strategies, R-RUNNER-67). Family: bands. The paper desk does not trade it.

AUTHOR: Larry Williams. SOURCE: How I Made One Million Dollars Last Year Trading Commodities
(1973), where %R is the close's place in the recent range: %R = (highest high - close) /
(highest high - lowest low) x -100, over the last 10 days. The rule, long only: buy at the close
when %R is at -90 or lower (the close in the bottom tenth of the range, oversold); sell at the
close when %R is at -10 or higher (the top tenth, overbought).

AUTHOR'S TEST: commodity futures, daily bars, about 1972; the book's claim is a large multiple
of a small account in one year. The published figure is NOT written here: this session had no
copy of the book, and a figure quoted from memory would be a guess. The ladder measures the
rule itself, after costs, on the desk's own data. Secondary sources (charting guides and
platforms, undated here) read %R over 14 days with the bands -80 and -20, so the RANGE of the
setting is 10 to 14 days and -90/-80 to -10/-20; this port takes the book's 10 days and its
-90 and -10.

Holding period: none. The book sells at the top tenth of the range alone, never a count of
sessions.

The old desk is a quarry for the reading only; none of its code is copied.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal, localcontext
from typing import ClassVar

from desk.lines import LINES
from desk.store import Bar
from desk.strategy import ARITHMETIC, RANGES, Decision, Declared, Rule, Timeframe, _run, _Window

NAME = "williams_r"
#: the book's days of range, and the %R (a negative percent) to buy at or below and sell at or above
DAYS, BUY_AT, SELL_AT = 10, Decimal(-90), Decimal(-10)


class WilliamsR:
    """The book's rule: in when the close sits in the range's bottom tenth, out at its top tenth."""

    declared: ClassVar[Declared] = Declared(Timeframe.DAILY, None, LINES, RANGES)

    def __init__(self) -> None:
        self._highs, self._lows = _Window(DAYS), _Window(DAYS)

    def step(self, bar: Bar, holding: bool) -> bool:
        """Shown the next bar after its close: whether to be in the market from here."""
        self._highs.add(bar.high)
        self._lows.add(bar.low)
        if not self._highs.full:
            return False
        top, bottom = self._highs.high(), self._lows.low()
        if top == bottom:  # no range, so %R is undefined: keep the position as it is
            return holding
        percent_r = (top - bar.close) / (top - bottom) * -100
        return percent_r < SELL_AT if holding else percent_r <= BUY_AT


def decide(bars: Mapping[str, Sequence[Bar]]) -> tuple[Decision, ...]:
    """The rule's decision for every line and every day the bars cover."""
    with localcontext(ARITHMETIC):
        return tuple(
            d for symbol, series in bars.items() for d in _run(NAME, WilliamsR(), symbol, series)
        )


EPONYMOUS: Mapping[str, type[Rule]] = {NAME: WilliamsR}
