"""reproduce - THE AUTHOR'S OWN RESULT: the desk's code run on the author's market over the
author's period, counted as the author counted, and set beside the figure the author printed.
It comes before a published rule is judged on the desk's market: the first rung waits for it.

The published rules (`lab/published.py`) hold the code to the rule's words on short series
worked by hand. This holds it to the author's result: the same code on the same market over
the same years should give what the book gives. Where it does not, the rule as coded, the
prices or the way of counting differ from the author's, and a verdict on the desk's own
market would be a verdict on something else. The old desk listed twenty-one published rules
and reproduced none of them, for want of the figures.

A FIGURE is the author's (or, labelled so, a replication's: SECOND HAND below), written down
before anything is run: the source, the market, the period, where the test fills an order,
each number printed, and how near the desk's must come to be called the same. How near is
fixed with the figure and never after a run.

COUNTED AS THE AUTHOR COUNTED. An author's figure is nearly always before any cost, and is
filled where the author says. The numbers made here are that arithmetic and nothing else:
they say whether the code is the author's, never what the rule would earn. What it would
earn is the first rung's to say (`lab/rung.py`), after every cost, and no number from this
module is a result of the desk's. Points gained are in the price as the bars carry it, so a
figure in points is met only on prices as the author's were: old prices scaled down for the
dividends paid since give nearly the same gains per cent, and far fewer points.

The rule is shown every bar the line has up to the period's end, so history before the
period warms it, and a trade belongs to the period it was bought in. A trade is counted once
both its fills fall on bars the rule was shown: one still held at the end is not.

NOTHING IS CALLED A REPRODUCTION THAT COULD NOT BE ONE. Refused loudly: bars that miss a
session, or hold a bar on a day that is none, from the first bar the rule is shown to the
period's end (the one calendar says which days those are); code that is not
the published rule; a period in which the rule made no trade. One number outside its
nearness and the figure is not reproduced, and each number made is given beside the author's.

THE FIRST RUNG WAITS (`settled`). A rule with an author's figure on file is given no verdict on
the desk's market until every such figure's reproduction is handed over: of the figure as it is
on file, made by the code as it now is, and the same in every number. A rule with no figure on
file is judged, and its verdict says that no author's result stands behind it. What is handed
over is `reproduce`'s own answer: the rung does not read the author's bars again.

A FIGURE GOES ON FILE only from the page that printed it, the author's or a replication's,
read at the time and never from memory, and only once the desk holds the rule as the page
tests it and the author's market over the author's period: a figure on file stops every
verdict on its rule until it is reproduced. A figure read and waiting for either is
written down, with how near is the same, in `docs/DECISIONS.md` and never in this module.

SECOND HAND, AND LABELLED SO (his ruling, 14 November 2026: no book is bought). Where an
author's table is not to be had free, the best replication somebody else has published stands
in: a figure whose `hand` is SECOND, its source saying who ran it and when. Where two such
sources of one test (the same rule, market, period and fills) print different numbers, the
range they give is the figure (`Stated.between`), and the desk's must land inside it. A
verdict carries its figures, so whose result stands behind it is read from the verdict.
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


class Hand(enum.Enum):
    """Whose test printed a figure's numbers; the words name them where a number is missed."""

    AUTHOR = "the author's"
    SECOND = "the replication's"  #: somebody else's published run of the author's rule


class Measure(enum.Enum):
    """A number an author prints of a test."""

    TRADES = "trades"
    WINNERS = "trades that gained, per cent"
    MEAN_GAIN = "mean gain a trade, per cent"
    NET_POINTS = "points gained, every trade's together"


@dataclass(frozen=True)
class Stated:
    measure: Measure
    value: Decimal  #: as printed; the middle of the range, where sources disagree
    within: Decimal  #: how far from it the desk's may lie and be the same, fixed beforehand

    @classmethod
    def between(cls, measure: Measure, low: Decimal, high: Decimal) -> Stated:
        """Sources that disagree: the same is anywhere from the least printed to the most."""
        if not (low.is_finite() and high.is_finite() and low <= high):
            raise ValueError(f"{measure.value}: no range runs from {low} to {high}")
        with localcontext(ARITHMETIC):
            return cls(measure, (low + high) / 2, (high - low) / 2)


