"""shuffle - THE LADDER'S SHUFFLE RUNG (Monte Carlo): did the rule time its line, or only ride it?

Each day a cell is shown after its first is kept whole, as its moves from the close before,
and SHUFFLES times the days are put in a random order and the rule run on the history that
makes, priced by the first rung (`lab/rung.py`). Every shuffle has the line's whole rise and
no order in it: a rule that earns as much there has timed nothing. The share of a trial is
the shuffles whose standard errors are its own or more, and itself, over SHUFFLES + 1. The
order is drawn from the trial's name, so a trial run again is shuffled the same.
"""

from __future__ import annotations

import random
from collections.abc import Sequence
from decimal import Decimal

from desk.orders import Settings
from desk.store import Bar
from lab import cell, trials
from lab.cell import Cell
from lab.rung import Rates, judge

SHUFFLES = 100
SHARE = Decimal("0.05")  #: at most this share of shuffles, itself among them, does as well


def share(c: Cell, bars: Sequence[Bar], settings: Settings, rates: Rates) -> Decimal:
    """The trial's share among its shuffles; 1 for a trial of under two trades, which has no
    standard errors to beat."""
    own = _t(c, bars, settings, rates)
    if own is None:
        return Decimal(1)
    rng = random.Random(trials.name(c))  # noqa: S311 - a repeatable draw, not a secret
    moves = _moves(bars)
    as_good = 1  #: the trial itself
    for _ in range(SHUFFLES):
        rng.shuffle(moves)
        made = _history(bars, moves)
        got = _t(c, made, settings, rates)
        as_good += got is not None and got >= own
    return Decimal(as_good) / (SHUFFLES + 1)


def _t(c: Cell, bars: Sequence[Bar], settings: Settings, rates: Rates) -> Decimal | None:
    return judge(cell.run(c, bars), bars, settings, rates).t


def _moves(bars: Sequence[Bar]) -> list[tuple[Decimal, ...]]:
    """Each day after the first as its open, high, low and close over the close before."""
    return [
        tuple(price / before.close for price in (bar.open, bar.high, bar.low, bar.close))
        for before, bar in zip(bars, bars[1:], strict=False)
    ]


def _history(bars: Sequence[Bar], moves: Sequence[tuple[Decimal, ...]]) -> list[Bar]:
    """The first bar, then the days' dates in their place with the moves in a new order."""
    made = [bars[0]]
    for day, (o, h, low, c) in zip(bars[1:], moves, strict=True):
        close = made[-1].close
        made.append(Bar(day.day, close * o, close * h, close * low, close * c, day.volume))
    return made
