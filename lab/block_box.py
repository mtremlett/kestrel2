"""block_box - the spec book's blocks for Darvas's box: an entry on a close over the box's top
and a stop on a close under the raised stop. The two share one reading of the boxes, which
depends on whether the position is held, so a row names both, and the fast engine
(`lab.fast`) walks such a row bar by bar."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from desk.store import Bar
from lab.block_base import Block


@dataclass(frozen=True)
class _Box:
    top: Decimal
    bottom: Decimal


class _Formation:
    """A box in the making: a top no later high passes, and the lowest low since it."""

    def __init__(self, bar: Bar, n: int) -> None:
        self.top, self.low, self.low_age, self.n = bar.high, bar.low, 0, n

    def add(self, bar: Bar) -> _Box | None:
        """The box once `n` sessions have not undercut its bottom; None while it forms."""
        if bar.low < self.low:
            self.low, self.low_age = bar.low, 0
        else:
            self.low_age += 1
        return _Box(self.top, self.low) if self.low_age >= self.n else None


class _Boxes(Block):
    """Darvas's boxes (How I Made $2,000,000 in the Stock Market, 1960) read bar by bar: what
    happened on the bar, `breakout` (a close over a standing box's top) or `stopped` (held, and
    a close under the stop, the highest bottom of the boxes held through). A box stands once
    `n` sessions (his 3) have not undercut its bottom."""

    def __init__(self, n: int) -> None:
        self._n = n
        self._form: _Formation | None = None
        self._box: _Box | None = None
        self._stop: Decimal | None = None
        self.breakout = self.stopped = False

    def _restart(self, bar: Bar) -> None:
        self._form, self._box = _Formation(bar, self._n), None

    def _raise_stop(self, bottom: Decimal) -> None:
        self._stop = bottom if self._stop is None else max(self._stop, bottom)

    def _forming(self, bar: Bar, holding: bool) -> None:
        if self._form is None or bar.high > self._form.top:
            self._restart(bar)
            return
        self._box = self._form.add(bar)
        if self._box is not None and holding:
            self._raise_stop(self._box.bottom)

    def see(self, bar: Bar, holding: bool) -> bool:
        """Shown the next bar: whether this block's event happened on it."""
        self.breakout = self.stopped = False
        if not holding:
            self._stop = None
        elif self._stop is not None and bar.close < self._stop:
            self._restart(bar)
            self.stopped = True
            return self._event()
        if self._box is None:
            self._forming(bar, holding)
        elif bar.close > self._box.top:
            self._raise_stop(self._box.bottom)
            self._restart(bar)
            self.breakout = True
        elif bar.high > self._box.top or (not holding and bar.close < self._box.bottom):
            self._restart(bar)
        return self._event()

    def _event(self) -> bool:
        raise NotImplementedError


class DarvasBreakout(_Boxes):
    """Fires on a close over the top of a standing box."""

    def _event(self) -> bool:
        return self.breakout


class DarvasStop(_Boxes):
    """Fires, when held, on a close under the stop the boxes have raised."""

    def _event(self) -> bool:
        return self.stopped
