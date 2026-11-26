"""eponymous_connors - Connors' rules, ported under the one template (SET 1 of the eponymous
strategies, R-RUNNER-60 and R-RUNNER-61). The paper desk does not trade them.

CONNORS %B (R-RUNNER-61). AUTHORS: Larry Connors and Cesar Alvarez. SOURCE: High Probability ETF
Trading (TradingMarkets, 2009), the %b chapter. The book's rule, long only: buy at the close when
the close is above its 200-day average and %b (where the close sits in Bollinger's 20-day, 2
deviation bands: 0 at the lower band, 1 at the upper) has closed under 0.2 three days running;
sell at the close when %b closes over 0.8. AUTHOR'S TEST: US index and sector ETFs, daily bars,
from each ETF's launch to 2008. The published figure is NOT written here: no copy of the book was
on hand and a figure from memory would be a guess; the ladder measures the rule after costs.
Secondary sources (blogs, undated here) quote the same entry but exit on %b over 0.5 (the
middle band) or on a close over the 5-day average, so the RANGE of the exit is 0.5 to 0.8; this
port takes the book's 0.8. A flat window has no bands, so no %b: it ends the run of low days.

---- RSI-2 below ----

AUTHORS: Larry Connors and Cesar Alvarez. SOURCE: Short Term Trading Strategies That Work
(TradingMarkets, 2008), the chapter on the 2-period RSI. The book's rule, long only: buy at the
close when the close is above its 200-day simple average and the 2-day RSI closes under 10
(the book also tests under 5, which the desk's frozen `rsi2_pullback` takes); sell at the
close that is above the 5-day simple average.

AUTHOR'S TEST: US stocks (and the index ETFs), daily bars, roughly 1995 to 2007. The author's
published figure for the rule is NOT written here: this session had no copy of the book to
read it from, and a figure quoted from memory would be a guess. The ladder measures the rule
itself, after costs, on the desk's own data. Secondary sources (blogs and forums, undated here)
quote entry thresholds from 2 to 10 and exits on the 5-day or the 2-day average, so the
RANGE of the setting is 2 to 10; this port takes the book's own, under 10, and the 5-day exit.
Holding period: none. Both rules sell on their own signal alone (%b over 0.8, a close over
the 5-day average); the books give no day limit, so none is declared.

The old desk is a quarry for the reading only; none of its code is copied.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal, localcontext
from typing import ClassVar

from desk.lines import LINES
from desk.store import Bar
from desk.strategy import (
    ARITHMETIC,
    CLOSES,
    ZERO,
    Decision,
    Declared,
    Rule,
    Timeframe,
    _run,
    _Wilder,
    _Window,
    lower_band,
    rsi,
)

NAME = "connors_rsi2"
#: the book's days of trend, days of exit, and the RSI under which to buy
TREND, EXIT, ENTRY = 200, 5, 10


class ConnorsRsi2:
    """The book's rule: in above the 200-day average at a 2-day RSI under 10; out over the 5-day."""

    declared: ClassVar[Declared] = Declared(Timeframe.DAILY, None, LINES, CLOSES)

    def __init__(self) -> None:
        self._long, self._short = _Window(TREND), _Window(EXIT)
        self._gain, self._loss = _Wilder(2), _Wilder(2)
        self._last: Decimal | None = None

    def step(self, bar: Bar, holding: bool) -> bool:
        """Shown the next bar after its close: whether to be in the market from here."""
        close, last, index = bar.close, self._last, None
        self._long.add(close)
        self._short.add(close)
        self._last = close
        if last is not None:
            gain = self._gain.add(max(close - last, ZERO))
            loss = self._loss.add(max(last - close, ZERO))
            if gain is not None and loss is not None:
                index = rsi(gain, loss)
        if holding:
            return close <= self._short.mean()
        return index is not None and self._long.full and close > self._long.mean() and index < ENTRY


#: the book's Bollinger window, run of low days, the %b to buy under and the %b to sell over
WINDOW, RUN, LOW, HIGH = 20, 3, Decimal("0.2"), Decimal("0.8")


class ConnorsPercentB:
    """The book's rule: in above the 200-day average after three closes under 0.2; out over 0.8."""

    declared: ClassVar[Declared] = Declared(Timeframe.DAILY, None, LINES, CLOSES)

    def __init__(self) -> None:
        self._long, self._bands = _Window(TREND), _Window(WINDOW)
        self._low_days = 0

    def step(self, bar: Bar, holding: bool) -> bool:
        """Shown the next bar after its close: whether to be in the market from here."""
        close = bar.close
        self._long.add(close)
        self._bands.add(close)
        dev = self._bands.deviation() if self._bands.full else ZERO
        b = (close - lower_band(self._bands.mean(), dev)) / (4 * dev) if dev else None
        self._low_days = self._low_days + 1 if b is not None and b < LOW else 0
        if holding:
            return b is None or b <= HIGH
        return self._long.full and close > self._long.mean() and self._low_days >= RUN


def decide_percent_b(bars: Mapping[str, Sequence[Bar]]) -> tuple[Decision, ...]:
    """The %b rule's decision for every line and every day the bars cover."""
    with localcontext(ARITHMETIC):
        return tuple(
            d
            for symbol, series in bars.items()
            for d in _run("connors_percent_b", ConnorsPercentB(), symbol, series)
        )


def decide(bars: Mapping[str, Sequence[Bar]]) -> tuple[Decision, ...]:
    """The rule's decision for every line and every day the bars cover."""
    with localcontext(ARITHMETIC):
        return tuple(
            d for symbol, series in bars.items() for d in _run(NAME, ConnorsRsi2(), symbol, series)
        )


EPONYMOUS: Mapping[str, type[Rule]] = {NAME: ConnorsRsi2, "connors_percent_b": ConnorsPercentB}
