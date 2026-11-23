"""block_swing - the spec book's blocks for Raschke's Turtle Soup, kept apart from `lab.blocks`
(which has no room): an entry on a failed breakdown, and a stop at the buying day's low."""

from __future__ import annotations

from collections import deque
from decimal import Decimal

from desk.store import Bar
from lab.block_base import Block


class TurtleSoup(Block):
    """Fires on a bar whose low is under the lowest low of the `n` bars before it, when that
    older low was set `gap` or more bars before and the close is back above it."""

    def __init__(self, n: int, gap: int) -> None:
        self._lows: deque[Decimal] = deque(maxlen=n)
        self._gap = gap

    def see(self, bar: Bar, holding: bool) -> bool:  # noqa: ARG002 - the one interface of every block
        """Shown the next bar: whether the block fires."""
        fired = False
        if len(self._lows) == self._lows.maxlen:
            older = min(self._lows)
            newest = len(self._lows) - 1 - list(reversed(self._lows)).index(older)
            fired = bar.low < older < bar.close and len(self._lows) - newest >= self._gap
        self._lows.append(bar.low)
        return fired


class UnderEntryLow(Block):
    """Fires on a close under the low of the bar on which the position was bought."""

    def __init__(self) -> None:
        self._last: tuple[Decimal, bool] | None = None  #: the last bar's low, and if held then
        self._level: Decimal | None = None

    def see(self, bar: Bar, holding: bool) -> bool:
        """Shown the next bar: whether the block fires."""
        if self._last is not None and holding and not self._last[1]:
            self._level = self._last[0]
        self._last = (bar.low, holding)
        return holding and self._level is not None and bar.close < self._level
