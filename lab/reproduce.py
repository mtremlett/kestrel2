"""reproduce - THE AUTHOR'S OWN RESULT: before a published rule is judged on the desk's
market, the desk's code is run on the author's market over the author's period, counted as
the author counted, and set beside the figure the author printed.

The published rules (`lab/published.py`) hold the code to the rule's words on short series
worked by hand. This holds it to the author's result: the same code on the same market over
the same years should give what the book gives. Where it does not, the rule as coded, the
prices or the way of counting differ from the author's, and a verdict on the desk's own
market would be a verdict on something else. The old desk listed twenty-one published rules
and reproduced none of them, for want of the figures.

A FIGURE is the author's, written down before anything is run: the source, the market, the
period, where the author's test fills an order, each number printed, and how near the desk's
must come to be called the same. How near is fixed with the figure and never after a run.

COUNTED AS THE AUTHOR COUNTED. An author's figure is nearly always before any cost, and is
filled where the author says. The numbers made here are that arithmetic and nothing else:
they say whether the code is the author's, never what the rule would earn. What it would
earn is the first rung's to say (`lab/rung.py`), after every cost, and no number from this
module is a result of the desk's.

The rule is shown every bar the line has up to the period's end, so history before the
period warms it, and a trade belongs to the period it was bought in. A trade is counted once
both its fills fall on bars the rule was shown: one still held at the end is not.

NOTHING IS CALLED A REPRODUCTION THAT COULD NOT BE ONE. Refused loudly: bars that miss a
session of the author's period (the one calendar says which days those are); code that is not
the published rule; a period in which the rule made no trade. One number outside its
nearness and the figure is not reproduced, and each number made is given beside the author's.

NO FIGURE IS ON FILE YET. None of the five rules' authors' figures has been read from its
source by this desk, and the desk's bars begin in 2010, after the periods the books tested.
A figure is entered in FIGURES only from the publication itself, never from memory or from a
second hand.
"""

from __future__ import annotations

import enum
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, localcontext

from desk import venues
from desk.lines import Line
from desk.store import Bar
from desk.strategy import ARITHMETIC
from lab import cell, published
from lab.cell import Cell, Key, Trade


class Fill(enum.Enum):
    """Where the author's test fills an order the rule gives after a close."""

    CLOSE = 0  #: at that close
    NEXT_OPEN = 1  #: at the next bar's open, as the desk itself fills


class Measure(enum.Enum):
    """A number an author prints of a test."""

    TRADES = "trades"
    WINNERS = "trades that gained, per cent"
    MEAN_GAIN = "mean gain a trade, per cent"


@dataclass(frozen=True)
class Stated:
    measure: Measure
    value: Decimal  #: as the author printed it
    within: Decimal  #: how far from it the desk's may lie and be the same, fixed beforehand


@dataclass(frozen=True)
class Figure:
    strategy: str
    source: str  #: the author, the work, and the table or page the numbers are printed on
    line: Line  #: the author's market
    start: date  #: the author's period: the first day a buy belongs to it,
    end: date  #: and the last bar the rule is shown
    fill: Fill
    stated: tuple[Stated, ...]

    def __post_init__(self) -> None:
        if self.strategy not in published.PUBLISHED:
            raise ValueError(f"{self.strategy}: no published rule on file for a figure to be of")
        if not self.source.strip():
            raise ValueError(f"{self.strategy}: a figure with no source is nobody's result")
        measures = [stated.measure for stated in self.stated]
        if not measures:
            raise ValueError(f"{self.source}: a figure that states no number")
        if len(set(measures)) != len(measures):
            raise ValueError(f"{self.source}: a figure that states one number twice")
        if any(stated.within < 0 for stated in self.stated):
            raise ValueError(f"{self.source}: nothing lies nearer than nothing to a number")


@dataclass(frozen=True)
class Found:
    stated: Stated
    measured: Decimal  #: the desk's code, counted as the author counted

    @property
    def same(self) -> bool:
        return abs(self.measured - self.stated.value) <= self.stated.within


@dataclass(frozen=True)
class Reproduction:
    figure: Figure
    key: Key  #: the code and the bars that made it
    found: tuple[Found, ...]  #: each number the author stated, with the desk's beside it

    @property
    def reproduced(self) -> bool:
        return all(found.same for found in self.found)


#: The authors' figures on file, each read from its publication. None yet (see above).
FIGURES: tuple[Figure, ...] = ()


def reproduce(figure: Figure, bars: Sequence[Bar]) -> Reproduction:
    """The figure's numbers as the desk's code makes them on the author's market, from the
    line's bars, oldest first, each beside the author's own."""
    published.proven(figure.strategy)
    days = {bar.day for bar in bars}
    period = venues.sessions(figure.line.venue, figure.start, figure.end)
    missing = [day for day in period if day not in days]
    if missing:
        raise ValueError(
            f"{figure.source}: {len(missing)} of the author's sessions on {figure.line.symbol} "
            f"have no bar, the first {missing[0]}: not the author's market, so no reproduction"
        )
    c = Cell(figure.strategy, figure.line, figure.start, figure.end)
    record = cell.run(c, bars)
    with localcontext(ARITHMETIC):
        gains = _gains(record.trades, cell.shown(c, bars), figure.fill)
        if not gains:
            raise ValueError(f"{figure.source}: {c} made no trade to set beside the figure")
        made = {
            Measure.TRADES: Decimal(len(gains)),
            Measure.WINNERS: Decimal(100 * sum(1 for gain in gains if gain > 0)) / len(gains),
            Measure.MEAN_GAIN: 100 * sum(gains, Decimal(0)) / len(gains),
        }
    found = tuple(Found(stated, made[stated.measure]) for stated in figure.stated)
    return Reproduction(figure, record.key, found)


def _gains(trades: Sequence[Trade], read: Sequence[Bar], fill: Fill) -> list[Decimal]:
    """Each counted trade's gain before any cost, as a fraction of its buying price, both
    legs filled where the author's test fills them."""
    at = {bar.day: n for n, bar in enumerate(read)}

    def price(day: date) -> Decimal | None:
        if fill is Fill.CLOSE:
            return read[at[day]].close
        return read[at[day] + 1].open if at[day] + 1 < len(read) else None

    gains = []
    for trade in trades:
        sold = None if trade.sold is None else price(trade.sold)
        bought = price(trade.bought)
        if bought is not None and sold is not None:
            gains.append(sold / bought - 1)
    return gains
