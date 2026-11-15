"""blocks - the building blocks a spec is made of, each written once: a small stateful class
shown every bar after its close, answering whether it fires. The indicators are the desk's
own proven parts (`desk.strategy`'s windows, held to the published tables), never copied.

Four kinds: an ENTRY fires when the rule should buy; an EXIT when it should sell; a STOP when
a held position has lost too much; a FILTER allows or forbids a buy. A block compares the bar
with what it saw BEFORE it, then takes it in. One not yet fed enough bars does not fire (a
filter then forbids).
"""

from __future__ import annotations

from collections import deque
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


class LowerRun(Block):
    """Fires after `n` bars in a row, this one the last, each with a lower high and a lower low
    than the bar before it."""

    def __init__(self, n: int) -> None:
        self._n, self._run = n, 0
        self._last: Bar | None = None

    def see(self, bar: Bar, holding: bool) -> bool:  # noqa: ARG002 - the one interface of every block
        """Shown the next bar: whether the block fires."""
        last, self._last = self._last, bar
        lower = last is not None and bar.high < last.high and bar.low < last.low
        self._run = self._run + 1 if lower else 0
        return self._run >= self._n


class _RangeEdge(Block):
    """Fires when the close lies within `pct` per cent of the range of the last `n` bars (this
    one's included), measured from its bottom or from its top. No range, no firing."""

    def __init__(self, n: int, pct: int, from_top: bool) -> None:
        self._highs, self._lows = _Window(n), _Window(n)
        self._pct, self._from_top = pct, from_top

    def see(self, bar: Bar, holding: bool) -> bool:  # noqa: ARG002 - the one interface of every block
        """Shown the next bar: whether the block fires."""
        self._highs.add(bar.high)
        self._lows.add(bar.low)
        if not self._highs.full:
            return False
        top, bottom = self._highs.high(), self._lows.low()
        gap = top - bar.close if self._from_top else bar.close - bottom
        return top > bottom and 100 * gap <= self._pct * (top - bottom)


class CloseNearRangeLow(_RangeEdge):
    """Fires on a close in the bottom `pct` per cent of the last `n` bars' range."""

    def __init__(self, n: int, pct: int) -> None:
        super().__init__(n, pct, from_top=False)


class CloseNearRangeHigh(_RangeEdge):
    """Fires on a close in the top `pct` per cent of the last `n` bars' range."""

    def __init__(self, n: int, pct: int) -> None:
        super().__init__(n, pct, from_top=True)


class _Channel(Block):
    """The channel of the `n` bars before a bar: its highest high and lowest low, taken in
    after the bar is judged. Subclasses say what the bar does against it."""

    def __init__(self, n: int) -> None:
        self._highs, self._lows = _Window(n), _Window(n)

    def judge(self, bar: Bar, high: Decimal, low: Decimal) -> bool:
        """Whether the bar fires against a full channel from `low` to `high`."""
        raise NotImplementedError

    def see(self, bar: Bar, holding: bool) -> bool:  # noqa: ARG002 - the one interface of every block
        """Shown the next bar: whether the block fires."""
        fires = self._highs.full and self.judge(bar, self._highs.high(), self._lows.low())
        self._highs.add(bar.high)
        self._lows.add(bar.low)
        return fires


class CloseAtRangeLow(_Channel):
    """Fires on a close at or under the lowest low of the `n` bars before, when that channel
    is a range: its width at most a tenth of its midpoint."""

    def judge(self, bar: Bar, high: Decimal, low: Decimal) -> bool:
        """Whether the close is at the low of a channel narrow enough to be a range."""
        return high - low <= (high + low) / 20 and bar.close <= low


class CloseAtMidpoint(_Channel):
    """Fires on a close at or over the midpoint of the channel of the `n` bars before."""

    def judge(self, bar: Bar, high: Decimal, low: Decimal) -> bool:
        """Whether the close is at or over the channel's midpoint."""
        return bar.close >= (high + low) / 2


class CloseUnderCloseAgo(Block):
    """Fires on a close under the close `n` bars before: a loser of the last `n` sessions."""

    def __init__(self, n: int) -> None:
        self._closes: deque[Decimal] = deque(maxlen=n)

    def see(self, bar: Bar, holding: bool) -> bool:  # noqa: ARG002 - the one interface of every block
        """Shown the next bar: whether the block fires."""
        fires = len(self._closes) == self._closes.maxlen and bar.close < self._closes[0]
        self._closes.append(bar.close)
        return fires


class TimeStop(Block):
    """Fires once the position has been seen held for `n` bars, however it stands."""

    def __init__(self, n: int) -> None:
        self._n, self._held = n, 0

    def see(self, bar: Bar, holding: bool) -> bool:  # noqa: ARG002 - the one interface of every block
        """Shown the next bar: whether the block fires."""
        self._held = self._held + 1 if holding else 0
        return self._held >= self._n


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
    """Fires on no bar: the stop that never stops, the exit that never leaves."""

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
_PCT = Param(int, 1, 50)
#: The one list of blocks by name; a spec names these and no others.
BLOCKS: Mapping[str, Spot] = {
    "highest_high": Spot(Kind.ENTRY, HighestHigh, {"n": _DAYS}),
    "lower_run": Spot(Kind.ENTRY, LowerRun, {"n": _DAYS}),
    "close_at_range_low": Spot(Kind.ENTRY, CloseAtRangeLow, {"n": _DAYS}),
    "close_under_close_ago": Spot(Kind.ENTRY, CloseUnderCloseAgo, {"n": _DAYS}),
    "close_at_midpoint": Spot(Kind.EXIT, CloseAtMidpoint, {"n": _DAYS}),
    "close_near_range_low": Spot(Kind.ENTRY, CloseNearRangeLow, {"n": _DAYS, "pct": _PCT}),
    "close_near_range_high": Spot(Kind.EXIT, CloseNearRangeHigh, {"n": _DAYS, "pct": _PCT}),
    "close_over_average": Spot(Kind.EXIT, CloseAboveAverage, {"n": _DAYS}),
    "lowest_low": Spot(Kind.EXIT, LowestLow, {"n": _DAYS}),
    "close_below_average": Spot(Kind.EXIT, CloseBelowAverage, {"n": _DAYS}),
    "trailing_stop": Spot(Kind.STOP, TrailingStop, {"pct": Param(Decimal, 1, 50)}),
    "time_stop": Spot(Kind.STOP, TimeStop, {"n": _DAYS}),
    "no_exit": Spot(Kind.EXIT, Never, {}),
    "no_stop": Spot(Kind.STOP, Never, {}),
    "close_above_average": Spot(Kind.FILTER, CloseAboveAverage, {"n": _DAYS}),
    "no_filter": Spot(Kind.FILTER, Always, {}),
}
