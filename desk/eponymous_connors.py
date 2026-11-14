"""eponymous_connors - Connors' RSI-2, ported as a rule under the one template (SET 1 of the
eponymous strategies, R-RUNNER-60). The paper desk does not trade it.

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
    Timeframe,
    _run,
    _Wilder,
    _Window,
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


def decide(bars: Mapping[str, Sequence[Bar]]) -> tuple[Decision, ...]:
    """The rule's decision for every line and every day the bars cover."""
    with localcontext(ARITHMETIC):
        return tuple(
            d for symbol, series in bars.items() for d in _run(NAME, ConnorsRsi2(), symbol, series)
        )
