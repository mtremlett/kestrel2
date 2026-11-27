"""eponymous_faber_tactical - Faber's timing rule, ported as a rule under the one template (SET 1
of the eponymous strategies, R-RUNNER-73). Family: momentum (trend following). The paper desk
does not trade it.

AUTHOR: Mebane T. Faber. SOURCE: A Quantitative Approach to Tactical Asset Allocation (2007,
Journal of Wealth Management; SSRN). The rule, one instrument at a time: at each month's last
close, be long when the close is above its 10-month simple average of month-end closes, and in
cash when it is not; stay put between month-ends. (The paper's other trend filter, the 200-day
average, is the same idea; the 10-month is its headline.)

AUTHOR'S TEST: the S&P 500 and four other asset classes, monthly, from 1973 (the S&P from 1901
in later editions). The author's published figure is NOT written here: this session had no copy
of the paper to read it from, and a figure quoted from memory would be a guess. The ladder
measures the rule itself, after costs, on the desk's own data. Secondary sources agree on the
10-month average, and some use 200 days or 12 months; this port takes the paper's own, 10.

THE DESK'S READING: the template shows a rule one daily bar at a time, and the last bar of a
month is known to be so only when the next month's first bar arrives. So the month-end close is
judged on that first bar: the decision is made one session after the paper's, on the same
information. Nothing between month-ends changes it.
Holding period: none. The sale is the month-end close under its 10-month average alone; the
paper gives no day limit, so none is declared.

The old desk is a quarry for the reading only; none of its code is copied.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import localcontext
from typing import ClassVar

from desk.lines import LINES
from desk.store import Bar
from desk.strategy import ARITHMETIC, CLOSES, Decision, Declared, Rule, Timeframe, _run, _Window

NAME = "faber_tactical"
#: the paper's months of average
MONTHS = 10


class FaberTactical:
    """The paper's rule: in while the month-end close is over the 10-month average of them."""

    declared: ClassVar[Declared] = Declared(Timeframe.DAILY, None, LINES, CLOSES)

    def __init__(self) -> None:
        self._ends = _Window(MONTHS)
        self._previous: Bar | None = None
        self._wants = False

    def step(self, bar: Bar, holding: bool) -> bool:  # noqa: ARG002 - the template's signature; this rule ignores the position
        """Shown the next bar after its close: whether to be in the market from here."""
        previous = self._previous
        self._previous = bar
        if previous is not None and (previous.day.year, previous.day.month) != (
            bar.day.year,
            bar.day.month,
        ):
            self._ends.add(previous.close)
            self._wants = self._ends.full and previous.close > self._ends.mean()
        return self._wants


def decide(bars: Mapping[str, Sequence[Bar]]) -> tuple[Decision, ...]:
    """The rule's decision for every line and every day the bars cover."""
    with localcontext(ARITHMETIC):
        return tuple(
            d
            for symbol, series in bars.items()
            for d in _run(NAME, FaberTactical(), symbol, series)
        )


EPONYMOUS: Mapping[str, type[Rule]] = {NAME: FaberTactical}
