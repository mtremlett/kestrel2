"""block_trails - the spec book's exponential-trail blocks (Kell's base n' break): a filter
that allows a buy only with the close over both of two exponential averages, an exit on a close
under the faster one. Over the desk's own exponential average, fed every bar."""

from __future__ import annotations

from decimal import Decimal

from desk.store import Bar
from desk.strategy import _Exponential
from lab.block_base import Block


class CloseOverEmas(Block):
    """Fires on a close over both the `n`-bar and the `slow`-bar exponential average of the
    close, this bar's included; not before both are seeded."""

    def __init__(self, n: int, slow: int) -> None:
        self._fast, self._slow = _Exponential(n), _Exponential(slow)

    def see(self, bar: Bar, holding: bool) -> bool:  # noqa: ARG002 - the one interface of every block
        """Shown the next bar: whether the block fires."""
        fast, slow = self._fast.add(bar.close), self._slow.add(bar.close)
        return fast is not None and slow is not None and bar.close > max(fast, slow)


class CloseUnderEma(Block):
    """Fires on a close under its `n`-bar exponential average, this bar's included."""

    def __init__(self, n: int) -> None:
        self._trail = _Exponential(n)

    def see(self, bar: Bar, holding: bool) -> bool:  # noqa: ARG002 - the one interface of every block
        """Shown the next bar: whether the block fires."""
        trail: Decimal | None = self._trail.add(bar.close)
        return trail is not None and bar.close < trail
