"""eponymous_raschke_swing - Linda Raschke's Turtle Soup, long side, ported as a rule under the
one template (SET 1 of the eponymous strategies, R-RUNNER-77). Family: swing. The paper desk
does not trade it.

AUTHORS: Linda Bradford Raschke and Laurence Connors. SOURCE: Street Smarts: High Probability
Short-Term Trading Strategies (M. Gordon Publishing, 1995). The book's rule, long only: when
the market makes a new 20-day low, and the 20-day low it undercuts was set at least four
sessions earlier, buy as it turns back above that older low (a failed breakdown); the protective
stop sits just under the new low.

THIS PORT, on daily bars: buy at the close of a day whose low is under the lowest low of the
twenty days before it, when that older low was set four or more sessions before, and the close
is back above it. Sell at the first close under the low of the buying day. The book's stop
trails and takes profit by discretion; no mechanical exit is published, so the port takes the
book's stop alone.

AUTHOR'S TEST: futures and stocks, intraday and daily, early 1990s. The author's published
figure is NOT written here: the book's cases are chart examples, and this session had no copy
to read a count from; a figure quoted from memory would be a guess. The ladder measures the
rule after costs on the desk's own data. Secondary sources (blogs and forums, undated here)
vary the lookback from 20 to 40 days and the gap from 3 to 4 sessions, so the RANGE of the
setting is 20 to 40 days, 3 to 4 sessions; this port takes the book's 20 days and 4 sessions.

The old desk is a quarry for the reading only; none of its code is copied.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping, Sequence
from decimal import Decimal, localcontext
from typing import ClassVar

from desk.lines import LINES
from desk.store import Bar
from desk.strategy import ARITHMETIC, RANGES, Decision, Declared, Timeframe, _run

NAME = "raschke_swing"
#: the book's days of low to undercut, and sessions the older low must be old by
LOOKBACK, GAP = 20, 4


class RaschkeTurtleSoup:
    """The book's rule: buy a new 20-day low that turns back above the older low."""

    declared: ClassVar[Declared] = Declared(Timeframe.DAILY, None, LINES, RANGES)

    def __init__(self) -> None:
        self._lows: deque[Decimal] = deque(maxlen=LOOKBACK)  #: the days before today
        self._stop: Decimal | None = None  #: the buying day's low

    def _fails_breakdown(self, bar: Bar) -> bool:
        if len(self._lows) < LOOKBACK:
            return False
        older = min(self._lows)
        newest = LOOKBACK - 1 - list(reversed(self._lows)).index(older)  #: its latest day
        return bar.low < older < bar.close and LOOKBACK - newest >= GAP

    def step(self, bar: Bar, holding: bool) -> bool:
        """Shown the next bar after its close: whether to be in the market from here."""
        buys = not holding and self._fails_breakdown(bar)
        if buys:
            self._stop = bar.low
        self._lows.append(bar.low)
        if holding:
            return self._stop is not None and bar.close >= self._stop
        return buys


def decide(bars: Mapping[str, Sequence[Bar]]) -> tuple[Decision, ...]:
    """The rule's decision for every line and every day the bars cover."""
    with localcontext(ARITHMETIC):
        return tuple(
            d
            for symbol, series in bars.items()
            for d in _run(NAME, RaschkeTurtleSoup(), symbol, series)
        )
