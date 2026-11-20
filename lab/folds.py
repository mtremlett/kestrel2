"""folds - THE LADDER'S FOLDS RUNG: a strategy is believed only where it earned on history
that no choice of it had seen, and it is judged on the worst such stretch.

A window's bars are cut into equal parts, oldest first. The first part is in-sample only:
the history a chooser starts with. Every later part is a fold, and each fold is judged twice
by the first rung (`lab/rung.py`), after the broker's costs: out-of-sample, on the fold
alone, and in-sample, on everything in the window before it, which is all a chooser could
have known the day the fold began. The two stand side by side, fold by fold.

Each is an ordinary cell (`lab/cell.py`), so nothing crosses a boundary: the rule is shown
no bar after its cell's end, and a trade counts only where it was bought and its sale
filled inside one cell. A trade held across a boundary belongs to neither side of it.

The verdict is given on the worst fold, and it is that fold's own answer (`rung.Answer`).
Thirty trades are asked of every fold. A fold with no trade at all is worst: the history
was cut too fine for the rule to trade in each part, a fault in the test. Then a fold that
failed on enough trades; then one with too few, which is not enough evidence and never a
fail; then one that passed. Among folds of one answer, the worst is the one whose
out-of-sample trades stand the fewest standard errors above nothing, a fold with under two
trades standing lowest. The strategy passes this rung when that fold passes the first
rung, which is every fold passing it. Every fold's out-of-sample verdict is a trial the
luck rung counts (`lab/luck.py`).

THE LADDER'S OWN FOLDS are `pool`: the last YEARS whole calendar years of a window, the rule's
trades pooled over all its lines in each, and the answer taken on the worst year as the
ladder's spec writes it (`lab/ladder.py`). An author's figure on file is handed on to every
cell (`reproduced`), so a rule with one is folded like any other.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, localcontext
from typing import Generic, Protocol, TypeVar

from desk.orders import Settings
from desk.store import Bar
from desk.strategy import ARITHMETIC
from lab import cell, market, rung
from lab.cell import Cell
from lab.reproduce import Reproduction
from lab.rung import Answer, Rates, Verdict


class Judged(Protocol):
    """What a fold's side must show: the t and the answer the worst fold is chosen by."""

    @property
    def t(self) -> Decimal | None:
        """The mean gain in standard errors; None under two trades."""

    @property
    def answer(self) -> Answer:
        """The first rung's answer."""


J = TypeVar("J", bound=Judged)


@dataclass(frozen=True)
class Fold(Generic[J]):
    """One fold, its two sides side by side."""

    inside: J  #: in-sample: the history before the fold
    outside: J  #: out-of-sample: the fold alone


@dataclass(frozen=True)
class Walked(Generic[J]):
    """The folds of one window, and the one answer on the worst."""

    folds: tuple[Fold[J], ...]  #: oldest first

    def __post_init__(self) -> None:
        if not self.folds:
            raise ValueError("no folds: there is no worst fold to judge on")

    @property
    def worst(self) -> Fold[J]:
        """The fold judged on; of two equally bad, the older."""
        return min(self.folds, key=lambda f: rung.standing(f.outside.answer, f.outside.t))

    @property
    def answer(self) -> Answer:
        """The worst fold's out-of-sample answer: the rung's."""
        return self.worst.outside.answer

    @property
    def passed(self) -> bool:
        """Whether every fold passed."""
        return self.answer is Answer.PASS


YEARS = 5  #: the last whole calendar years of a window are its folds (M6)


@dataclass(frozen=True)
class Folded(Walked[Verdict]):
    """The first rung's folds of a window; each out-of-sample verdict is a trial."""

    @property
    def trials(self) -> tuple[Verdict, ...]:
        """Every fold's out-of-sample verdict: the trials this strategy cost."""
        return tuple(fold.outside for fold in self.folds)


