"""spans - THE TIMEFRAMES the fast store holds: one Span for each of 1m, 2m, 5m, 10m, 15m, 30m,
1h, 4h, 1d and 1wk, with its length and the rule for where a bar starts. Marks are counted in
UTC from EPOCH: a bar of a span starts on a whole multiple of its length (a one-minute bar on a
whole minute, a four-hour bar on 00:00, 04:00, 08:00 ... so London's open is one), a week's on
a Monday 00:00. A venue's own session-aligned bars are built by desk.rollup, not here. Five
minutes and a day keep the store's older names and their own writers; every other span is
written and read as `Timed`. Spans from an hour up live in the long database."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

DAILY, FIVE = "daily", "five-minute"  #: the two spans of bar the store held first
EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
_HOUR, _DAY = 3600, 86400


def _seconds(moment: datetime) -> int:
    """The first whole second since EPOCH at or after a moment in UTC, so that a bar starts at
    or after a moment exactly when its second does; a moment in no zone, or off UTC, is refused."""
    if moment.utcoffset() != timedelta(0):
        raise ValueError(f"{moment!r} is not a moment in UTC")
    return -((EPOCH - moment) // timedelta(seconds=1))


@dataclass(frozen=True)
class Span:
    """One timeframe: its name in the store, its length and the offset of its first mark."""

    name: str
    seconds: int
    anchor: int = 0  #: seconds past EPOCH of one mark (EPOCH was a Thursday)

    @property
    def long(self) -> bool:
        """It is kept in the long database: an hour or more."""
        return self.seconds >= _HOUR

    @property
    def home(self) -> str:
        """The span whose database holds this one's bars: the daily's or the five-minute's."""
        return DAILY if self.long else FIVE

    def marks(self, moment: datetime) -> bool:
        """A bar of this span starts at the moment."""
        return not moment.microsecond and (_seconds(moment) - self.anchor) % self.seconds == 0


SPANS = {
    span.name: span
    for span in (
        Span("1m", 60),
        Span("2m", 120),
        Span(FIVE, 300),
        Span("10m", 600),
        Span("15m", 900),
        Span("30m", 1800),
        Span("1h", _HOUR),
        Span("4h", 4 * _HOUR),
        Span(DAILY, _DAY),
        Span("1wk", 7 * _DAY, anchor=4 * _DAY),
    )
}


@dataclass(frozen=True)
class Five:
    """A five-minute bar, named by the moment it starts."""

    start: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int

    def __post_init__(self) -> None:
        if not SPANS[FIVE].marks(self.start):
            raise ValueError(f"{self.start!r} is not a five-minute mark in UTC")


@dataclass(frozen=True)
class Timed:
    """A bar of any span but the two with their own writers, named by the moment it starts."""

    span: str
    start: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int

    def __post_init__(self) -> None:
        if self.span in (FIVE, DAILY) or self.span not in SPANS:
            raise ValueError(f"{self.span!r} is no span written as a timed bar")
        if not SPANS[self.span].marks(self.start):
            raise ValueError(f"{self.start!r} is not a {self.span} mark in UTC")
