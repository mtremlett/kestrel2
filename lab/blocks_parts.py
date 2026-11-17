"""blocks_parts - the spec book's blocks over a run of day-to-day moves: the big-move stop, and
Clenow's rising score with its rolling log-slope. Kept apart from `lab.blocks`, which imports
them and holds the one list."""

from __future__ import annotations

from collections import deque
from decimal import Decimal

from desk.eponymous_clenow_momentum import YEAR
from desk.store import Bar
from desk.strategy import ZERO
from lab.block_base import Block


class _Moves:
    """The big moves among the last `n` day-to-day changes of the close: a change is big when
    it is more than `pct` per cent of the close before."""

    def __init__(self, n: int, pct: int) -> None:
        self._limit = Decimal(pct) / 100
        self._big: deque[bool] = deque(maxlen=n)
        self._last: Decimal | None = None

    def add(self, close: Decimal) -> bool:
        """Takes in the close; whether a big move lies among the last `n` changes."""
        if self._last is not None:
            self._big.append(abs(close / self._last - 1) > self._limit)
        self._last = close
        return any(self._big)


class LogSlope:
    """The annualised slope of the exponential regression of the last `n` closes times its
    R-squared (Clenow's score). Each close's logarithm is worked out once, as it arrives, and
    kept in a rolling window, where the desk's own `score` works out all `n` on every bar."""

    def __init__(self, n: int) -> None:
        self._logs: deque[Decimal] = deque(maxlen=n)

    def add(self, close: Decimal) -> None:
        """Takes in the next close."""
        self._logs.append(close.ln())

    @property
    def full(self) -> bool:
        """Whether `n` closes have been taken in."""
        return len(self._logs) == self._logs.maxlen

    def score(self) -> Decimal:
        """The score of the closes held; the same number, to the digit, as the desk's `score`."""
        n, ys = len(self._logs), self._logs
        mx, my = Decimal(n - 1) / 2, sum(ys, ZERO) / n
        sxx = sum(((x - mx) ** 2 for x in range(n)), ZERO)
        sxy = sum(((x - mx) * (y - my) for x, y in enumerate(ys)), ZERO)
        syy = sum(((y - my) ** 2 for y in ys), ZERO)
        if syy == 0:
            return ZERO
        return (((sxy / sxx) * YEAR).exp() - 1) * (sxy * sxy / (sxx * syy))


class RisingScore(Block):
    """Fires when the last `n` closes score above nothing (see `LogSlope`) and none of the last
    `n` changes was a move of more than `pct` per cent."""

    def __init__(self, n: int, pct: int) -> None:
        self._slope, self._moves = LogSlope(n), _Moves(n, pct)

    def see(self, bar: Bar, holding: bool) -> bool:  # noqa: ARG002 - the one interface of every block
        """Shown the next bar: whether the block fires."""
        self._slope.add(bar.close)
        big = self._moves.add(bar.close)
        return self._slope.full and not big and self._slope.score() > 0


class BigMove(Block):
    """Fires while a move of more than `pct` per cent lies among the last `n` changes."""

    def __init__(self, n: int, pct: int) -> None:
        self._moves = _Moves(n, pct)

    def see(self, bar: Bar, holding: bool) -> bool:  # noqa: ARG002 - the one interface of every block
        """Shown the next bar: whether the block fires."""
        return self._moves.add(bar.close)
