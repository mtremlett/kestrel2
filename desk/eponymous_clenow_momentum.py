"""eponymous_clenow_momentum - Clenow's momentum rule, ported as a rule under the one template
(SET 1 of the eponymous strategies, R-RUNNER-74). Its family is momentum. The paper desk does
not trade it.

AUTHOR: Andreas Clenow. SOURCE: Stocks on the Move (2015), the chapter on the momentum model.
The book's rule: score a stock by the slope of the exponential regression of its last 90 closes
(the slope annualised over 250 days) times the regression's R-squared; buy only a stock above its
100-day simple average with no move of more than 15% in a day inside the last 90 days; sell it
when it falls below the 100-day average, or has such a move.

AUTHOR'S TEST: the S&P 500 members, daily bars, 2000 to 2014; the book reports about 14% a year
net of costs. This figure is from the secondary record of the book's results, not from a copy
read by this session, and it is not checked here. The ladder measures the rule on the desk's data.

ONE LINE AT A TIME. The book ranks a whole list and buys the top fifth; a rule under the template
sees one line, so it cannot rank. The port keeps the score and asks of it what a single line can
answer: that it is positive (the 90-day trend is up). The book's other exits (a fall out of the
top fifth, the index under its 200-day average) need the list and are not ported. Secondary sources
vary the windows (90 or 125 days of regression; 100 or 200 days of average); this port takes the
book's own. No holding period: the book sells on the average or the move only.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping, Sequence
from decimal import Decimal, localcontext
from typing import ClassVar

from desk.lines import LINES
from desk.store import Bar
from desk.strategy import (
    ARITHMETIC,
    CLOSES,
    ZERO,
    Decision,
    Declared,
    Rule,
    Timeframe,
    _run,
    _Window,
)

NAME = "clenow_momentum"
#: the book's days of regression, days of average, days a year, and the largest move of a day
REGRESSION, TREND, YEAR, GAP = 90, 100, 250, Decimal("0.15")
_ONE = Decimal(1)


def score(closes: Sequence[Decimal]) -> Decimal:
    """The annualised slope of the exponential regression of `closes`, times its R-squared."""
    n = len(closes)
    xs, ys = range(n), [c.ln() for c in closes]
    mx, my = Decimal(n - 1) / 2, sum(ys, ZERO) / n
    sxx = sum(((x - mx) ** 2 for x in xs), ZERO)
    sxy = sum(((x - mx) * (y - my) for x, y in zip(xs, ys, strict=True)), ZERO)
    syy = sum(((y - my) ** 2 for y in ys), ZERO)
    if syy == 0:
        return ZERO
    slope = sxy / sxx
    return ((slope * YEAR).exp() - _ONE) * (sxy * sxy / (sxx * syy))


class ClenowMomentum:
    """The book's rule: in above the 100-day average on a rising 90-day score with no 15% move."""

    declared: ClassVar[Declared] = Declared(Timeframe.DAILY, None, LINES, CLOSES)

    def __init__(self) -> None:
        self._average = _Window(TREND)
        self._closes: deque[Decimal] = deque(maxlen=REGRESSION)
        self._gapped: deque[bool] = deque(maxlen=REGRESSION)

    def step(self, bar: Bar, holding: bool) -> bool:
        """Shown the next bar after its close: whether to be in the market from here."""
        close = bar.close
        if self._closes:
            self._gapped.append(abs(close / self._closes[-1] - _ONE) > GAP)
        self._closes.append(close)
        self._average.add(close)
        if not self._average.full or any(self._gapped) or close <= self._average.mean():
            return False
        return holding or score(self._closes) > ZERO


def decide(bars: Mapping[str, Sequence[Bar]]) -> tuple[Decision, ...]:
    """The rule's decision for every line and every day the bars cover."""
    with localcontext(ARITHMETIC):
        return tuple(
            d
            for symbol, series in bars.items()
            for d in _run(NAME, ClenowMomentum(), symbol, series)
        )


EPONYMOUS: Mapping[str, type[Rule]] = {NAME: ClenowMomentum}
