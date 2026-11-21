"""eponymous_raschke_swing - Linda Raschke's Turtle Soup, long side, ported as a rule under the
one template (SET 1 of the eponymous strategies, R-RUNNER-77). Family: swing. The paper desk
does not trade it.

AUTHORS: Linda Bradford Raschke and Laurence Connors. SOURCE: Street Smarts: High Probability
Short-Term Trading Strategies (M. Gordon Publishing, 1995). The book's rule, long only: when
the market makes a new 20-day low, and the 20-day low it undercuts was set at least four
sessions earlier, buy as it turns back above that older low (a failed breakdown); the protective
stop sits just under the new low.

THIS PORT, on daily bars: a day whose low is under the lowest low of the twenty days before
it, when that older low was set four or more sessions before, is the setup. The NEXT day buys
at its close when it trades no lower than the setup day's low and closes back above the older
low (the book's buy stop just over the old low). Sell at the first close under the setup low.
The book's stop trails and takes profit by discretion; no mechanical exit is published, so the
port takes the book's stop alone. (Until 21 Nov the port demanded the setup day itself close
back above the older low, a one-day reversal the book never asks for: 239 lines never traded.)

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
from desk.strategy import ARITHMETIC, RANGES, Decision, Declared, Rule, Timeframe, _run

NAME = "raschke_swing"
#: the book's days of low to undercut, and sessions the older low must be old by
LOOKBACK, GAP = 20, 4


class RaschkeTurtleSoup:
    """The book's rule: buy a new 20-day low that turns back above the older low."""

    declared: ClassVar[Declared] = Declared(Timeframe.DAILY, None, LINES, RANGES)

    def __init__(self) -> None:
        self._lows: deque[Decimal] = deque(maxlen=LOOKBACK)  #: the days before today
        self._setup: tuple[Decimal, Decimal] | None = None  #: (older low, setup day's low)
        self._stop: Decimal | None = None  #: the setup day's low, once bought

    def _undercut(self, bar: Bar) -> tuple[Decimal, Decimal] | None:
        if len(self._lows) < LOOKBACK:
            return None
        older = min(self._lows)
        newest = LOOKBACK - 1 - list(reversed(self._lows)).index(older)  #: its latest day
        return (older, bar.low) if bar.low < older and LOOKBACK - newest >= GAP else None

    def step(self, bar: Bar, holding: bool) -> bool:
        """Shown the next bar after its close: whether to be in the market from here."""
        setup, self._setup = self._setup, None if holding else self._undercut(bar)
        buys = not holding and setup is not None and bar.low >= setup[1] and bar.close > setup[0]
        if buys and setup is not None:
            self._stop = setup[1]
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


EPONYMOUS: Mapping[str, type[Rule]] = {NAME: RaschkeTurtleSoup}
