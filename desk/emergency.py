"""emergency - THE THREE EMERGENCIES, IN NUMBERS (EMG-01). An emergency, a crash and a black
swan are each a fall that is measured, set here in advance, and each has the one thing the desk
does about it. Nothing here acts: the crash watch measures and reads, and the halt and the
protective sale do what the level calls for.

A fall is measured twice: below the last session's close (the day's fall), and below the
highest close of the last MONTH sessions (the month's fall, which keeps a crash a crash on the
days between its worst ones). A line that makes three times its market's move is read in its
MARKET'S terms, as its stop is: a third of its price's fall.

The market is the yardstick, and its numbers were set on the series the desk reads: the S&P
500 in pounds as London trades it (VUSA since May 2012, and the yardstick, its twin, since
2019), in the archive to November 2026. Its worst day closed 7.2% down and its worst month
23.4%, and within a day it read 8.7% and 26.0%, all in March 2020: a black swan is beyond
every one of them. A crash, as defined here and read at each day's close, came on 26 days in
six episodes (days within a month of each other are one episode). New York's own close is
another series, with other falls, and these numbers are not its."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from decimal import ROUND_DOWN, Decimal
from enum import Enum

from desk.lines import YARDSTICK, Line
from desk.orders import STOP_FALL

MONTH = 20  #: sessions: a fall "below the month's high" is below the highest close of these


def _set(part: Decimal) -> str:
    """A number set in advance, said whole: 0.125 is 12.5%, never 12%."""
    return f"{(part * 100).normalize():f}%"


def _read(part: Decimal) -> str:
    """A measured fall, cut to a tenth of a per cent and never rounded up to a number it did
    not reach: 0.04996 is 4.9%."""
    return f"{part.quantize(Decimal('0.001'), ROUND_DOWN):.1%}"


class Action(Enum):
    """What the desk does about it, and until when; he is told at once, whichever it is. A
    reading within a day raises an emergency or a crash and never lifts it: only a session
    that closes with the fall no longer one does."""

    PARK = (
        "buys no more of that line until a session closes clear of it, and sells nothing:"
        " a holding is left to its stop"
    )
    HALT = (
        "buys nothing on any line until a session closes clear of it, and sells nothing:"
        " every holding is left to its stop"
    )
    CASH = "sells every position, and buys nothing until he says so"


@dataclass(frozen=True)
class Definition:
    """One of the three, in numbers: either fall reached makes it."""

    market: bool  #: read on the market itself, the yardstick; if not, on any one line
    day: Decimal  #: the fall in one day
    high: Decimal | None  #: the fall below the month's high; none where only the day counts
    action: Action

    def __post_init__(self) -> None:
        if not 0 < self.day < (1 if self.high is None else self.high) <= 1:
            raise ValueError(f"no emergency is a fall of {self.day} in a day, or {self.high}")

    def words(self) -> str:
        """The definition, as it is said."""
        whose = "the market" if self.market else "any one line's market"
        slow = "" if self.high is None else f", or {_set(self.high)} below its month's high"
        return f"{whose} down {_set(self.day)} in a day{slow}"


class Level(Enum):
    """The three, the gravest last, and each graver one of the market is the one before it too.

    EMERGENCY: a shock to one line: in one day, the whole fall its stop allows a holding.
    CRASH: the market falls as it has in one episode every two or three years.
    BLACK SWAN: the market falls further than it has read at any moment of the history the
    rules are tested on. No test says what the rules do there, and to sell everything on a
    fall that was only a crash costs more than to halt on one that was more: so its numbers
    are the first round ones beyond the history's worst, and the desk stands in cash."""

    EMERGENCY = Definition(False, STOP_FALL, None, Action.PARK)
    CRASH = Definition(True, Decimal("0.04"), Decimal("0.12"), Action.HALT)
    BLACK_SWAN = Definition(True, Decimal("0.10"), Decimal("0.30"), Action.CASH)


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
    def market(self) -> bool:
        """Whether this is the market's own fall: the yardstick's, whose series set the numbers."""
        return self.line.symbol == YARDSTICK.symbol

    @property
    def level(self) -> Level | None:
        """The gravest of the three this fall is, or none of them. One line, however far it
        falls, is never a crash."""
        met = None
        for level in Level:
            rule = level.value
            slow = rule.high is not None and self.high >= rule.high
            if (self.day >= rule.day or slow) and (self.market or not rule.market):
                met = level
        return met

    def words(self) -> str:
        """The fall, which of the three it is, and what the desk does: one message."""
        line, level, fallen = self.line, self.level, "not below its last close"
        if self.day:
            fallen = f"{_read(self.day * line.leverage)} below its last close"
        if self.day and line.leverage > 1:
            fallen += f" (its market {_read(self.day)}: it moves {line.leverage} times as far)"
        if self.market:
            fallen += f" and {_read(self.high)} below its month's high"
        if level is None:
            return f"{line.symbol} is {fallen}: none of the three emergencies."
        rule, name = level.value, level.name.replace("_", " ")
        said = f"{name}, which is {rule.words()}: {line.symbol} is {fallen}"
        return f"{said}. The desk {rule.action.value}."


def measure(line: Line, closes: Sequence[Decimal], price: Decimal) -> Fall:
    """A line's fall as its newest price stands. closes are its closes on the sessions before
    this one, the oldest first, the last MONTH of them at least; price is its newest bar's
    close, never a bar's low: a print the market took back within the bar is no fall. For a
    line that multiplies its market, the month's fall is its own divided, as its stop is."""
    month = closes[-MONTH:]
    if len(month) < MONTH or not all(p.is_finite() and p > 0 for p in (*month, price)):
        raise ValueError(
            f"{line.symbol}: no fall is measured from {len(month)} of the month's {MONTH}"
            f" closes to a price of {price}: every one must be a price"
        )

    def below(close: Decimal) -> Decimal:
        return max(Decimal(0), (1 - price / close) / line.leverage)

    return Fall(line, below(month[-1]), below(max(month)))


def alarms(falls: Iterable[Fall]) -> tuple[Fall, ...]:
    """The falls that are one of the three, the gravest first: a crash or a black swan, the
    market's, is what the desk does as a whole, and each emergency names a line of its own.
    The market's fall must be among them: a market nobody read is not a calm one."""
    read, order = tuple(falls), list(Level)
    if not any(fall.market for fall in read):
        raise ValueError(f"the market, {YARDSTICK.symbol}, is not among the {len(read)} falls read")
    grave = [(order.index(level), fall) for fall in read if (level := fall.level) is not None]
    return tuple(fall for _, fall in sorted(grave, key=lambda ranked: -ranked[0]))
