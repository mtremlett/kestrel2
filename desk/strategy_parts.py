"""strategy_parts - THE INDICATORS UNDER THE DAILY STRATEGIES: the rolling window, Wilder's and
the exponential average, Wilder's RSI and Bollinger's lower band. `desk.strategy` imports them
and gives them to its callers; a pure move, with no change of behaviour."""

from __future__ import annotations

from collections import deque
from decimal import Decimal

ZERO = Decimal(0)


class _Window:
    """The last `size` values and their sum."""

    def __init__(self, size: int) -> None:
        if size < 1:
            raise ValueError(f"a window of {size} values")
        self._values: deque[Decimal] = deque(maxlen=size)
        self._sum = ZERO

    def add(self, value: Decimal) -> None:
        if self.full:
            self._sum -= self._values[0]
        self._values.append(value)
        self._sum += value

    @property
    def full(self) -> bool:
        return len(self._values) == self._values.maxlen

    def mean(self) -> Decimal:
        return self._sum / len(self._values)

    def deviation(self) -> Decimal:
        """The population standard deviation, as Bollinger defines his bands."""
        mean = self.mean()
        return (sum(((v - mean) ** 2 for v in self._values), ZERO) / len(self._values)).sqrt()

    def high(self) -> Decimal:
        return max(self._values)

    def low(self) -> Decimal:
        return min(self._values)


class _Wilder:
    """Wilder's smoothing: the plain average of the first `size` values, then each new value
    weighted 1/`size`. None until it has `size` values."""

    def __init__(self, size: int) -> None:
        self._size, self._first = size, _Window(size)
        self.value: Decimal | None = None

    def add(self, value: Decimal) -> Decimal | None:
        if self.value is not None:
            self.value = (self.value * (self._size - 1) + value) / self._size
        else:
            self._first.add(value)
            self.value = self._first.mean() if self._first.full else None
        return self.value


class _Exponential(_Wilder):
    """The standard exponential average: seeded as Wilder's is, with the plain average of
    the first `size` values, then each new value weighted two parts in `size + 1`."""

    def add(self, value: Decimal) -> Decimal | None:
        if self.value is None:
            return super().add(value)
        self.value += (value - self.value) * 2 / (self._size + 1)
        return self.value


def rsi(gain: Decimal, loss: Decimal) -> Decimal:
    """Wilder's relative strength index (New Concepts in Technical Trading Systems, 1978) of
    a smoothed gain and a smoothed loss: 100 less 100 over one more than gain over loss, and
    100 where nothing was lost."""
    return Decimal(100) if loss == 0 else 100 - 100 / (1 + gain / loss)


def lower_band(mean: Decimal, deviation: Decimal, width: Decimal = Decimal(2)) -> Decimal:
    """Bollinger's lower band, at his setting of two deviations unless told another."""
    return mean - width * deviation
