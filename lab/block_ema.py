"""block_ema - the spec book's exponential-average blocks (Kell's trail and slow averages),
kept apart from `lab.blocks` (which has no room), over the desk's own `_Exponential`."""

from __future__ import annotations

from desk.store import Bar
from desk.strategy import _Exponential
from lab.block_base import Block


class CloseOverExponentials(Block):
    """Fires on a close over both its `n`-bar and its `slow`-bar exponential average, this
    bar's included. As a filter: a breakout leaving its base on rising averages."""

    def __init__(self, n: int, slow: int) -> None:
        self._quick, self._slow = _Exponential(n), _Exponential(slow)

    def see(self, bar: Bar, holding: bool) -> bool:  # noqa: ARG002 - the one interface of every block
        """Shown the next bar: whether the block fires."""
        quick, slow = self._quick.add(bar.close), self._slow.add(bar.close)
        return quick is not None and slow is not None and bar.close > max(quick, slow)


class CloseUnderExponential(Block):
    """Fires on a close under its `n`-bar exponential average, this bar's included."""

    def __init__(self, n: int) -> None:
        self._average = _Exponential(n)

    def see(self, bar: Bar, holding: bool) -> bool:  # noqa: ARG002 - the one interface of every block
        """Shown the next bar: whether the block fires."""
        average = self._average.add(bar.close)
        return average is not None and bar.close < average
