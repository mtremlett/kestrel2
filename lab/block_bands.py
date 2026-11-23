"""block_bands - the spec book's blocks that read where the close sits in Bollinger's bands,
kept apart from `lab.blocks` (which has no room), each written once over the desk's own
`_Window` and `lower_band`."""

from __future__ import annotations

from collections import deque
from decimal import Decimal

from desk.store import Bar
from desk.strategy import ZERO, _Exponential, _Window, lower_band
from lab.block_base import Block


class _PercentB(Block):
    """Where the close sits in the bands of the last `n` bars (this one's included): %b, 0 at
    the lower band (2 deviations under the average) and 1 at the upper. A flat window has no
    bands, so no %b, and the block does not fire."""

    def __init__(self, n: int, pct: int) -> None:
        self._bands, self._pct = _Window(n), Decimal(pct) / 100

    def percent_b(self, bar: Bar) -> Decimal | None:
        """Takes in the bar; its %b, or None while the window is not full or is flat."""
        self._bands.add(bar.close)
        dev = self._bands.deviation() if self._bands.full else ZERO
        return (bar.close - lower_band(self._bands.mean(), dev)) / (4 * dev) if dev else None


class PercentBOver(_PercentB):
    """Fires while %b of the last `n` bars is over `pct` per cent."""

    def see(self, bar: Bar, holding: bool) -> bool:  # noqa: ARG002 - the one interface of every block
        """Shown the next bar: whether the block fires."""
        b = self.percent_b(bar)
        return b is not None and b > self._pct


class PercentBUnderRun(_PercentB):
    """Fires once %b of the last `n` bars has been under `pct` per cent on `run` bars in a row,
    this one the last."""

    def __init__(self, n: int, pct: int, run: int) -> None:
        super().__init__(n, pct)
        self._run, self._days = run, 0

    def see(self, bar: Bar, holding: bool) -> bool:  # noqa: ARG002 - the one interface of every block
        """Shown the next bar: whether the block fires."""
        b = self.percent_b(bar)
        self._days = self._days + 1 if b is not None and b < self._pct else 0
        return self._days >= self._run


class CloseOverBandAfterSqueeze(Block):
    """Bollinger's squeeze: fires on a close over the upper band (2 deviations over the `n`-bar
    average) when, on the bar before, the band width (4 deviations over the average) was the
    lowest of the last `look` widths, ties included."""

    def __init__(self, n: int, look: int) -> None:
        self._closes, self._widths, self._squeezed = _Window(n), _Window(look), False

    def see(self, bar: Bar, holding: bool) -> bool:  # noqa: ARG002 - the one interface of every block
        """Shown the next bar: whether the block fires."""
        self._closes.add(bar.close)
        if not self._closes.full:
            return False
        mean, dev = self._closes.mean(), self._closes.deviation()
        width = 4 * dev / mean
        self._widths.add(width)
        squeezed, self._squeezed = self._squeezed, self._widths.full and width <= self._widths.low()
        return squeezed and bar.close > mean + 2 * dev


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


class TrendTemplate(Block):
    """Fires while Minervini's Trend Template holds, this bar's included: the close over the
    150- and 200-day averages, the 150 over the 200, the 200 higher than 21 sessions before,
    the 50 over both, the close over the 50, 30% over the 252-session low and within 25% of
    its high. Not before the year and the month's averages are seen."""

    def __init__(self) -> None:
        self._avg = {n: _Window(n) for n in (50, 150, 200)}
        self._high, self._low = _Window(252), _Window(252)
        self._slow: deque[Decimal] = deque(maxlen=22)

    def see(self, bar: Bar, holding: bool) -> bool:  # noqa: ARG002 - the one interface of every block
        """Shown the next bar: whether the block fires."""
        for window in self._avg.values():
            window.add(bar.close)
        if self._avg[200].full:
            self._slow.append(self._avg[200].mean())
        self._high.add(bar.high)
        self._low.add(bar.low)
        if not (self._high.full and len(self._slow) == self._slow.maxlen):
            return False
        fifty, mid, slow = (self._avg[n].mean() for n in (50, 150, 200))
        return (
            bar.close > mid > slow
            and fifty > mid
            and bar.close > fifty
            and slow > self._slow[0]
            and bar.close >= Decimal("1.30") * self._low.low()
            and bar.close >= Decimal("0.75") * self._high.high()
        )
