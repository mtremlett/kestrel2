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
from decimal import Decimal
from functools import partial

from desk.store import Bar
from desk.strategy import ZERO, _Wilder, _Window, rsi
from lab.block_bands import (
    CloseOverBandAfterSqueeze,
    CloseOverEmas,
    CloseUnderEma,
    PercentBOver,
    PercentBUnderRun,
    TrendTemplate,
)
from lab.block_base import Block, Kind, Param, Spot
from lab.block_months import (
    MonthEndNotOverAgo,
    MonthEndNotOverAverage,
    MonthEndOverAgo,
    MonthEndOverAverage,
)
from lab.block_sequential import CountdownBuy, SellSetup
from lab.block_swing import TurtleSoup, UnderEntryLow
from lab.blocks_parts import BigMove, RisingScore
from lab.blocks_parts import (
    LogSlope as LogSlope,  # noqa: PLC0414 - re-exported: callers import it from here
)


class HighestHigh(Block):
    """Fires on a close over the highest high of the `n` bars before."""

    def __init__(self, n: int) -> None:
        self._highs = _Window(n)

    def see(self, bar: Bar, holding: bool) -> bool:  # noqa: ARG002 - the one interface of every block
        """Shown the next bar: whether the block fires."""
        fires = self._highs.full and bar.close > self._highs.high()
        self._highs.add(bar.high)
        return fires


class HighestHighOnVolume(Block):
    """Fires on a close over the highest high of the `n` bars before, the day's volume at least
    `pct` per cent of the average volume of those bars (Zanger's heavy volume)."""

    def __init__(self, n: int, pct: int) -> None:
        self._highs, self._volumes, self._heavy = _Window(n), _Window(n), Decimal(pct) / 100

    def see(self, bar: Bar, holding: bool) -> bool:  # noqa: ARG002 - the one interface of every block
        """Shown the next bar: whether the block fires."""
        fires = (
            self._highs.full
            and bar.close > self._highs.high()
            and Decimal(bar.volume) >= self._heavy * self._volumes.mean()
        )
        self._highs.add(bar.high)
        self._volumes.add(Decimal(bar.volume))
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


class CloseAtOrBelowAverage(_Average):
    """Fires on a close at or under its `n`-bar average, this bar's included."""

    def __init__(self, n: int) -> None:
        super().__init__(n, lambda close, mean: close <= mean)


class CloseOverRisingAverage(Block):
    """Fires on a close over its `n`-bar average, this bar's included, when that average is
    higher than it was `ago` bars before (Weinstein's stage 2)."""

    def __init__(self, n: int, ago: int) -> None:
        self._closes = _Window(n)
        self._means: deque[Decimal] = deque(maxlen=ago + 1)

    def see(self, bar: Bar, holding: bool) -> bool:  # noqa: ARG002 - the one interface of every block
        """Shown the next bar: whether the block fires."""
        self._closes.add(bar.close)
        if not self._closes.full:
            return False
        mean = self._closes.mean()
        self._means.append(mean)
        return len(self._means) == self._means.maxlen and mean > self._means[0] and bar.close > mean


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


class _Keltner(Block):
    """The band of the last `n` bars, this one's included: the average of the typical price
    (high, low and close over three) plus or minus the average of the range."""

    def __init__(self, n: int, upper: bool) -> None:
        self._typical, self._range, self._upper = _Window(n), _Window(n), upper

    def see(self, bar: Bar, holding: bool) -> bool:  # noqa: ARG002 - the one interface of every block
        """Shown the next bar: whether the close is over the upper band or under the lower."""
        self._typical.add((bar.high + bar.low + bar.close) / 3)
        self._range.add(bar.high - bar.low)
        if not self._typical.full:
            return False
        centre, width = self._typical.mean(), self._range.mean()
        return bar.close > centre + width if self._upper else bar.close < centre - width


class RsiUnder(Block):
    """Fires when Wilder's `n`-bar RSI of the close, this bar's included, is under `pct`; with
    no loss in the window it is 100, and an RSI of exactly `pct` is not under."""

    def __init__(self, n: int, pct: int) -> None:
        self._gain, self._loss, self._under = _Wilder(n), _Wilder(n), Decimal(pct)
        self._last: Decimal | None = None

    def see(self, bar: Bar, holding: bool) -> bool:  # noqa: ARG002 - the one interface of every block
        """Shown the next bar: whether the block fires."""
        last, self._last = self._last, bar.close
        if last is None:
            return False
        gain = self._gain.add(max(bar.close - last, ZERO))
        loss = self._loss.add(max(last - bar.close, ZERO))
        return gain is not None and loss is not None and rsi(gain, loss) < self._under


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


