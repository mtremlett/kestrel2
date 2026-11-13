"""emergency - THE THREE EMERGENCIES, IN NUMBERS (EMG-01). An emergency, a crash and a black
swan are each a fall that is measured, set here in advance, and each has the one thing the desk
does about it. Nothing here acts: the crash watch measures and reads, and the halt and the
protective sale do what the level calls for.

A fall is measured twice: below the close of the session before (the day's fall), and below
the highest close of the last MONTH sessions (the month's fall, which keeps a crash a crash on
the days between its worst ones). A line that makes three times its market's move is judged in
its MARKET'S terms, as its stop is: it must fall three times as far.

The market is the yardstick, and its numbers were set on the series the desk reads: the S&P
500 in pounds as London trades it (VUSA since May 2012, and the yardstick, its twin, since
2019), in the archive to November 2026. Its worst day closed 7.2% down and its worst month
23.4%, and within a day it read 8.7% and 26.0%, all in March 2020: a black swan is beyond
every one of them. A crash, as defined here and read at each day's close, came on 26 days in
six episodes (days within a month of each other are one episode). New York's own close is
another series, with other falls, and these numbers are not its.

His words for the three name more than falls, and each has its home. A desk fault is the
book not being the broker's, and the send path already buys nothing then. A spike in
volatility is what a fall of a crash's size is. A market halt is a market with no price. A
reading here is of a dated bar and says its session, so an old price is never read as today's;
and what cannot be read at all is said to be UNREAD, never taken for calm. Whether the newest
bar is new enough, within its session, is the crash watch's to say: it holds the clock."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_DOWN, Decimal
from enum import Enum

from desk import venues
from desk.bars import Five
from desk.lines import YARDSTICK, Line
from desk.orders import STOP_FALL
from desk.store import JUMP, Bar

MONTH = 20  #: sessions: a fall "below the month's high" is below the highest close of these


class Unread(Exception):
    """A line, or the market, could not be read. That is no calm reading, and nothing here
    treats it as one: whoever asked must say the line is unread."""


def _set(part: Decimal) -> str:
    """A number set in advance, said whole: 0.125 is 12.5%, never 12%."""
    return f"{(part * 100).normalize():f}%"


def _cut(part: Decimal) -> Decimal:
    """A measured fall, cut to a tenth of a per cent and never rounded up to a number it did
    not reach: 0.04996 is said as 4.9%."""
    return part.quantize(Decimal("0.001"), ROUND_DOWN)


def _below(part: Decimal, what: str) -> str:
    if _cut(part):
        return f"{_cut(part):.1%} below {what}"
    return f"{'under 0.1%' if part else 'not'} below {what}"


class Response(Enum):
    """What the level calls for the desk to do, and until when; he is told at once, whichever
    it is. A reading within a day raises an emergency or a crash and never lifts it: only a day
    that ends with the fall no longer one does. Neither sells: the rules' own sales and the
    stops go on as ever. What was done is for the part that does it to say."""

    PARK = (
        "buy no more of that line until it ends a day clear of an emergency, and sell nothing"
        " because of it: the rules and the stops sell as ever"
    )
    HALT = (
        "buy nothing on any line until the market ends a day clear of a crash, and sell nothing"
        " because of it: the rules and the stops sell as ever"
    )
    CASH = "sell every position, and buy nothing until the operator says so"


@dataclass(frozen=True)
class Definition:
    """One of the three, in numbers: either fall reached makes it."""

    market: bool  #: read on the market itself, the yardstick; if not, on any other line
    day: Decimal  #: the fall in one day
    high: Decimal | None  #: the fall below the month's high; none where only the day counts
    response: Response

    def __post_init__(self) -> None:
        if not 0 < self.day < (1 if self.high is None else self.high) <= 1:
            raise ValueError(f"no emergency is a fall of {self.day} in a day, or {self.high}")

    def words(self) -> str:
        """The definition, as it is said."""
        whose = f"the market ({YARDSTICK.symbol})" if self.market else "any one line"
        geared = "" if self.market else " (a leveraged line: its market down as far)"
        slow = "" if self.high is None else f", or {_set(self.high)} below its month's high"
        return f"{whose} down {_set(self.day)} in a day{geared}{slow}"


class Level(Enum):
    """The three, the gravest last; a black swan is a crash too.

    EMERGENCY: a shock to one line: in one day, the whole fall its stop allows a holding, a
    tenth of a fifth of the capital. For a line of five times that is half its price, a move
    the store parks a line for: its stop and the parking are what guard such a line.
    CRASH: the market falls as it has in one episode every two or three years.
    BLACK SWAN: the market falls further than it has read at any moment of the history the
    rules are tested on. No test says what the rules do there, and to sell everything on a
    fall that was only a crash costs more than to halt on one that was more: so its numbers
    are the first round ones beyond the history's worst, and the desk stands in cash. One bad
    price must never do that: the crash watch sells only on a black swan it has read twice."""

    EMERGENCY = Definition(False, STOP_FALL, None, Response.PARK)
    CRASH = Definition(True, Decimal("0.04"), Decimal("0.12"), Response.HALT)
    BLACK_SWAN = Definition(True, Decimal("0.10"), Decimal("0.30"), Response.CASH)


@dataclass(frozen=True)
class Fall:
    """How far one line's own price has fallen in one session, each a part of one: 0.05 is 5%."""

    line: Line
    on: date  #: the session it was read in
    day: Decimal  #: below the close of the line's session before; nothing when it stands above
    high: Decimal  #: below the highest close of the line's last MONTH sessions

    def __post_init__(self) -> None:
        if not 0 <= self.day <= self.high < 1:
            raise ValueError(
                f"{self.line.symbol}: no line has fallen {self.day} in a day and {self.high}"
                " below its month's high"
            )
        if self.line.symbol == YARDSTICK.symbol and self.line != YARDSTICK:
            raise ValueError(f"{self.line} is not the yardstick as the master records it")

    @property
    def market(self) -> bool:
        """Whether this is the market's own fall: the yardstick's, whose series set the numbers."""
        return self.line == YARDSTICK

    @property
    def level(self) -> Level | None:
        """The gravest of the three this fall is, or none of them. The market's fall is a crash
        or a black swan; any other line's, however far it falls, an emergency of its own."""
        met, geared = None, self.line.leverage
        for level in Level:
            rule = level.value
            slow = rule.high is not None and self.high >= rule.high * geared
            if self.market == rule.market and (self.day >= rule.day * geared or slow):
                met = level
        return met

    def words(self) -> str:
        """The fall, which of the three it is, and what the desk does: one message."""
        line, level, fallen = self.line, self.level, _below(self.day, "its last close")
        if line.leverage > 1 and (market := _cut(self.day / line.leverage)):
            fallen += f" (its market {market:.1%}: it moves {line.leverage} times as far)"
        if self.market:
            fallen = _below(self.high, "its month's high") + f" and {fallen}"
        said = f"{line.symbol}, on {self.on}, is {fallen}"
        if level is None:
            return f"{said}: none of the three emergencies."
        rule, name = level.value, level.name.replace("_", " ")
        return f"{name}, which is {rule.words()}: {said}. The desk is to {rule.response.value}."


