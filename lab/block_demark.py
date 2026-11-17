"""block_demark - the spec book's TD Sequential blocks, kept apart from `lab.blocks` (which has
no room): an entry on the thirteenth countdown bar that follows a nine-bar buy setup, and an
exit on a nine-bar sell setup. Both read one counter, as the desk's Python rule does."""

from __future__ import annotations

from desk.store import Bar
from lab.block_base import Block

SETUP, BACK, COUNTDOWN, LAG = 9, 4, 13, 2  #: the book's setup, compare-back, countdown, lag


class _Sequential(Block):
    """The run of closes under / over the close four bars back, and the countdown it starts."""

    def __init__(self) -> None:
        self._bars: list[Bar] = []
        self._down = self._up = 0
        self._count: int | None = None

    def settle(self, bar: Bar) -> tuple[bool, bool]:
        """Takes in the bar; whether it is the countdown's thirteenth, and a nine-bar sell setup."""
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
        return bought, sell_setup


class DemarkCountdown(_Sequential):
    """Fires on the thirteenth countdown bar after a nine-bar buy setup."""

    def see(self, bar: Bar, holding: bool) -> bool:  # noqa: ARG002 - the one interface of every block
        """Shown the next bar: whether the block fires."""
        return self.settle(bar)[0]


class DemarkSellSetup(_Sequential):
    """Fires on the ninth close in a row over the close four bars before."""

    def see(self, bar: Bar, holding: bool) -> bool:  # noqa: ARG002 - the one interface of every block
        """Shown the next bar: whether the block fires."""
        return self.settle(bar)[1]
