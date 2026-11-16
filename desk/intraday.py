"""intraday - THE ONE ENGINE, INTRADAY (R-RUNNER-199, his ruling of 16 November 2026): a rule
declares the span of the bar it decides on, and is shown one bar at a time, after its close,
only the bars of its venue's session; a bar outside the session, or of another span, is
refused, never skipped. The template is strategy.py's: a change of mind is a BUY or a SELL,
every other bar a HOLD, and only what is held is sold. `run` is the backtest; `latest` is the
desk's step at one bar, the rule worked up to it with the position the book holds. The two
agree bar for bar (the parity test), and no rule here trades until it passes the ladder."""

from __future__ import annotations

from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import ClassVar, Protocol

from desk import venues
from desk.rollup import Candle
from desk.strategy import Action


class Span(Enum):
    """The bar an intraday rule decides on, as minutes."""

    ONE_MINUTE = 1
    FIVE_MINUTES = 5


@dataclass(frozen=True)
class IntradayDecision:
    """What a rule said of a line on one bar."""

    strategy: str
    symbol: str
    at: datetime  #: when the bar decided on began, timezone-aware UTC
    action: Action


class IntradayRule(Protocol):
    """A rule shown one bar at a time, declaring the span it decides on."""

    span: ClassVar[Span]

    def step(self, bar: Candle, holding: bool) -> bool:
        """Shown the next bar after its close: whether to be in the market from here."""
        ...


def _checked(venue: str, span: Span, bars: Sequence[Candle]) -> None:
    """Refuse a bar that is not whole, in time order, inside one session of the venue."""
    last: datetime | None = None
    for bar in bars:
        found = venues.open_at(venue, bar.start)
        length = timedelta(minutes=span.value)
        if found is None or not found.open <= bar.start <= found.close - length:
            raise ValueError(f"{bar.start}: not a {span.value}-minute bar in {venue}'s session")
        if last is not None and bar.start <= last:
            raise ValueError(f"{bar.start}: not after the bar before it, {last}")
        last = bar.start


def run(
    name: str,
    rule: IntradayRule,
    venue: str,
    symbol: str,
    bars: Sequence[Candle],
    last: bool | None = None,
) -> Iterator[IntradayDecision]:
    """The rule's decision on every bar, holding what it last chose; on the last bar,
    holding `last` instead when it is given."""
    _checked(venue, rule.span, bars)
    holding = False
    for n, bar in enumerate(bars):
        if last is not None and n == len(bars) - 1:
            holding = last
        wants = rule.step(bar, holding)
        action = (
            Action.SELL
            if holding and not wants
            else Action.BUY
            if wants and not holding
            else Action.HOLD
        )
        holding = wants
        yield IntradayDecision(name, symbol, bar.start, action)


def latest(
    name: str,
    make: Callable[[], IntradayRule],
    venue: str,
    symbol: str,
    bars: Sequence[Candle],
    held: bool,
) -> IntradayDecision:
    """The desk's step at the last bar: a fresh rule worked up the bars to it, the position
    on that bar read from the book (`held`), not from the rule."""
    return [*run(name, make(), venue, symbol, bars, held)][-1]