_DAYS = Param(int, 2, 400)
_PCT = Param(int, 1, 50)
_AGO = Param(int, 1, 50)
_HEAVY = Param(int, 101, 500)
_LOW, _HIGH = Param(int, 1, 49), Param(int, 51, 99)
#: The one list of blocks by name; a spec names these and no others.
BLOCKS: Mapping[str, Spot] = {
    "highest_high": Spot(Kind.ENTRY, HighestHigh, {"n": _DAYS}),
    "highest_high_on_volume": Spot(Kind.ENTRY, HighestHighOnVolume, {"n": _DAYS, "pct": _HEAVY}),
    "close_over_band_after_squeeze": Spot(
        Kind.ENTRY, CloseOverBandAfterSqueeze, {"n": _DAYS, "look": _DAYS}
    ),
    "close_over_rising_average": Spot(
        Kind.ENTRY, CloseOverRisingAverage, {"n": _DAYS, "ago": _AGO}
    ),
    "lower_run": Spot(Kind.ENTRY, LowerRun, {"n": _DAYS}),
    "month_end_over_average": Spot(Kind.ENTRY, MonthEndOverAverage, {"n": _DAYS}),
    "month_end_not_over_average": Spot(Kind.EXIT, MonthEndNotOverAverage, {"n": _DAYS}),
    "month_end_over_ago": Spot(Kind.ENTRY, MonthEndOverAgo, {"n": _AGO}),
    "month_end_not_over_ago": Spot(Kind.EXIT, MonthEndNotOverAgo, {"n": _AGO}),
    "close_at_range_low": Spot(Kind.ENTRY, CloseAtRangeLow, {"n": _DAYS}),
    "close_over_keltner_band": Spot(Kind.ENTRY, partial(_Keltner, upper=True), {"n": _DAYS}),
    "close_under_keltner_band": Spot(Kind.EXIT, partial(_Keltner, upper=False), {"n": _DAYS}),
    "percent_b_under_run": Spot(
        Kind.ENTRY, PercentBUnderRun, {"n": _DAYS, "pct": _LOW, "run": _AGO}
    ),
    "percent_b_over": Spot(Kind.EXIT, PercentBOver, {"n": _DAYS, "pct": _HIGH}),
    "rsi_under": Spot(Kind.ENTRY, RsiUnder, {"n": _DAYS, "pct": _PCT}),
    "close_under_close_ago": Spot(Kind.ENTRY, CloseUnderCloseAgo, {"n": _DAYS}),
    "close_at_midpoint": Spot(Kind.EXIT, CloseAtMidpoint, {"n": _DAYS}),
    "close_near_range_low": Spot(Kind.ENTRY, CloseNearRangeLow, {"n": _DAYS, "pct": _PCT}),
    "close_near_range_high": Spot(Kind.EXIT, CloseNearRangeHigh, {"n": _DAYS, "pct": _PCT}),
    "close_over_average": Spot(Kind.EXIT, CloseAboveAverage, {"n": _DAYS}),
    "rising_score": Spot(Kind.ENTRY, RisingScore, {"n": _DAYS, "pct": _PCT}),
    "big_move": Spot(Kind.STOP, BigMove, {"n": _DAYS, "pct": _PCT}),
    "close_at_or_under_average": Spot(Kind.EXIT, CloseAtOrBelowAverage, {"n": _DAYS}),
    "lowest_low": Spot(Kind.EXIT, LowestLow, {"n": _DAYS}),
    "close_below_average": Spot(Kind.EXIT, CloseBelowAverage, {"n": _DAYS}),
    "trailing_stop": Spot(Kind.STOP, TrailingStop, {"pct": Param(Decimal, 1, 50)}),
    "time_stop": Spot(Kind.STOP, TimeStop, {"n": _DAYS}),
    "no_exit": Spot(Kind.EXIT, Never, {}),
    "no_stop": Spot(Kind.STOP, Never, {}),
    "close_above_average": Spot(Kind.FILTER, CloseAboveAverage, {"n": _DAYS}),
    "close_over_emas": Spot(Kind.FILTER, CloseOverEmas, {"n": _DAYS, "slow": _DAYS}),
    "close_under_ema": Spot(Kind.EXIT, CloseUnderEma, {"n": _DAYS}),
    "td_countdown_buy": Spot(Kind.ENTRY, CountdownBuy, {}),
    "td_sell_setup": Spot(Kind.EXIT, SellSetup, {}),
    "turtle_soup": Spot(Kind.ENTRY, TurtleSoup, {"n": _DAYS, "gap": _AGO}),
    "under_entry_low": Spot(Kind.STOP, UnderEntryLow, {}),
    "no_filter": Spot(Kind.FILTER, Always, {}),
    "trend_template": Spot(Kind.FILTER, TrendTemplate, {}),
}
