"""scalping - rules on one-minute bars (VwapReversion below), research: in no desk mapping
and never trade until it passes the ladder. The idea is Pradeep Bonde's "momentum burst"
(Stockbee, 2010s, taught on daily bars: a few days' sharp move on range that carries on a few
more); here it is worked on the one-minute bars of a session, an adaptation that is ours. Buy
when the close has risen over the last LOOKBACK bars by more than BURST times their average
range; sell after HOLD_BARS bars held or a close under the entry bar's low; be out at the
session's last bar. A new session empties the window."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import ClassVar

from desk import venues
from desk.intraday import Span
from desk.rollup import Candle

LOOKBACK = 3  #: bars the rise is measured over
BURST = Decimal(2)  #: how many average ranges the rise must exceed
HOLD_BARS = 10  #: bars a position is kept, the entry bar not counted
BELOW_VWAP = Decimal("0.01")  #: how far under the VWAP, as a fraction of it, a close is bought


def _session(venue: str, bar: Candle) -> venues.Hours:
    """The venue's session the bar falls in; a bar outside any is an error."""
    found = venues.open_at(venue, bar.start)
    if found is None:
        raise ValueError(f"{bar.start}: outside {venue}'s session")
    return found


class MomentumBurst:
    """Bonde's momentum burst on one-minute bars, a new session resetting the window."""

    span: ClassVar[Span] = Span.ONE_MINUTE

    def __init__(self, venue: str = "LSE") -> None:
        self.venue = venue
        self.opened: datetime | None = None
        self.window: list[Candle] = []
        self.held = 0
        self.stop = Decimal(0)  #: the entry bar's low

    def step(self, bar: Candle, holding: bool) -> bool:
        """Shown the next bar after its close: whether to be in the market from here."""
        found = _session(self.venue, bar)
        if found.open != self.opened:
            self.opened, self.window = found.open, []
        self.window = [*self.window, bar][-(LOOKBACK + 1) :]
        if bar.start + timedelta(minutes=self.span.value) >= found.close:
            return False
        if holding:
            self.held += 1
            return self.held < HOLD_BARS and bar.close >= self.stop
        if len(self.window) <= LOOKBACK or not self._burst():
            return False
        self.held, self.stop = 0, bar.low
        return True

    def _burst(self) -> bool:
        """Whether the close rose over the window by more than BURST average ranges."""
        recent = self.window[1:]
        average = sum((b.high - b.low for b in recent), Decimal(0)) / LOOKBACK
        return self.window[-1].close - self.window[0].close > BURST * average


class VwapReversion:
    """A one-minute mean reversion to the session's VWAP, a new session resetting it. VWAP, the
    volume-weighted average price, is the institutional benchmark of Berkowitz, Logue and Noser
    ("The Total Cost of Transactions on the NYSE", Journal of Finance, 1988); trading a close
    back to it from BELOW_VWAP under is the common practitioner's use, the rule here ours.
    Buy a close that far under the VWAP, sell at or over it, be out at the session's last bar;
    a bar of no volume adds nothing to the VWAP."""

    span: ClassVar[Span] = Span.ONE_MINUTE

    def __init__(self, venue: str = "LSE") -> None:
        self.venue = venue
        self.opened: datetime | None = None
        self.worth = Decimal(0)  #: typical price times volume, summed over the session
        self.volume = 0

    @property
    def vwap(self) -> Decimal | None:
        """The VWAP of the bars seen this session, None until one has traded."""
        return self.worth / self.volume if self.volume else None

    def step(self, bar: Candle, holding: bool) -> bool:
        """Shown the next bar after its close: whether to be in the market from here."""
        found = _session(self.venue, bar)
        if found.open != self.opened:
            self.opened, self.worth, self.volume = found.open, Decimal(0), 0
        self.worth += (bar.high + bar.low + bar.close) / 3 * bar.volume
        self.volume += bar.volume
        vwap = self.vwap
        if vwap is None or bar.start + timedelta(minutes=self.span.value) >= found.close:
            return False
        return bar.close < vwap if holding else bar.close < vwap * (1 - BELOW_VWAP)
