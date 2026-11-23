"""eponymous_zweig_breadth_thrust - Martin Zweig's breadth thrust as a rule under the one
template (SET 1 of the eponymous strategies, R-RUNNER-80; family: swing). The paper desk does
not trade it.

AUTHOR: Martin Zweig. SOURCE: Winning on Wall Street (1986), the "Breadth Thrust" signal.
AUTHOR'S TEST: the New York Stock Exchange, daily advances and declines, 1945 to 1985 as the
book is quoted. Published figure: every thrust followed by a gain, about 24.6% on average
eleven months later; the count of thrusts (14 in the quotations) and the figure are SECONDARY,
read from later write-ups (2000s), and not checked against the book here.
WHERE SOURCES DIFFER: the thresholds are 0.40 and 0.615 in every write-up read; the 10-day
window is stated for both the average and the climb; the exit is not in the signal at all.
READING HERE: long only, on the close. The ratio of the day is advances over advances plus
declines; its 10-day exponential average (the desk's standard one) rising from under 0.40 to
over 0.615 inside 10 sessions is the thrust: buy. Zweig gives no sale, so this port holds
HOLD = 230 sessions (about eleven months, the book's horizon) and sells.

BLOCKED ON DATA: no store we hold has market breadth (advances and declines), so the rule is
ported with its known-answer fixture only; it takes the breadth as an argument and never
invents a series. Nothing is bought on a day without its breadth: the rule fails loudly.

The old desk is a quarry for the reading only; none of its code is copied.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, localcontext
from typing import ClassVar

from desk.lines import LINES
from desk.store import Bar
from desk.strategy import (
    ARITHMETIC,
    CLOSES,
    Decision,
    Declared,
    Rule,
    Timeframe,
    _Exponential,
    _run,
)

NAME = "zweig_breadth_thrust"
#: days of the average and of the climb; the low and high marks; sessions held after a buy
WINDOW, HOLD = 10, 230
LOW, HIGH = Decimal("0.40"), Decimal("0.615")


@dataclass(frozen=True)
class Breadth:
    """One day's count of stocks that rose and stocks that fell."""

    advances: int
    declines: int

    def __post_init__(self) -> None:
        if self.advances < 0 or self.declines < 0 or self.advances + self.declines == 0:
            raise ValueError(f"breadth needs some advances or declines: {self}")

    @property
    def ratio(self) -> Decimal:
        """Advances over advances plus declines."""
        return Decimal(self.advances) / (self.advances + self.declines)


class ZweigBreadthThrust:
    """In on the breadth average climbing from under 0.40 to over 0.615 within 10 sessions."""

    declared: ClassVar[Declared] = Declared(Timeframe.DAILY, None, LINES, CLOSES)

    def __init__(self, breadth: Mapping[date, Breadth]) -> None:
        self._breadth = breadth
        self._average = _Exponential(WINDOW)
        self._recent: deque[Decimal] = deque(maxlen=WINDOW)
        self._held = 0

    def step(self, bar: Bar, holding: bool) -> bool:
        """Shown the next bar after its close: whether to be in the market from here."""
        if bar.day not in self._breadth:
            raise KeyError(f"no breadth for {bar.day}: the rule never invents it")
        average = self._average.add(self._breadth[bar.day].ratio)
        if average is not None:
            self._recent.append(average)
        if holding:
            self._held += 1
            return self._held < HOLD
        self._held = 0
        return average is not None and average > HIGH and min(self._recent) < LOW


def decide(
    bars: Mapping[str, Sequence[Bar]], breadth: Mapping[date, Breadth]
) -> tuple[Decision, ...]:
    """The rule's decision for every line and every day the bars cover."""
    with localcontext(ARITHMETIC):
        return tuple(
            d
            for symbol, series in bars.items()
            for d in _run(NAME, ZweigBreadthThrust(breadth), symbol, series)
        )


EPONYMOUS: Mapping[str, type[Rule]] = {NAME: ZweigBreadthThrust}
