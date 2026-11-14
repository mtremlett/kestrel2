"""eponymous_dan_zanger - Dan Zanger's chart-pattern breakout, ported as one rule under the one
template (SET 1 of the eponymous strategies, R-RUNNER-71). FAMILY: breakouts. The paper desk
does not trade it.

AUTHOR: Dan Zanger, US stock trader. SOURCE: his chart-pattern breakouts as told in interviews
and profiles of him (Wizards of Wall Street-style press and his own chart service); SECONDARY,
no primary text was on hand and no dates are written here. The rule as told: buy a stock that
breaks out of a base (the cup-and-handle, the flag) to a new high on volume well over its
usual, and get out when it closes under its 10-day moving average.

AUTHOR'S INSTRUMENT AND PERIOD: US growth stocks, 1998 to 2000 (the dot-com run). PUBLISHED
FIGURE: secondary only, and the sources differ: $10,775 turned into $18 million in about two
years in the usual telling; larger figures (above $40 million) appear in others. The range is
$18 million to over $40 million, unverified; no figure is claimed here. The ladder measures the
rule after costs on the desk's own data.

READING HERE, ONE RULE, long only, on the close: BUY when the close is over the highest high of
the 50 sessions before AND the day's volume is at least 1.5 times the 50-day average volume
before it; SELL when the close is under its 10-day simple average. The 50 days and the 1.5 are
this port's reading of "a base" and "heavy volume"; sources give no single number.

The old desk is a quarry for the reading only; none of its code is copied.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal, localcontext
from typing import ClassVar

from desk.lines import LINES
from desk.store import Bar
from desk.strategy import ARITHMETIC, Decision, Declared, Field, Timeframe, _run, _Window

NAME = "dan_zanger_breakout"
#: sessions of base, sessions of the exit average, and the volume multiple that is heavy
BASE, EXIT, HEAVY = 50, 10, Decimal("1.5")


class DanZangerBreakout:
    """In on a close over the 50-day high on heavy volume; out under the 10-day average."""

    declared: ClassVar[Declared] = Declared(
        Timeframe.DAILY, None, LINES, frozenset({Field.HIGH, Field.CLOSE, Field.VOLUME})
    )

    def __init__(self) -> None:
        self._highs, self._volumes, self._closes = _Window(BASE), _Window(BASE), _Window(EXIT)

    def step(self, bar: Bar, holding: bool) -> bool:
        """Shown the next bar after its close: whether to be in the market from here."""
        self._closes.add(bar.close)
        if holding:
            wants = bar.close >= self._closes.mean()
        else:
            wants = (
                self._highs.full
                and bar.close > self._highs.high()
                and bar.volume >= HEAVY * self._volumes.mean()
            )
        self._highs.add(bar.high)
        self._volumes.add(Decimal(bar.volume))
        return wants


def decide(bars: Mapping[str, Sequence[Bar]]) -> tuple[Decision, ...]:
    """The rule's decision for every line and every day the bars cover."""
    with localcontext(ARITHMETIC):
        return tuple(
            d for s, series in bars.items() for d in _run(NAME, DanZangerBreakout(), s, series)
        )
