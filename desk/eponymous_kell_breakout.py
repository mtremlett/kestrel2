"""eponymous_kell_breakout - Oliver Kell's "base n' break" as a rule under the one template
(SET 1 of the eponymous strategies, R-RUNNER-70). The paper desk does not trade it.

AUTHOR: Oliver Kell, US stock trader (US Investing Championship 2020 winner, 2019 figure
quoted in the press as +941%). SOURCE: his interviews and his own published setups (the price
cycle: "base n' break", "wedge pop", "EMA crossback"), SECONDARY, read in 2020 to 2023 write-ups;
no book or primary text was on hand, and the quoted figure is the press's, not checked here.
AUTHOR'S TEST: US growth stocks, daily bars, discretionary, 2019 to 2020; a trader's year, not a
backtest of this rule. Published figure for this rule alone: none.
WHERE SOURCES DIFFER: the base is 10 to 30 sessions in the write-ups, and the trail is the 10-day
exponential average or the 20-day; this port takes a base of 20 sessions and the 10-day trail.
READING HERE: long only, on the close. Buy a close over the highest high of the 20 sessions
before, with that close over both the 10- and the 20-day exponential averages (the breakout
leaves the base on the rising averages); sell a close under the 10-day average. Nothing is
bought until 20 sessions are seen.
Holding period: none. The sale is the close under the 10-day average alone; his write-ups
give no day limit, so none is declared.

The old desk is a quarry for the reading only; none of its code is copied.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import localcontext
from typing import ClassVar

from desk.lines import LINES
from desk.store import Bar
from desk.strategy import (
    ARITHMETIC,
    Decision,
    Declared,
    Field,
    Rule,
    Timeframe,
    _Exponential,
    _run,
    _Window,
)

NAME = "kell_breakout"
#: sessions of base, and days of the trail average and of the slower average
BASE, TRAIL, SLOW = 20, 10, 20


class KellBreakout:
    """In on a close over the base's highest high above both averages; out under the 10-day."""

    declared: ClassVar[Declared] = Declared(
        Timeframe.DAILY, None, LINES, frozenset({Field.HIGH, Field.CLOSE})
    )

    def __init__(self) -> None:
        self._highs = _Window(BASE)
        self._trail, self._slow = _Exponential(TRAIL), _Exponential(SLOW)

    def step(self, bar: Bar, holding: bool) -> bool:
        """Shown the next bar after its close: whether to be in the market from here."""
        trail, slow = self._trail.add(bar.close), self._slow.add(bar.close)
        broke = self._highs.full and bar.close > self._highs.high()
        self._highs.add(bar.high)
        if holding:
            return trail is not None and bar.close >= trail
        return broke and trail is not None and slow is not None and bar.close > max(trail, slow)


def decide(bars: Mapping[str, Sequence[Bar]]) -> tuple[Decision, ...]:
    """The rule's decision for every line and every day the bars cover."""
    with localcontext(ARITHMETIC):
        return tuple(
            d for symbol, series in bars.items() for d in _run(NAME, KellBreakout(), symbol, series)
        )


EPONYMOUS: Mapping[str, type[Rule]] = {NAME: KellBreakout}
