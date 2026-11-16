"""eponymous_connors_double_7 - Connors' Double 7's, ported as a rule under the one template
(R-RUNGS-10, the eponymous strategies). Family: connors. The paper desk does not trade it.

AUTHORS: Larry Connors and Cesar Alvarez. SOURCE: Short Term Trading Strategies That Work
(TradingMarkets, 2008). The book's rule, long only: buy at the close when the close is above its
200-day simple average and is the lowest close of the last 7 days; sell at the close that is the
highest close of the last 7 days.

AUTHOR'S TEST: US stocks and ETFs, daily bars, roughly 1995 to 2007. The author's published
figure for the rule is NOT written here: this session had no copy of the book to read it from,
and a figure quoted from memory would be a guess. The ladder measures the rule itself, after
costs, on the desk's own data. Secondary sources (blogs and forums, undated here) vary the
window from 5 to 10 days, so the RANGE of the setting is 5 to 10 days; this port takes the
book's 7.

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

NAME = "connors_double_7"
#: the book's days of trend, and days for a closing low to buy on and a closing high to sell on
TREND, WINDOW = 200, 7


class ConnorsDouble7:
    """The book's rule: in above the 200-day average at a 7-day closing low, out at a high."""

    declared: ClassVar[Declared] = Declared(Timeframe.DAILY, None, LINES, RANGES)

    def __init__(self) -> None:
        self._trend = _Window(TREND)
        self._closes: deque[Decimal] = deque(maxlen=WINDOW)

    def step(self, bar: Bar, holding: bool) -> bool:
        """Shown the next bar after its close: whether to be in the market from here."""
        self._trend.add(bar.close)
        self._closes.append(bar.close)
        if len(self._closes) < WINDOW:
            return holding
        if holding:
            return bar.close < max(self._closes)
        return (
            self._trend.full and bar.close > self._trend.mean() and bar.close <= min(self._closes)
        )


def decide(bars: Mapping[str, Sequence[Bar]]) -> tuple[Decision, ...]:
    """The rule's decision for every line and every day the bars cover."""
    with localcontext(ARITHMETIC):
        return tuple(
            d
            for symbol, series in bars.items()
            for d in _run(NAME, ConnorsDouble7(), symbol, series)
        )


EPONYMOUS: Mapping[str, type[Rule]] = {NAME: ConnorsDouble7}
