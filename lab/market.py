"""market - THE MARKET'S RUNG: is the edge the strategy's own, or only the market's, taken
with the risk of holding it (BIC-01)?

A rule that is in a rising market half its days earns half the market's rise and has found
nothing: the same money simply held would have earned it with no rule at all. The first rung
(`lab/rung.py`) cannot tell that from an edge, since both earn after costs. This rung can.

EACH DAY OF THE WINDOW is a pair: what the strategy made that day, and what the market did.
The strategy's day is its position marked at that day's close: on the day a trade's buy fills,
its shares at the close against the pounds they took; each day held, close on close; on the
day its sale fills, the pounds received, less every cost of both legs, against the close
before. Each is a part of the pounds the trade took, so a trade's days sum to the first
rung's own gain on it, and nothing is priced again here. A day it holds nothing makes
nothing. The market's day is its close on the close before. Both are in pounds, each day at
its own rate of exchange (`rung.rate`), so a dollar line carries the currency as its market
does.

SET BESIDE TWO THINGS SIMPLY HELD, each in its turn: its own line, and the market. A rule on
a line that climbs of itself, whatever the market does, has earned the line's climb and not
a penny by its rule; the market alone would not show that, and the line alone would not show
a line that is only the market geared up. The strategy must stand against both.

THE RISK IT TOOK IS MEASURED, never assumed: the least-squares line through the days gives
the strategy's beta, how much of the other's move it carried on an average day, in and out.
A line's stated leverage is not that number (five times the market for a fifth of the days is
the market's own risk), so a leveraged line needs no rule of its own. What is left of a
day's gain once beta times the other's is taken away is the EXCESS.

JUDGED BY ITS INTERVAL, NOT ITS SIGN. The rung passes a strategy whose mean excess a day is
at least `rung.T_PASS` standard errors above nothing, the first rung's own bar, against the
line and against the market: the whole of each confidence interval above nothing, not merely
a figure that came out positive. A rule that times its line well is in for the rises and out
for the falls: its excess is real, and it passes.

FAILING FAIRLY (LAD-06). Where the first rung found too few trades, or none, this rung has no
more to judge and gives the first rung's answer, measuring nothing. A trade the first rung
could not judge (still held at the window's end, or sold on its last day) is not counted, so
neither are its days: the days counted end on the day it was bought.

WHICH MARKET is the caller's to say, and nothing calls this rung yet (docs/STATUS.md). It
must trade on the line's own venue: closes hours apart, or sessions one has and the other
has not, understate the risk taken. Refused loudly: such a market; a counted day the market
has no bar on, or none the day before; bars that did not make the verdict; a market or a
line that never moved; days that leave no spread to judge by.
"""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, localcontext
from statistics import fmean

from desk.lines import Line
from desk.store import Bar
from desk.strategy import ARITHMETIC
from lab import cell, rung
from lab.cell import Cell
from lab.rung import Answer, Priced, Rates, Verdict


@dataclass(frozen=True)
class Fit:
    beta: float  #: the part of the other's move the strategy carried, a day
    excess: float  #: the mean of a day's gain beyond beta times the other's
    t: float  #: the excess in its standard errors


@dataclass(frozen=True)
class Against:
    verdict: Verdict  #: the first rung's, whose trades these are
    market: Line
    days: int  #: the days counted; none where the first rung left nothing to judge
    line: Fit | None  #: against its own line simply held
    wide: Fit | None  #: against the market
    answer: Answer  #: this rung's own: PASS or FAIL, or the first rung's THIN or FAULT


def judge(
    verdict: Verdict, bars: Sequence[Bar], market: Line, held: Sequence[Bar], rates: Rates
) -> Against:
    """The first rung's verdict on a whole window judged against its line simply held and
    against the market: the line's bars that made it, and the market's own, oldest first."""
    c = verdict.key.cell
    if market.venue != c.line.venue:
        raise ValueError(
            f"{market.symbol} trades on {market.venue}, {c.symbol} on {c.line.venue}: not the "
            "market it took, day for day"
        )
    if cell.key(c, bars) != verdict.key:
        raise ValueError(f"{c}: these bars or this code did not make the verdict")
    if verdict.answer in (Answer.FAULT, Answer.THIN):
        return Against(verdict, market, 0, None, None, verdict.answer)
    read = cell.shown(c, bars)
    judged = {priced.trade for priced in verdict.trades}
    unjudged = [trade.bought for trade in cell.run(c, bars).trades if trade not in judged]
    last = min(unjudged, default=c.end)
    days = [bar.day for bar in read if bar.day <= last]
    #: the first day counted is the window's first with a close before it to move from
    days = days[max(1, sum(1 for day in days if day < c.start)) - 1 :]
    with localcontext(ARITHMETIC):
        made = daily(verdict.trades, read, c.line, rates)
        own = [float(made.get(day, Decimal(0))) for day in days[1:]]
        line = fit(own, _moves(c, c.line, read, rates, days))
        wide = fit(own, _moves(c, market, held, rates, days))
    passed = min(line.t, wide.t) >= rung.T_PASS
    return Against(verdict, market, len(own), line, wide, Answer.PASS if passed else Answer.FAIL)


def _moves(
    c: Cell, line: Line, bars: Sequence[Bar], rates: Rates, days: Sequence[date]
) -> list[float]:
    """The line's move on each of the days after the first: its close on the close of the
    day before, in pounds, each at its own day's rate."""
    marks = {bar.day: bar.close for bar in bars}
    lost = [day for day in days if day not in marks]
    if lost:
        raise ValueError(f"{c}: {line.symbol} has no bar on {lost[0]} to set beside it")
    closes = [marks[day] * rung.rate(line, rates, day) for day in days]
    return [float(now / before - 1) for before, now in zip(closes, closes[1:], strict=False)]


def daily(
    trades: Sequence[Priced], read: Sequence[Bar], line: Line, rates: Rates
) -> dict[date, Decimal]:
    """What the trades made each day one was held, as a part of the pounds it took: marked
    at each close at that day's rate, every cost of both legs counted on the day it is sold."""
    at = {bar.day: n for n, bar in enumerate(read)}
    made: defaultdict[date, Decimal] = defaultdict(Decimal)
    with localcontext(ARITHMETIC):
        for priced in trades:
            (first, last), worth = priced.held, priced.paid
            for bar in read[at[first] : at[last]]:
                now = priced.shares * bar.close * rung.rate(line, rates, bar.day)
                made[bar.day] += (now - worth) / priced.paid
                worth = now
            made[last] += (priced.received - priced.costs.total - worth) / priced.paid
    return dict(made)


def fit(own: Sequence[float], market: Sequence[float]) -> Fit:
    """The least-squares line of the strategy's days on the market's: its slope the beta, its
    height the excess, and the excess in its standard errors."""
    n, mean, level = len(own), fmean(own), fmean(market)
    swing = sum((m - level) ** 2 for m in market)
    if not swing:
        raise ValueError(f"{n} days of a market that never moved: no risk to set the edge against")
    beta = sum((m - level) * (o - mean) for o, m in zip(own, market, strict=True)) / swing
    excess = mean - beta * level
    left = sum((o - excess - beta * m) ** 2 for o, m in zip(own, market, strict=True)) / (n - 2)
    if not left:
        raise ValueError(f"{n} days all on one line: no spread to judge the excess by")
    return Fit(beta, excess, excess / math.sqrt(left * (1 / n + level**2 / swing)))