def measure(line: Line, bars: Sequence[Bar], newest: Five) -> Fall:
    """A line's fall as its newest five-minute bar closes: its close, never its low, for a
    print the market took back within the bar is no fall. The bar says which session is read,
    and must start within one of the line's venue. bars are the line's daily bars from the
    store, the oldest first; only those before that session are read, and they must be the
    line's last MONTH sessions, each one and no other, up to the session before: a close a day
    stale, or missing, would make one day's fall of two. The price must lie within a move the
    store believes of the last close. If any of it fails, the line is unread."""
    day, price = newest.start.date(), newest.close
    month = [bar for bar in bars if bar.day < day][-MONTH:]
    first, last = (month[0].day, month[-1].close) if month else (day, price)
    due = [d for d in venues.sessions(line.venue, first, day) if d not in line.suspended]
    whole = len(month) == MONTH and due == [*(bar.day for bar in month), day]
    believed = price.is_finite() and last / JUMP <= price <= last * JUMP
    if venues.open_at(line.venue, newest.start) is None or not whole or not believed:
        raise Unread(
            f"{line.symbol}: no fall is read from its bar of {newest.start:%Y-%m-%d %H:%M} UTC"
            f" closing at {price}: it must lie in a session of {line.venue}, after the closes of"
            f" the line's last {MONTH} sessions ({len(month)} given, the last at {last}), and"
            " within a move the store believes of the last"
        )
    closes = [bar.close for bar in month]
    below = [max(Decimal(0), 1 - price / close) for close in (closes[-1], max(closes))]
    return Fall(line, day, *below)


def alarms(falls: Iterable[Fall]) -> tuple[Fall, ...]:
    """The falls that are one of the three, the gravest first: a crash or a black swan, the
    market's, is what the desk does as a whole, and each emergency names a line of its own.
    They are one session's, and the market's fall is among them, once: a market nobody read is
    not a calm one. With no market to read (London shut, New York open) each fall's own level
    still stands, and the caller reads those and says the market is unread."""
    read, order = tuple(falls), list(Level)
    markets, days = sum(fall.market for fall in read), {fall.on for fall in read}
    if markets != 1 or len(days) != 1:
        raise Unread(
            f"{len(read)} falls hold {markets} readings of the market, {YARDSTICK.symbol}, and"
            f" {len(days)} days: there must be one of each"
        )
    grave = [(order.index(level), fall) for fall in read if (level := fall.level) is not None]
    return tuple(fall for _, fall in sorted(grave, key=lambda ranked: -ranked[0]))
