"""blocks - the building blocks a spec is made of, each written once: a small stateful class
shown every bar after its close, answering whether it fires. The indicators are the desk's
own proven parts (`desk.strategy`'s windows, held to the published tables), never copied.

Four kinds: an ENTRY fires when the rule should buy; an EXIT when it should sell; a STOP when
a held position has lost too much; a FILTER allows or forbids a buy. A block compares the bar
with what it saw BEFORE it, then takes it in. One not yet fed enough bars does not fire (a
filter then forbids).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from desk.store import Bar
from desk.strategy import _Window


class Kind(Enum):
    """Where in a rule a block sits."""

    ENTRY = "entry"
    EXIT = "exit"
    STOP = "stop"
    FILTER = "filter"


class Block:
    """Shown each bar with whether the position is held; says whether it fires."""

    def see(self, bar: Bar, holding: bool) -> bool:
        """Shown the next bar: whether the block fires."""
        raise NotImplementedError


class HighestHigh(Block):
    """Fires on a close over the highest high of the `n` bars before."""

    def __init__(self, n: int) -> None:
        self._highs = _Window(n)

    def see(self, bar: Bar, holding: bool) -> bool:  # noqa: ARG002 - the one interface of every block
        """Shown the next bar: whether the block fires."""
        fires = self._highs.full and bar.close > self._highs.high()
        self._highs.add(bar.high)
        return fires


class LowestLow(Block):
    """Fires on a close under the lowest low of the `n` bars before."""

    def __init__(self, n: int) -> None:
        self._lows = _Window(n)

    def see(self, bar: Bar, holding: bool) -> bool:  # noqa: ARG002 - the one interface of every block
        """Shown the next bar: whether the block fires."""
        fires = self._lows.full and bar.close < self._lows.low()
        self._lows.add(bar.low)
        return fires


class _Average(Block):
    """A plain average of the close over `n` bars; `fires` is told the close and the average."""

    def __init__(self, n: int, test: Callable[[Decimal, Decimal], bool]) -> None:
        self._closes, self._test = _Window(n), test

    def see(self, bar: Bar, holding: bool) -> bool:  # noqa: ARG002 - the one interface of every block
        """Shown the next bar: whether the block fires."""
        self._closes.add(bar.close)
        return self._closes.full and self._test(bar.close, self._closes.mean())


class CloseAboveAverage(_Average):
    """Fires on a close over its `n`-bar average, this bar's included. As a filter: an uptrend."""

    def __init__(self, n: int) -> None:
        super().__init__(n, lambda close, mean: close > mean)


class CloseBelowAverage(_Average):
    """Fires on a close under its `n`-bar average, this bar's included."""

    def __init__(self, n: int) -> None:
        super().__init__(n, lambda close, mean: close < mean)


class TrailingStop(Block):
    """Fires on a close `pct` per cent or more under the highest close since the position was
    first seen held. Nothing while the position is not held."""

    def __init__(self, pct: Decimal) -> None:
        self._keep = 1 - pct / 100
        self._peak: Decimal | None = None

    def see(self, bar: Bar, holding: bool) -> bool:  # noqa: ARG002 - the one interface of every block
        """Shown the next bar: whether the block fires."""
        if not holding:
            self._peak = None
            return False
        self._peak = bar.close if self._peak is None else max(self._peak, bar.close)
        return bar.close <= self._peak * self._keep


class Always(Block):
    """Fires on every bar: the filter that forbids nothing."""

    def see(self, bar: Bar, holding: bool) -> bool:  # noqa: ARG002 - the one interface of every block
        """Shown the next bar: whether the block fires."""
        return True


class Never(Block):
    """Fires on no bar: the stop that never stops."""

    def see(self, bar: Bar, holding: bool) -> bool:  # noqa: ARG002 - the one interface of every block
        """Shown the next bar: whether the block fires."""
        return False


@dataclass(frozen=True)
class Param:
    """One parameter a block takes: its type and the closed range it must lie in."""

    kind: type[int] | type[Decimal]
    low: int
    high: int


@dataclass(frozen=True)
class Spot:
    """A block as the registry holds it: the kind of place it fits, its class, its parameters
    in the order its constructor takes them."""

    kind: Kind
    make: Callable[..., Block]
    params: Mapping[str, Param]


_DAYS = Param(int, 2, 400)
#: The one list of blocks by name; a spec names these and no others.
BLOCKS: Mapping[str, Spot] = {
    "highest_high": Spot(Kind.ENTRY, HighestHigh, {"n": _DAYS}),
    "lowest_low": Spot(Kind.EXIT, LowestLow, {"n": _DAYS}),
    "close_below_average": Spot(Kind.EXIT, CloseBelowAverage, {"n": _DAYS}),
    "trailing_stop": Spot(Kind.STOP, TrailingStop, {"pct": Param(Decimal, 1, 50)}),
    "no_stop": Spot(Kind.STOP, Never, {}),
    "close_above_average": Spot(Kind.FILTER, CloseAboveAverage, {"n": _DAYS}),
    "no_filter": Spot(Kind.FILTER, Always, {}),
}
