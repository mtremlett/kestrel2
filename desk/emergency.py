"""emergency - THE THREE EMERGENCIES, IN NUMBERS (EMG-01). An emergency, a crash and a black
swan are each a fall that is measured, set here in advance, and each has the one thing the desk
does about it. Nothing here acts: the crash watch measures and reads, and the halt and the
protective sale do what the level calls for.

A fall is read in the line's MARKET'S terms, as its stop is: a line that makes three times its
market's move has fallen a third as far as its price. It is measured twice: below the last
session's close (the day's fall), and below the highest close of the last MONTH sessions (how
far the month has fallen, which keeps a crash a crash on the days between its worst ones).

The numbers were set against the archive's S&P 500 from 2010 to November 2026. Its worst day
fell 11.9% and its worst month 32.6%, both in March 2020, so no day of it was a black swan; a
crash, as defined here, came in six episodes read at each day's close (26 days) and in eight
read at its low (37 days). Each US share of the desk's had an emergency on at most two or
three days a year, read at the close."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from desk.lines import YARDSTICK, Line
from desk.orders import STOP_FALL

MONTH = 20  #: sessions: a fall "below the month's high" is below the highest close of these


class Action(Enum):
    """What the desk does about it, and until when. He is told at once, whichever it is."""

    PARK = "buys no more of that line while it lasts; its stop rests at the broker"
    HALT = "buys nothing on any line while it lasts; every stop rests at the broker"
    CASH = "sells every position, and buys nothing until he says so"


@dataclass(frozen=True)
class Definition:
    """One of the three, in numbers: either fall reached makes it."""

    market: bool  #: read on the market itself, the yardstick; if not, on any one line
    day: Decimal  #: the fall in one day
    high: Decimal | None  #: the fall below the month's high; none where only the day counts
    action: Action

    def words(self) -> str:
        """The definition, as it is said."""
        whose = "the market" if self.market else "any one line"
        slow = f", or {self.high:.0%} below its month's high" if self.high is not None else ""
        return f"{whose} down {self.day:.0%} in a day{slow}"


class Level(Enum):
    """The three, the gravest last, and each graver one of the market is the one before it too.

    EMERGENCY: a shock to one line: in one day, the whole fall its stop allows a holding.
    CRASH: the market falls as it has in one episode every two or three years.
    BLACK SWAN: the market falls further than on any day or in any month of the history the
    rules were tested on (and, in a day, as far as halts the US market a second time): the
    desk has no test that says what its rules do there, so it stands in cash until he says."""

    EMERGENCY = Definition(False, STOP_FALL, None, Action.PARK)
    CRASH = Definition(True, Decimal("0.05"), Decimal("0.15"), Action.HALT)
    BLACK_SWAN = Definition(True, Decimal("0.13"), Decimal("0.35"), Action.CASH)


@dataclass(frozen=True)
class Fall:
    """How far one line has fallen, in its market's terms, each a part of one: 0.05 is 5%."""

    line: Line
    day: Decimal  #: below the last session's close; nothing when it stands above it
    high: Decimal  #: below the highest close of the last MONTH sessions

    def __post_init__(self) -> None:
        if not 0 <= self.day <= self.high < 1:
            raise ValueError(
                f"{self.line.symbol}: no line has fallen {self.day} in a day and {self.high}"
                " below its month's high"
            )

    @property
    def level(self) -> Level | None:
        """The gravest of the three this fall is, or none of them. Only the yardstick's fall
        is the market's: one line, however far it falls, is never a crash."""
        met = None
        for level in Level:
            rule = level.value
            if rule.market and self.line != YARDSTICK:
                continue
            if self.day >= rule.day or (rule.high is not None and self.high >= rule.high):
                met = level
        return met

    def words(self) -> str:
        """The fall, which of the three it is, and what the desk does: one message."""
        times = f" (at {self.line.leverage} times its market)" if self.line.leverage > 1 else ""
        fallen = (
            f"{self.line.symbol}{times} is {self.day:.1%} below its last close and"
            f" {self.high:.1%} below its month's high, in its market's terms"
        )
        level = self.level
        if level is None:
            return f"{fallen}: none of the three emergencies."
        rule, name = level.value, level.name.replace("_", " ")
        return f"{name}, which is {rule.words()}: {fallen}. The desk {rule.action.value}."


def measure(line: Line, closes: Sequence[Decimal], price: Decimal) -> Fall:
    """A line's fall as its newest price stands. closes are its closes on the sessions before
    this one, the oldest first, as many of the last MONTH as it has traded; price is its newest
    bar's close, never a bar's low: a print the market took back within the bar is no fall."""
    month = closes[-MONTH:]
    if not month or min(*month, price) <= 0:
        raise ValueError(
            f"{line.symbol}: no fall is measured from {len(month)} closes, the least"
            f" {min(month, default=None)}, to a price of {price}"
        )

    def below(close: Decimal) -> Decimal:
        return max(Decimal(0), (1 - price / close) / line.leverage)

    return Fall(line, below(month[-1]), below(max(month)))


def alarms(falls: Iterable[Fall]) -> tuple[Fall, ...]:
    """The falls that are one of the three, the gravest first: the first is what the desk does
    as a whole, and each emergency after it names a line of its own."""
    order = list(Level)
    grave = [(order.index(level), fall) for fall in falls if (level := fall.level) is not None]
    return tuple(fall for _, fall in sorted(grave, key=lambda ranked: -ranked[0]))
