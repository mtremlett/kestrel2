"""eponymous_connors_three_day_high_low - the Connors/Alvarez three-day high/low rule, ported as a
rule under the one template (SET 1 of the eponymous strategies, R-RUNNER-62). Family: connors.
The paper desk does not trade it.

AUTHORS: Larry Connors and Cesar Alvarez. SOURCE: High Probability ETF Trading (TradingMarkets,
2009). The book's rule, long only: buy at the close when the close is above its 200-day simple
average and the day's high and low are each lower than the day before's, for three days in a
row; sell at the close that is above the 5-day simple average.

AUTHOR'S TEST: US index and sector ETFs, daily bars, roughly 1998 to 2008. The author's
published figure for the rule is NOT written here: this session had no copy of the book to read
it from, and a figure quoted from memory would be a guess. The ladder measures the rule itself,
after costs, on the desk's own data. Secondary sources (blogs and forums, undated here) vary the
run of lower days from 2 to 4 and the exit between the 5-day average and the 2-day average, so
the RANGE of the setting is 2 to 4 days; this port takes the book's three and the 5-day exit.

The old desk is a quarry for the reading only; none of its code is copied.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import localcontext
from typing import ClassVar

from desk.lines import LINES
from desk.store import Bar
from desk.strategy import ARITHMETIC, RANGES, Decision, Declared, Rule, Timeframe, _run, _Window

NAME = "connors_three_day_high_low"
#: the book's days of trend, days of exit, and lower-high-and-low days in a row to buy on
TREND, EXIT, RUN = 200, 5, 3


class ConnorsThreeDayHighLow:
    """The book's rule: in above the 200-day average after three lower highs and lows."""

    declared: ClassVar[Declared] = Declared(Timeframe.DAILY, None, LINES, RANGES)

    def __init__(self) -> None:
        self._long, self._short = _Window(TREND), _Window(EXIT)
        self._last: Bar | None = None
        self._lower = 0  #: days in a row with a lower high and a lower low

    def step(self, bar: Bar, holding: bool) -> bool:
        """Shown the next bar after its close: whether to be in the market from here."""
        last, self._last = self._last, bar
        lower = last is not None and bar.high < last.high and bar.low < last.low
        self._lower = self._lower + 1 if lower else 0
        self._long.add(bar.close)
        self._short.add(bar.close)
        if holding:
            return bar.close <= self._short.mean()
        return self._long.full and bar.close > self._long.mean() and self._lower >= RUN


def decide(bars: Mapping[str, Sequence[Bar]]) -> tuple[Decision, ...]:
    """The rule's decision for every line and every day the bars cover."""
    with localcontext(ARITHMETIC):
        return tuple(
            d
            for symbol, series in bars.items()
            for d in _run(NAME, ConnorsThreeDayHighLow(), symbol, series)
        )


EPONYMOUS: Mapping[str, type[Rule]] = {NAME: ConnorsThreeDayHighLow}
