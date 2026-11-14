"""eponymous_weinstein_stage - Stan Weinstein's stage analysis, ported as a rule under the one
template (SET 1 of the eponymous strategies, R-RUNNER-79). Family: swing. The paper desk does
not trade it.

AUTHOR: Stan Weinstein. SOURCE: Secrets for Profiting in Bull and Bear Markets (1988). The
book's rule, long only, on the weekly chart: a stock in Stage 2 trades above its 30-week simple
average and that average is rising; buy when the price breaks above a rising 30-week average,
and sell when the price closes below it (Stage 3 turning to Stage 4).

AUTHOR'S INSTRUMENT AND PERIOD: US stocks and the US market indices, weekly charts; no single
test period or published figure is given for the rule, and none is quoted here. The ladder
measures the rule itself, after costs, on the desk's own data. The desk reads daily bars, so
the 30-week average is 150 daily closes and "rising" is the average above its own value five
sessions (one week) before. Secondary sources (blogs and courses, undated here) vary the
average from 30 weeks to 40 weeks and its slope test from "rising" to "flat or rising", so the
RANGE of the setting is 30 to 40 weeks; this port takes the book's 30.

The old desk is a quarry for the reading only; none of its code is copied.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping, Sequence
from decimal import Decimal, localcontext
from typing import ClassVar

from desk.lines import LINES
from desk.store import Bar
from desk.strategy import ARITHMETIC, RANGES, Decision, Declared, Timeframe, _run, _Window

NAME = "weinstein_stage"
#: the book's 30 weeks of closes, and the sessions (one week) the average is compared across
AVERAGE, WEEK = 150, 5


class WeinsteinStage:
    """The book's rule: in while the price is above a rising 30-week average."""

    declared: ClassVar[Declared] = Declared(Timeframe.DAILY, None, LINES, RANGES)

    def __init__(self) -> None:
        self._window = _Window(AVERAGE)
        self._means: deque[Decimal] = deque(maxlen=WEEK + 1)

    def step(self, bar: Bar, holding: bool) -> bool:
        """Shown the next bar after its close: whether to be in the market from here."""
        self._window.add(bar.close)
        if not self._window.full:
            return False
        mean = self._window.mean()
        self._means.append(mean)
        if holding:
            return bar.close >= mean
        rising = len(self._means) == self._means.maxlen and mean > self._means[0]
        return rising and bar.close > mean


def decide(bars: Mapping[str, Sequence[Bar]]) -> tuple[Decision, ...]:
    """The rule's decision for every line and every day the bars cover."""
    with localcontext(ARITHMETIC):
        return tuple(
            d
            for symbol, series in bars.items()
            for d in _run(NAME, WeinsteinStage(), symbol, series)
        )