def cut(window: Cell, bars: Sequence[Bar], folds: int) -> tuple[tuple[Cell, Cell], ...]:
    """Each fold's two cells, in-sample then out-of-sample, oldest fold first: the window's
    bars in folds + 1 equal parts, a fold being each part but the first."""
    days = [bar.day for bar in cell.shown(window, bars) if bar.day >= window.start]
    parts = folds + 1
    if folds < 1 or len(days) < parts:
        raise ValueError(
            f"{window.strategy} on {window.symbol}, {window.start} to {window.end}: "
            f"{len(days)} bars cannot be cut into {folds} folds and the part before them"
        )
    edges = [n * len(days) // parts for n in range(1, parts + 1)]
    return tuple(
        (
            Cell(window.strategy, window.line, window.start, days[first - 1]),
            Cell(window.strategy, window.line, days[first], days[after - 1]),
        )
        for first, after in zip(edges, edges[1:], strict=False)
    )


def judge(
    window: Cell,
    bars: Sequence[Bar],
    settings: Settings,
    rates: Rates,
    folds: int,
    reproduced: Sequence[Reproduction] = (),
) -> Folded:
    """The window in folds, each cell run and judged by the first rung on the line's bars;
    each fill at its own day's rate of exchange."""

    def first_rung(c: Cell) -> Verdict:
        return rung.judge(cell.run(c, bars), bars, settings, rates, reproduced)

    return Folded(tuple(Fold(first_rung(i), first_rung(o)) for i, o in cut(window, bars, folds)))


@dataclass(frozen=True)
class Year:
    """One calendar year, the rule's trades pooled over its lines: bought and sold inside it."""

    year: int
    lines: int  #: the lines pooled: those with a bar in the year
    trades: int  #: judged trades, all lines
    t: Decimal | None  #: the mean day in standard errors; None under two days
    before: Decimal | None  #: the same on the history before the year, in-sample
    answer: Answer


@dataclass(frozen=True)
class Pooled:
    """The rule's years, pooled over its lines, and the one answer on the worst of them."""

    years: tuple[Year, ...]  #: oldest first

    @property
    def worst(self) -> Year:
        """The year judged on; of two equally bad, the older."""
        return min(self.years, key=lambda y: rung.standing(y.answer, y.t))

    @property
    def answer(self) -> Answer:
        """The worst year's answer: the rule's, on every line."""
        return self.worst.answer

    @property
    def reason(self) -> str:
        """The worst year named, with its pooled figures and the history before it."""
        w = self.worst
        return (
            f"the worst of {len(self.years)} yearly folds, {w.year}: {w.trades} trades pooled "
            f"over {w.lines} lines, their mean day {_t(w.t)} standard errors from nothing; "
            f"on the history before it, {_t(w.before)}"
        )


def _t(t: Decimal | None) -> str:
    return "n/a" if t is None else f"{t:.2f}"


def pool(
    cells: Sequence[tuple[Cell, Sequence[Bar]]],
    settings: Settings,
    rates: Rates,
    count: int = YEARS,
    reproduced: Sequence[Reproduction] = (),
) -> Pooled:
    """One rule's whole-window cells, one a line with its bars (the lines that wait already
    left out), walked forward over the last `count` whole calendar years before the latest
    line's end. Each line is folded on its own window: it joins a year only if its end is not
    before that year's close. In each year every line's trades bought and sold inside it are
    pooled, and its days summed over the lines as the market rung marks them, so trades held
    together are not bets apart. With 30 judged trades or more a year passes if its mean day
    earned after costs, fails at 2 standard errors under nothing and is in doubt between;
    fewer is THIN, none a FAULT."""
    if len({c.strategy for c, _ in cells}) != 1:
        raise ValueError("pooled cells must be one rule's")
    last = max(
        c.end.year if c.end >= date(c.end.year, 12, 31) else c.end.year - 1 for c, _ in cells
    )
    first = last - count + 1
    if count < 1 or min(c.start for c, _ in cells) > date(first, 1, 1):
        raise ValueError(f"{cells[0][0].strategy}: no {count} whole years of history to fold")

    def year(y: int) -> Year:
        inside = _stretch(cells, None, date(y - 1, 12, 31), settings, rates, reproduced)
        out = _stretch(cells, date(y, 1, 1), date(y, 12, 31), settings, rates, reproduced)
        return Year(y, out[0], out[1], out[2], inside[2], _answer(out[1], out[2], out[3]))

    return Pooled(tuple(year(y) for y in range(first, last + 1)))


def _answer(trades: int, t: Decimal | None, mean: Decimal) -> Answer:
    if not trades:
        return Answer.FAULT
    if t is None or trades < rung.MIN_TRADES:
        return Answer.THIN
    return Answer.PASS if mean > 0 else rung.band(t)


def _stretch(
    cells: Sequence[tuple[Cell, Sequence[Bar]]],
    start: date | None,
    end: date,
    settings: Settings,
    rates: Rates,
    reproduced: Sequence[Reproduction],
) -> tuple[int, int, Decimal | None, Decimal]:
    """Lines pooled, judged trades, the mean day in standard errors, and the mean day, over
    [start (each cell's own where None), end] with each line cut as an ordinary cell."""
    gains: defaultdict[date, Decimal] = defaultdict(Decimal)
    lines = trades = 0
    for c, bars in cells:
        begin = c.start if start is None else max(start, c.start)
        stop = min(end, c.end)
        if (start is not None and stop < end) or begin > stop:
            continue
        if not any(begin <= bar.day <= stop for bar in bars):
            continue
        part = Cell(c.strategy, c.line, begin, stop)
        verdict = rung.judge(cell.run(part, bars), bars, settings, rates, reproduced)
        lines, trades = lines + 1, trades + len(verdict.trades)
        for bar in cell.shown(part, bars):
            if bar.day >= begin:
                gains[bar.day] += Decimal(0)
        for day, made in market.daily(
            verdict.trades, cell.shown(part, bars), c.line, rates
        ).items():
            gains[day] += made
    if not trades:
        return lines, 0, None, Decimal(0)
    with localcontext(ARITHMETIC):
        days = list(gains.values())
        return lines, trades, rung.standard_errors(days), sum(days, Decimal(0)) / len(days)
