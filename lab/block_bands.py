"""block_bands - the blocks read from Bollinger's bands, kept apart from `lab.blocks` for its
400-line cap. Registered there like every other block."""

from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal

from desk.store import Bar
from desk.strategy import ZERO, _Window, lower_band
from lab.block_base import Block


class _PercentB(Block):
    """Bollinger's %b of the close over the `n` bars ending with this one (population deviation,
    bands at two), tested by `test` after `run` bars in a row; a flat window has no %b."""

    def __init__(
        self, n: int, pct: int, run: int, test: Callable[[Decimal, Decimal], bool]
    ) -> None:
        self._closes, self._limit, self._need, self._test = (
            _Window(n),
            Decimal(pct) / 100,
            run,
            test,
        )
        self._run = 0

    def see(self, bar: Bar, holding: bool) -> bool:  # noqa: ARG002 - the one interface of every block
        """Shown the next bar: whether the block fires."""
        self._closes.add(bar.close)
        dev = self._closes.deviation() if self._closes.full else ZERO
        band = lower_band(self._closes.mean(), dev) if dev else None
        percent_b = None if band is None else (bar.close - band) / (4 * dev)
        self._run = (
            self._run + 1 if percent_b is not None and self._test(percent_b, self._limit) else 0
        )
        return self._run >= self._need


class PercentBUnder(_PercentB):
    """Fires after `run` closes in a row with %b under `pct` per cent, at most 50
    (Connors' three under 20)."""

    def __init__(self, n: int, run: int, pct: int) -> None:
        super().__init__(n, pct, run, lambda b, limit: b < limit)


class PercentBOver(_PercentB):
    """Fires on a close with %b over `pct` per cent, at least 50."""

    def __init__(self, n: int, pct: int) -> None:
        super().__init__(n, pct, 1, lambda b, limit: b > limit)
