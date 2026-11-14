"""eponymous_demark_sequential - Tom DeMark's TD Sequential, ported as one rule under the one
template (SET 1 of the eponymous strategies, R-RUNNER-78). Family: swing. The paper desk does
not trade it.

AUTHOR: Tom DeMark. SOURCE: The New Science of Technical Analysis (Wiley, 1994). The book's
buy side, long only: a BUY SETUP is nine closes in a row, each lower than the close four bars
before it. After the setup a BUY COUNTDOWN counts bars (not necessarily in a row) whose close is
at or below the low two bars before; the thirteenth is the buy. The countdown is cancelled by a
SELL SETUP (nine closes in a row, each higher than the close four bars before it), which is
also this port's exit, and a fresh buy setup restarts the count.

AUTHOR'S TEST: the book applies it to futures and stocks on daily and shorter bars; the
author's published figure for the rule is NOT written here: this session had no copy of the book
to read it from, and a figure quoted from memory would be a guess. The ladder measures the rule
itself, after costs, on the desk's own data. Secondary sources (undated here) differ on the
countdown's compare (close against the low two bars back, or against the close) and on its
exact cancel rules; this port takes the book's low-two-bars-back reading, so the RANGE of the
setting is those two compares with the 9 and 13 fixed.

The old desk is a quarry for the reading only; none of its code is copied.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import localcontext
from typing import ClassVar

from desk.lines import LINES
from desk.store import Bar
from desk.strategy import ARITHMETIC, RANGES, Decision, Declared, Timeframe, _run

NAME = "demark_sequential"
#: the book's setup length, the bars back a setup compares with, the countdown length and its lag
SETUP, BACK, COUNTDOWN, LAG = 9, 4, 13, 2


class DemarkSequential:
    """The book's rule: in on the thirteenth countdown bar, out on a nine-bar sell setup."""

    declared: ClassVar[Declared] = Declared(Timeframe.DAILY, None, LINES, RANGES)

    def __init__(self) -> None:
        self._bars: list[Bar] = []
        self._down = self._up = 0  #: the run of setup closes below / above the close four back
        self._count: int | None = None  #: countdown bars so far; None while no countdown runs

    def step(self, bar: Bar, holding: bool) -> bool:
        """Shown the next bar after its close: whether to be in the market from here."""
        self._bars.append(bar)
        n = len(self._bars)
        if n > BACK:
            ref = self._bars[n - 1 - BACK].close
            self._down = self._down + 1 if bar.close < ref else 0
            self._up = self._up + 1 if bar.close > ref else 0
        sell_setup = self._up == SETUP
        if sell_setup:
            self._count = None
        elif self._down == SETUP:
            self._count = 0
        elif self._count is not None and n > LAG and bar.close <= self._bars[n - 1 - LAG].low:
            self._count += 1
        bought = self._count == COUNTDOWN
        if bought:
            self._count = None
        return bought or (holding and not sell_setup)


def decide(bars: Mapping[str, Sequence[Bar]]) -> tuple[Decision, ...]:
    """The rule's decision for every line and every day the bars cover."""
    with localcontext(ARITHMETIC):
        return tuple(
            d
            for symbol, series in bars.items()
            for d in _run(NAME, DemarkSequential(), symbol, series)
        )
