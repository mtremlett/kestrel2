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

RANGE_BARS = 6  #: the opening range: the session's first six five-minute bars


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
