"""block_sequential - the spec book's blocks for DeMark's TD Sequential (The New Science of
Technical Analysis, 1994), long side: an entry on the thirteenth bar of a buy countdown and an
exit on a nine-bar sell setup, which also cancels a countdown. The setup's length `n` (his 9) is
the one setting, ranged as a variant; the rest are the book's own numbers."""

from __future__ import annotations

from decimal import Decimal

from desk.store import Bar
from lab.block_base import Block

BACK, COUNTDOWN, LAG = 4, 13, 2


class SellSetup(Block):
    """Fires on the `n`th close in a row over the close four bars before it."""

    def __init__(self, n: int) -> None:
        self._n = n
        self._closes: list[Decimal] = []
        self._run = 0

    def see(self, bar: Bar, holding: bool) -> bool:  # noqa: ARG002 - the one interface of every block
        """Shown the next bar: whether the block fires."""
        self._closes.append(bar.close)
        n = len(self._closes)
        self._run = self._run + 1 if n > BACK and bar.close > self._closes[n - 1 - BACK] else 0
        return self._run == self._n


class BuyCountdown(Block):
    """Fires on the thirteenth bar, after an `n`-bar buy setup, whose close is at or under the
    low two bars before; an `n`-bar sell setup cancels the count, a fresh buy setup restarts it."""

    def __init__(self, n: int) -> None:
        self._n = n
        self._bars: list[Bar] = []
        self._down = self._up = 0
        self._count: int | None = None

    def see(self, bar: Bar, holding: bool) -> bool:  # noqa: ARG002 - the one interface of every block
        """Shown the next bar: whether the block fires."""
        self._bars.append(bar)
        n = len(self._bars)
        if n > BACK:
            ref = self._bars[n - 1 - BACK].close
            self._down = self._down + 1 if bar.close < ref else 0
            self._up = self._up + 1 if bar.close > ref else 0
        if self._up == self._n:
            self._count = None
        elif self._down == self._n:
            self._count = 0
        elif self._count is not None and n > LAG and bar.close <= self._bars[n - 1 - LAG].low:
            self._count += 1
        fired = self._count == COUNTDOWN
        if fired:
            self._count = None
        return fired
