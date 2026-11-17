"""block_sequential - the spec book's blocks for DeMark's TD Sequential: an entry on the
thirteenth countdown bar, and an exit on a nine-bar sell setup. Both read one counter,
`Counts`, which the fast engine drives with its own whole numbers."""

from __future__ import annotations

from decimal import Decimal
from typing import Generic, TypeVar

from desk.eponymous_demark_sequential import BACK, COUNTDOWN, LAG, SETUP
from desk.store import Bar
from lab.block_base import Block

_N = TypeVar("_N", Decimal, float)


class Counts(Generic[_N]):
    """The book's counts, fed one close and low at a time, as `desk.eponymous_demark_sequential`
    keeps them; it reads no position, so the entry and the exit each hold their own."""

    def __init__(self) -> None:
        self._closes: list[_N] = []
        self._lows: list[_N] = []
        self._down = self._up = 0
        self._count: int | None = None

    def see(self, close: _N, low: _N) -> tuple[bool, bool]:
        """Shown the next bar: whether it is the thirteenth countdown bar, and whether it
        completes a sell setup."""
        self._closes.append(close)
        self._lows.append(low)
        n = len(self._closes)
        if n > BACK:
            ref = self._closes[n - 1 - BACK]
            self._down = self._down + 1 if close < ref else 0
            self._up = self._up + 1 if close > ref else 0
        sell = self._up == SETUP
        if sell:
            self._count = None
        elif self._down == SETUP:
            self._count = 0
        elif self._count is not None and n > LAG and close <= self._lows[n - 1 - LAG]:
            self._count += 1
        bought = self._count == COUNTDOWN
        if bought:
            self._count = None
        return bought, sell


class CountdownBuy(Block):
    """Fires on the thirteenth bar of a countdown that a nine-bar buy setup began."""

    def __init__(self) -> None:
        self._seq: Counts[Decimal] = Counts()

    def see(self, bar: Bar, holding: bool) -> bool:  # noqa: ARG002 - the one interface of every block
        """Shown the next bar: whether the block fires."""
        return self._seq.see(bar.close, bar.low)[0]


class SellSetup(Block):
    """Fires on the ninth close in a row over the close four bars before it."""

    def __init__(self) -> None:
        self._seq: Counts[Decimal] = Counts()

    def see(self, bar: Bar, holding: bool) -> bool:  # noqa: ARG002 - the one interface of every block
        """Shown the next bar: whether the block fires."""
        return self._seq.see(bar.close, bar.low)[1]
