"""units - THE STEP OF UNITS (M3): a line part in dollars and part in pounds is not judged.

A London line of a dollar fund can arrive part in dollars and part in pounds, a step under the
price store's jump. On a line in pounds, a close that moves in one day by that day's rate of
exchange, or one over it, to within TOLERANCE, on a day the master names no real move, is such
a step: the line waits on its bars, with the day as its reason.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from desk.lines import Line
from desk.store import Bar
from lab.rung import Rates

TOLERANCE = Decimal("0.03")


def refuse(line: Line, bars: Sequence[Bar], rates: Rates) -> None:
    """Raise, naming the day, if the line's bars step by the pound and the dollar's rate."""
    if line.currency != "GBP" or line.leverage != 1:  #: a leveraged line's real crashes sit
        return  #: as near the rate (5QQQ x0.770, 3 April 2025)
    named = {day for day, _ in line.real_moves}
    for before, bar in zip(bars, bars[1:], strict=False):
        rate = rates.get(bar.day)
        if rate is None or bar.day in named:
            continue
        move = bar.close / before.close
        if any(abs(move / step - 1) <= TOLERANCE for step in (rate, 1 / rate)):
            raise ValueError(
                f"{line.symbol}: a step of units on {bar.day}: {before.close} to {bar.close} "
                f"is the rate of exchange, {rate}, and no move the master names"
            )
