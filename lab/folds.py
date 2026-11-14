"""folds - THE LADDER'S FOLDS RUNG: a rule is believed only where it earned in every one of the
last FOLDS whole calendar years, and it is judged on the worst (`lab/ladder.py` is the spec).

A rule trades a line five to ten times a year, so a year is judged on the trades of every line
of the rule at once, pooled, and the one answer is every line's. A fold's gains are taken by
the day, every day one of its lines has a bar, summed over the lines as the market's rung marks
them (`lab/market.py`), so trades held together are not counted as bets apart. Its trades are
those bought and sold inside the year, as a cell's are (`lab/cell.py`). With MIN_TRADES pooled
or more a fold PASSES if its mean day earned after costs, FAILS at T_PASS standard errors under
nothing and is in DOUBT between; with fewer it is THIN, with none FAULT, and the worst fold
speaks, its year named. `cut` is the other way of cutting a window, in equal parts, which the
regime rung (`lab/regime.py`) keeps.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from datetime import date
from decimal import Decimal
from statistics import fmean, stdev

from desk.lines import Line
from desk.orders import Settings
from desk.store import Bar
from lab import cell, market, rung
from lab.cell import Cell
from lab.rung import Answer, Rates

FOLDS = 5


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
            Cell(window.strategy, window.symbol, window.start, days[first - 1]),
            Cell(window.strategy, window.symbol, days[first], days[after - 1]),
        )
        for first, after in zip(edges, edges[1:], strict=False)
    )


def years(end: date) -> range:
    """The last FOLDS whole calendar years up to the end, oldest first."""
    last = end.year if end >= date(end.year, 12, 31) else end.year - 1
    return range(last - FOLDS + 1, last + 1)


def judge(
    rule: str, lines: Mapping[Line, Sequence[Bar]], settings: Settings, rates: Rates, end: date
) -> tuple[Answer, str]:
    """The rule's folds rung: each year's trades pooled over the lines, the worst year's
    answer with its reason. A line with no bar in a year is left out of it."""
    folds = [_fold(rule, lines, year, settings, rates) for year in years(end)]
    answer, _, why = min(folds, key=lambda f: (f[0], f[1]))
    return answer, why


def _fold(
    rule: str, lines: Mapping[Line, Sequence[Bar]], year: int, settings: Settings, rates: Rates
) -> tuple[Answer, float, str]:
    made: dict[date, Decimal] = {}
    days: set[date] = set()
    trades = pooled = 0
    for line, bars in lines.items():
        window = Cell(rule, line, date(year, 1, 1), date(year, 12, 31))
        if not any(bar.day >= window.start for bar in cell.shown(window, bars)):
            continue
        verdict = rung.judge(cell.run(window, bars), bars, settings, rates)
        read = cell.shown(window, bars)
        for day, gain in market.daily(verdict.trades, read, line, rates).items():
            made[day] = made.get(day, Decimal(0)) + gain
        days |= {bar.day for bar in read if bar.day >= window.start}
        trades, pooled = trades + len(verdict.trades), pooled + 1
    said = f"{year}: {trades} trades pooled from {pooled} lines; {rung.MIN_TRADES} asked"
    if not trades:
        return Answer.FAULT, 0.0, f"the worst of {FOLDS} folds, {said}, none made"
    if trades < rung.MIN_TRADES:
        return Answer.THIN, 0.0, f"the worst of {FOLDS} folds, {said}"
    gains = [float(made.get(day, Decimal(0))) for day in sorted(days)]
    mean = fmean(gains)
    if not (spread := stdev(gains)):
        raise ValueError(f"{year}: {len(gains)} days all of {mean}: no spread to judge the fold by")
    t = mean / (spread / math.sqrt(len(gains)))
    answer = Answer.PASS if mean > 0 else Answer.FAIL if t <= -float(rung.T_PASS) else Answer.DOUBT
    return (
        answer,
        t,
        f"the worst of {FOLDS} folds, {said}; mean day {mean:.5f}, {t:.2f} standard errors",
    )
