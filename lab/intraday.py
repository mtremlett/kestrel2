"""intraday - the opening range breakout on five-minute bars (Crabel, Day Trading with Short Term
Price Patterns and Opening Range Breakout, 1990), a research rule: it is in no desk mapping and
never trades until it passes the ladder. The range is the session's first six bars (30 minutes);
after them buy a close above its high, sell a close under its low, and be out at the last bar."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import ClassVar

from desk import venues
from desk.intraday import Span
from desk.rollup import Candle
from desk.strategy import _Window, lower_band

RANGE_BARS = 6  #: the opening range: the session's first six five-minute bars
BAND_BARS = 20  #: Bollinger's band: the session's last twenty five-minute closes


class OpeningRangeBreakout:
    """Crabel's opening range breakout on five-minute bars, a new session resetting the range."""

    span: ClassVar[Span] = Span.FIVE_MINUTES

    def __init__(self, venue: str = "LSE") -> None:
        self.venue = venue
        self.opened: datetime | None = None
        self.seen = 0
        self.high = self.low = Decimal(0)

    def step(self, bar: Candle, holding: bool) -> bool:
        """Shown the next bar after its close: whether to be in the market from here."""
        found = venues.open_at(self.venue, bar.start)
        if found is None:
            raise ValueError(f"{bar.start}: outside {self.venue}'s session")
        if found.open != self.opened:
            self.opened, self.seen, self.high, self.low = found.open, 0, bar.high, bar.low
        if self.seen < RANGE_BARS:
            self.seen += 1
            self.high, self.low = max(self.high, bar.high), min(self.low, bar.low)
            return False
        if bar.start + timedelta(minutes=self.span.value) >= found.close:
            return False
        return bar.close >= self.low if holding else bar.close > self.high


class IntradayMeanReversion:
    """Bollinger's bands (Bollinger on Bollinger Bands, 2001) on five-minute bars, 20 bars and 2
    deviations counted within the session: buy a close under the lower band, sell a close over
    the middle, be out at the last bar. Each session refills the band, holding nothing till full."""

    span: ClassVar[Span] = Span.FIVE_MINUTES

    def __init__(self, venue: str = "LSE") -> None:
        self.venue = venue
        self.opened: datetime | None = None
        self.closes = _Window(BAND_BARS)

    def step(self, bar: Candle, holding: bool) -> bool:
        """Shown the next bar after its close: whether to be in the market from here."""
        found = venues.open_at(self.venue, bar.start)
        if found is None:
            raise ValueError(f"{bar.start}: outside {self.venue}'s session")
        if found.open != self.opened:
            self.opened, self.closes = found.open, _Window(BAND_BARS)
        self.closes.add(bar.close)
        if not self.closes.full or bar.start + timedelta(minutes=self.span.value) >= found.close:
            return False
        mean = self.closes.mean()
        if holding:
            return bar.close <= mean
        return bar.close < lower_band(mean, self.closes.deviation())
