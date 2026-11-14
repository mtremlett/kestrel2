"""bets - THE BOOK'S CONCENTRATION: how many independent bets it holds, and which cluster of
lines its profit came from (BIC-02).

Five holdings are not five bets. A fund of the S&P 500, a fund of the Nasdaq and a product
that makes five times the Nasdaq's day rise and fall as one market, and a book of them has
made one bet three times: its profit is one piece of luck or one piece of skill, not three.
The old desk counted names. This counts what moves apart.

HOW LINES MOVE TOGETHER IS MEASURED, never taken from a name, a sector or a stated leverage.
Each line's close is put in pounds at its own day's rate (`rung.rate`), on the days every
line given has a bar, and the latest YEAR of its moves is read and no older: lines that once
moved as one and no longer do are two bets now. A move is across TWO of those days, because
New York closes hours after London: most of a day's move in one market reaches the other
market's line a day late, and day against day two lines of one market look half strangers.

A CLUSTER is lines joined by a correlation of LINK or more, either way, directly or through
a chain of others. Either way, because a line and its inverse are one bet seen from two
sides. A chain joins, so the split errs towards fewer and larger clusters, on purpose: a
book called more spread than it is was the old desk's mistake. Each cluster is given with
the pounds its lines made, after every cost, the largest gain first, and `top` is the part
of the whole profit the first of them made: more than the whole, where the others lost.

THE NUMBER OF INDEPENDENT BETS on a day is read from the pounds held of each line at its
end, each counted by how far it moves: with every holding's moves in pounds set beside every
other's (their co-variances), the square of the sum of the holdings' own, over the sum of
the squares of them all. Five equal holdings that share nothing are five; five of one market
are one; a market held beside itself geared, or beside its hedge, is one; a large holding
among crumbs is hardly more than one. The book's number is the mean over the days given,
with the fewest beside it. Read from a year of moves and not from the truth, it comes out a
little under: five holdings that truly share nothing measure about 4.8.

A READING AFTER THE FACT, NOT A FORECAST. Every day held is weighed by the one year's moves,
those after it among them, so each must lie in the year read, which ends with the bars
given: the caller ends them with the days judged, and a line whose bars stop while its venue
went on trading is refused, never left to end the year early. Nothing trades on this number.

MEASURED AND SHOWN, NOT JUDGED. Nothing here passes or fails a book: what concentration the
A-GATE allows is the operator's to rule, and nothing calls this yet.

Refused loudly: no lines; fewer than FEWEST moves on days all the lines share; a line that
never moved, or with a bar owed; a line held that has no bars here, and a line with bars and
no profit stated or a profit and no bars; a profit that is no number; a book that held
nothing; a day of it outside the year read; pounds held that are no number, below nothing,
or nothing at all that day.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

import numpy as np
from numpy.typing import NDArray

from desk import venues
from desk.lines import Line
from desk.store import Bar
from lab import rung
from lab.rung import Rates

#: Fixed before any result. Two lines whose moves correlate by a half or more are one
#: cluster; a year of moves is read, and under half a year is too few to call lines apart.
LINK, YEAR, FEWEST = 0.5, 250, 120
Floats = NDArray[np.float64]


@dataclass(frozen=True)
class Cluster:
    lines: tuple[Line, ...]  #: lines that move together
    profit: Decimal  #: pounds they made between them, after every cost


@dataclass(frozen=True)
class Concentration:
    moves: int  #: the two-day moves the lines were set beside each other on
    bets: float  #: the book's independent bets, the mean over the days it held anything
    fewest: float  #: and on the day it held the fewest
    clusters: tuple[Cluster, ...]  #: every line given, in its cluster, the largest gain first

    @property
    def top(self) -> Decimal | None:
        """The part of the whole profit its best cluster made, above one where the others
        lost between them; None when the book made no gain to share out."""
        whole = sum((cluster.profit for cluster in self.clusters), Decimal(0))
        return self.clusters[0].profit / whole if whole > 0 else None


def measure(
    bars: Mapping[Line, Sequence[Bar]],
    rates: Rates,
    held: Mapping[date, Mapping[Line, Decimal]],
    profit: Mapping[Line, Decimal],
) -> Concentration:
    """The book's concentration: from the bars of every line it held or made anything on, the
    pounds held of each at the end of each day it held anything, and the pounds each of those
    lines made over the days judged, after every cost (nothing, said so, where it made none)."""
    lines = set(bars)
    odd = {line for day in held.values() for line in day} - lines | lines ^ set(profit)
    odd |= {line for line, made in profit.items() if not made.is_finite()}
    if odd:
        raise ValueError(
            f"{sorted(line.symbol for line in odd)}: held with no bars given, of bars and "
            "profit only the one, or a profit that is no number"
        )
    (first, end), moves, co = together(bars, rates)
    if not held:
        raise ValueError("a book that held nothing has no bets to count")
    out = sorted(day for day in held if not first <= day <= end)
    if out:
        raise ValueError(f"held on {out[0]}, outside the year of moves read, {first} to {end}")
    counts = [count([float(day.get(line, 0)) for line in bars], co) for day in held.values()]
    clusters = split(tuple(bars), co, profit)
    return Concentration(moves, float(np.mean(counts)), min(counts), clusters)


def together(
    bars: Mapping[Line, Sequence[Bar]], rates: Rates
) -> tuple[tuple[date, date], int, Floats]:
    """The lines' latest year of two-day moves in pounds, on the days all of them have a bar:
    the first of those days with the last day of any bar, how many moves were read, and their
    co-variances, line by line."""
    if not bars:
        raise ValueError("no lines given, so nothing moves together or apart")
    shared = set.intersection(*({bar.day for bar in own} for own in bars.values()))
    days = sorted(shared)[-(YEAR + 2) :]
    if len(days) - 2 < FEWEST:
        raise ValueError(
            f"{max(len(days) - 2, 0)} two-day moves on the days {len(bars)} lines share, "
            f"fewer than {FEWEST}: too few to call any of them apart"
        )
    lasts = {line: max(bar.day for bar in own) for line, own in bars.items()}
    end = max(lasts.values())
    owed = sorted(
        line.symbol
        for line, last in lasts.items()
        if set(venues.sessions(line.venue, last + timedelta(1), end)) - line.suspended
    )
    if owed:
        raise ValueError(f"{owed}: bars owed up to {end}, their venues trading after their last")
    rows = []
    for line, own in bars.items():
        close = {bar.day: bar.close for bar in own}
        pounds = [float(close[day] * rung.rate(line, rates, day)) for day in days]
        rows.append([now / before - 1 for before, now in zip(pounds, pounds[2:], strict=False)])
    moves = np.array(rows, dtype=np.float64)
    co = np.atleast_2d(np.cov(moves))
    still = [line.symbol for line, own in zip(bars, co.diagonal(), strict=True) if not own > 0]
    if still:
        raise ValueError(f"{', '.join(still)} never moved: nothing to set beside the others")
    return (days[0], end), moves.shape[1], co


def count(pounds: Sequence[float], co: Floats) -> float:
    """The independent bets in a day's holdings: the pounds held of each line, in the order
    of the lines whose moves' co-variances are given."""
    held = np.array(pounds, dtype=np.float64)
    if not (np.isfinite(held).all() and (held >= 0).all() and held.any()):
        raise ValueError(
            f"pounds held of {list(pounds)}: each a number, none below nothing, " "and some above"
        )
    risk = co * np.outer(held, held)
    return float(risk.trace() ** 2 / (risk**2).sum())


def split(lines: Sequence[Line], co: Floats, profit: Mapping[Line, Decimal]) -> tuple[Cluster, ...]:
    """The lines in their clusters, each with the profit its lines made, the largest first."""
    spread = np.sqrt(co.diagonal())
    linked = np.abs(co / np.outer(spread, spread)) >= LINK
    mark = list(range(len(lines)))
    for a in range(len(lines)):
        for b in range(a):
            if linked[a, b]:
                mark = [mark[a] if m == mark[b] else m for m in mark]
    clusters = [
        Cluster(
            members := tuple(line for line, m in zip(lines, mark, strict=True) if m == own),
            sum((profit[line] for line in members), Decimal(0)),
        )
        for own in sorted(set(mark))
    ]
    return tuple(sorted(clusters, key=lambda cluster: cluster.profit, reverse=True))
