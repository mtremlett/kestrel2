"""eponymous_momentum - Antonacci's dual momentum, the rule he named for himself, on one line.

AUTHOR: Gary Antonacci. SOURCE: Dual Momentum Investing (2014), his Global Equities
Momentum (GEM). THE PUBLISHED RULE: each month-end, hold the stronger of US and world
equities if its trailing 12-month return beats Treasury bills (ABSOLUTE momentum), else hold
bonds. THE AUTHOR'S TEST: US equities, world equities ex-US and aggregate bonds, January 1974
to December 2013 (the book's backtest). PUBLISHED FIGURE: about 17.4% a year against about
10-11% for the S&P 500 over the same years (the author's table; this session did not re-derive
it, and secondary summaries, which are not this module's source, vary with the period they cut).

WHAT THIS MODULE IS: the template (desk/strategy.py) shows a rule one line's bars, long only,
and no second line or bill rate; so it holds the ABSOLUTE leg alone, as the author states it
for one market. Its two departures are named, not hidden: (1) the bill return is taken as
zero, so the line is held while its 12-month return is positive; (2) the relative leg (US
against world) and the bond fallback need other series and are not here. A month's call is
made on the first bar of the next month from the closes of the month-ends (known by then, so
never a later bar), one session after the author's month-end. No rule here is tuned.
It is a module the paper desk does not trade: it is in no list of strategy.STRATEGIES.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from decimal import Decimal
from typing import ClassVar

from desk.lines import LINES
from desk.store import Bar
from desk.strategy import CLOSES, Declared, Rule, Timeframe

#: month-ends in a year, plus the one a year ago: the 12-month return needs 13 closes
MONTH_ENDS = 13


class DualMomentum:
    """Hold while the close at the last month-end beats the close twelve month-ends before."""

    declared: ClassVar[Declared] = Declared(Timeframe.DAILY, None, LINES, CLOSES)

    def __init__(self) -> None:
        self._ends: deque[Decimal] = deque(maxlen=MONTH_ENDS)
        self._month: tuple[int, int] | None = None
        self._last: Decimal | None = None
        self._in = False

    def step(self, bar: Bar, holding: bool) -> bool:  # noqa: ARG002 - the Rule interface; the call is monthly state, not the position
        """Shown the next bar: on a new month, the call from the month-ends; else the last call."""
        month = (bar.day.year, bar.day.month)
        if self._month is not None and month != self._month and self._last is not None:
            self._ends.append(self._last)
            if len(self._ends) == MONTH_ENDS:
                self._in = self._ends[-1] > self._ends[0]
        self._month, self._last = month, bar.close
        return self._in


EPONYMOUS: Mapping[str, type[Rule]] = {"dual_momentum": DualMomentum}
