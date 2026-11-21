"""block_breadth - the spec book's block for Zweig's breadth thrust (Winning on Wall Street,
1986): an entry when the 10-day exponential average of the breadth ratio climbs from under 0.40
to over 0.615 inside 10 sessions. It reads RATIO BARS, as Mansfield's row does: a bar whose
close is the day's advances over advances plus declines, built by the caller from the store's
breadth (`lab.universe.breadth`). Its numbers are the book's own, not settings. The sale is the
time stop, 230 sessions after the buy, as in `desk/eponymous_zweig_breadth_thrust.py`."""

from __future__ import annotations

from collections import deque
from decimal import Decimal

from desk.store import Bar
from desk.strategy import _Exponential
from lab.block_base import Block

WINDOW = 10
LOW, HIGH = Decimal("0.40"), Decimal("0.615")


class BreadthThrust(Block):
    """Fires when the average of the ratio closes is over 0.615 with a value under 0.40 among
    its last ten."""

    def __init__(self) -> None:
        self._average = _Exponential(WINDOW)
        self._recent: deque[Decimal] = deque(maxlen=WINDOW)

    def see(self, bar: Bar, holding: bool) -> bool:  # noqa: ARG002 - the one interface of every block
        """Shown the next bar: whether the block fires."""
        average = self._average.add(bar.close)
        if average is not None:
            self._recent.append(average)
        return average is not None and average > HIGH and min(self._recent) < LOW
