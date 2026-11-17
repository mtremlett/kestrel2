"""block_months - the spec book's blocks that judge on a month's last close, kept apart from
`lab.blocks` (which has no room), each written once over the desk's own `_Window`."""

from __future__ import annotations

from desk.store import Bar
from desk.strategy import _Window
from lab.block_base import Block


class _MonthEnd(Block):
    """The last closes of the last `n` months, each known to be a month's last only when the
    next month's first bar arrives, and judged on that bar: over their average, or not."""

    def __init__(self, n: int) -> None:
        self._ends = _Window(n)
        self._previous: Bar | None = None

    def settle(self, bar: Bar) -> bool | None:
        """Takes in the bar; on a month's first bar, whether the month before closed over the
        average of the month-end closes (this one's included); None on any other bar."""
        previous = self._previous
        self._previous = bar
        if previous is None or (previous.day.year, previous.day.month) == (
            bar.day.year,
            bar.day.month,
        ):
            return None
        self._ends.add(previous.close)
        return self._ends.full and previous.close > self._ends.mean()


class MonthEndOverAverage(_MonthEnd):
    """Fires on a month's first bar when the month before closed over its `n`-month average."""

    def see(self, bar: Bar, holding: bool) -> bool:  # noqa: ARG002 - the one interface of every block
        """Shown the next bar: whether the block fires."""
        return self.settle(bar) is True


class MonthEndNotOverAverage(_MonthEnd):
    """Fires on a month's first bar when the month before did not close over its average."""

    def see(self, bar: Bar, holding: bool) -> bool:  # noqa: ARG002 - the one interface of every block
        """Shown the next bar: whether the block fires."""
        return self.settle(bar) is False
