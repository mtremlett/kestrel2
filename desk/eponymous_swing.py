"""eponymous_swing - rules named for the authors who published them, one rule each, run under
the template of `desk/strategy.py`. The paper desk does not trade them; they are for the ladder.

weekly_reversal_jegadeesh. AUTHOR: Narasimhan Jegadeesh. SOURCE: "Evidence of Predictable
Behavior of Security Returns", Journal of Finance 45(3), 1990. HIS INSTRUMENT AND PERIOD: every
common stock on the NYSE and AMEX (CRSP), January 1934 to December 1987. HIS FIGURE: the
first-order autocorrelation of monthly returns is negative (about -0.03 on average, a reversal),
and buying the decile of last month's losers while selling the winners earned about 2.5% a
month before costs (as I read it from memory; unverified this session, the paper was not at hand).
WHERE SOURCES DISAGREE: Jegadeesh's own horizon is a MONTH. The WEEKLY form is Lehmann's,
"Fads, Martingales, and Market Efficiency", Quarterly Journal of Economics (1990), which found
last week's losers gain the next week (SECONDARY here: the desk's request names the rule
"weekly", under Jegadeesh). The range of the horizon is therefore one week to one month; this
module takes the week: five sessions, the name's reading.

THE READING. He ranks a cross-section and goes long the losers, short the winners. The desk
trades one line at a time, long only, so only the loser leg survives, and "loser" becomes the
line's own: its close is under its close five sessions before (a flat week is no loser). It
buys on that close and holds five sessions (the following week), then sells; never short.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping, Sequence
from decimal import Decimal, localcontext
from typing import ClassVar

from desk.lines import LINES
from desk.store import Bar
from desk.strategy import ARITHMETIC, CLOSES, Decision, Declared, Rule, Timeframe, _run

WEEK = 5


class _WeeklyReversal:
    """Buy a close under the close five sessions back; sell after five sessions held."""

    declared: ClassVar[Declared] = Declared(Timeframe.DAILY, WEEK, LINES, CLOSES)

    def __init__(self) -> None:
        self._closes: deque[Decimal] = deque(maxlen=WEEK)
        self._held = 0

    def step(self, bar: Bar, holding: bool) -> bool:
        self._held = self._held + 1 if holding else 0
        if holding and self._held >= WEEK:
            wants = False
        elif holding:
            wants = True
        else:
            wants = len(self._closes) == WEEK and bar.close < self._closes[0]
        self._closes.append(bar.close)
        return wants


EPONYMOUS: Mapping[str, type[Rule]] = {"weekly_reversal_jegadeesh": _WeeklyReversal}


def decide(bars: Mapping[str, Sequence[Bar]]) -> tuple[Decision, ...]:
    """A decision from every eponymous rule for every line and day the bars cover."""
    with localcontext(ARITHMETIC):
        return tuple(
            decision
            for symbol, series in bars.items()
            for name, make in EPONYMOUS.items()
            for decision in _run(name, make(), symbol, series)
        )