@dataclass(frozen=True)
class Figure:
    strategy: str
    source: str  #: the author, the work, and the table or page the numbers are printed on
    line: Line  #: the author's market
    start: date  #: the author's period: the first day a buy belongs to it,
    end: date  #: and the last bar the rule is shown
    fill: Fill
    stated: tuple[Stated, ...]
    hand: Hand  #: the author's own table, or a replication standing in for it

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
        for stated in self.stated:
            if not (stated.value.is_finite() and stated.within.is_finite()):
                raise ValueError(f"{self.source}: {stated.measure.value} is stated by no number")
            if stated.within < 0:
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
    key: Key  #: the code, this module's with the rule's, and the bars that made it
    found: tuple[Found, ...]  #: each number the author stated, with the desk's beside it

    def __post_init__(self) -> None:
        if tuple(found.stated for found in self.found) != self.figure.stated:
            raise ValueError(f"{self.figure.source}: not the figure's numbers, each as stated")

    @property
    def reproduced(self) -> bool:
        return all(found.same for found in self.found)


#: The figures on file, each read from the page that printed it. None yet: those read and
#: waiting are in `docs/DECISIONS.md`, each with the market or the rule it waits for.
FIGURES: tuple[Figure, ...] = ()


def reproduce(figure: Figure, bars: Sequence[Bar]) -> Reproduction:
    """The figure's numbers as the desk's code makes them on the author's market, from the
    line's bars, oldest first, each beside the author's own."""
    published.proven(figure.strategy)
    c = Cell(figure.strategy, figure.line, figure.start, figure.end)
    record = cell.run(c, bars)
    read = cell.shown(c, bars)
    first = min(figure.start, read[0].day)
    traded = set(venues.sessions(figure.line.venue, first, figure.end))
    odd = sorted(traded ^ {bar.day for bar in read})
    if odd:
        raise ValueError(
            f"{figure.source}: {len(odd)} days of {figure.line.symbol} from {first} are a "
            f"session with no bar or a bar on no session, the first {odd[0]}: not the "
            "author's market, so no reproduction"
        )
    with localcontext(ARITHMETIC):
        fills = _fills(record.trades, read, figure.fill)
        if not fills:
            raise ValueError(f"{figure.source}: {c} made no trade to set beside the figure")
        gains = [sold / bought - 1 for bought, sold in fills]
        made = {
            Measure.TRADES: Decimal(len(gains)),
            Measure.WINNERS: Decimal(100 * sum(1 for gain in gains if gain > 0)) / len(gains),
            Measure.MEAN_GAIN: 100 * sum(gains, Decimal(0)) / len(gains),
            Measure.NET_POINTS: sum((sold - bought for bought, sold in fills), Decimal(0)),
        }
    found = tuple(Found(stated, made[stated.measure]) for stated in figure.stated)
    return Reproduction(figure, record.key.rung(__name__), found)


def _fills(
    trades: Sequence[Trade], read: Sequence[Bar], fill: Fill
) -> list[tuple[Decimal, Decimal]]:
    """Each counted trade's two prices before any cost, bought and sold, both legs filled
    where the author's test fills them."""
    at = {bar.day: n for n, bar in enumerate(read)}

    def price(day: date) -> Decimal | None:
        if fill is Fill.CLOSE:
            return read[at[day]].close
        return read[at[day] + 1].open if at[day] + 1 < len(read) else None

    fills = []
    for trade in trades:
        sold = None if trade.sold is None else price(trade.sold)
        bought = price(trade.bought)
        if bought is not None and sold is not None:
            fills.append((bought, sold))
    return fills


def settled(strategy: str, made: Sequence[Reproduction]) -> tuple[Reproduction, ...]:
    """The authors' own results that stand behind a verdict on the rule: one for each of its
    figures on file. Refused loudly while any figure waits, and for anything handed over that
    is not a reproduction of one of them by the code as it now is."""
    owed = [figure for figure in FIGURES if figure.strategy == strategy]
    for one in made:
        if one.figure not in owed:
            raise ValueError(f"{strategy}: {one.figure.source} is no figure on file for it")
        c = Cell(strategy, one.figure.line, one.figure.start, one.figure.end)
        if one.key != Key(c, cell.LOADED, one.key.data).rung(__name__):
            raise ValueError(
                f"{one.figure.source}: made over another market or period than the figure's, "
                "or by other code than this: run it again"
            )
        if not one.reproduced:
            out = "; ".join(
                f"{f.stated.measure.value}: {f.measured} against "
                f"{one.figure.hand.value} {f.stated.value}"
                for f in one.found
                if not f.same
            )
            raise ValueError(f"{one.figure.source}: not reproduced, so no verdict ({out})")
    waiting = [figure.source for figure in owed if all(one.figure != figure for one in made)]
    if waiting:
        raise ValueError(f"{strategy}: no verdict before its published result: {waiting}")
    return tuple(dict.fromkeys(made))
