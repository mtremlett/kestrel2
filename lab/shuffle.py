"""shuffle - THE LADDER'S SHUFFLE RUNG (Monte Carlo): did the rule time its line, or only ride it?

Each day a cell is shown after its first (none after its end) is kept whole, as its moves
from the close before, and SHUFFLES times the days are put in a random order and the rule run
on the history that makes, priced by the first rung (`lab/rung.py`). Every shuffle has the
line's whole rise and no order in it: a rule that earns as much there has timed nothing. The
share of a trial is the shuffles whose standard errors are its own or more, and itself, over
SHUFFLES + 1. The order is drawn from the trial's name, so a trial run again is shuffled the
same. A trial that can no longer pass is stopped there: its answer is the full run's.
"""

from __future__ import annotations

import random
from collections.abc import Sequence
from decimal import Decimal

from desk.orders import Settings
from desk.store import Bar
from lab import cell, trials
from lab.cell import Cell
from lab.reproduce import Reproduction
from lab.rung import Rates, judge

SHUFFLES = 100
SHARE = Decimal("0.05")  #: at most this share of shuffles, itself among them, does as well
MOST_AS_GOOD = int(SHARE * (SHUFFLES + 1))  #: the most as good, itself among them, that passes


def share(
    c: Cell, bars: Sequence[Bar], settings: Settings, rates: Rates, made: Sequence[Reproduction]
) -> Decimal:
    """The trial's share among its shuffles, each judged behind the rule's reproductions of its
    authors' figures; 1 for a trial of under two trades, which has no standard errors to beat."""
    own = _t(c, bars, settings, rates, made)
    if own is None:
        return Decimal(1)
    rng = random.Random(trials.name(c))  # noqa: S311 - a repeatable draw, not a secret
    shown = cell.shown(c, bars)  #: only the cell's own days are drawn: none after its end (B3)
    moves = _moves(shown)
    as_good = 1  #: the trial itself
    for _ in range(SHUFFLES):
        rng.shuffle(moves)
        got = _t(c, _history(shown, moves), settings, rates, made)
        as_good += got is not None and got >= own
        if as_good > MOST_AS_GOOD:  #: it cannot pass now: the shuffles left would only add (S3)
            break
    return Decimal(as_good) / (SHUFFLES + 1)


def said(share: Decimal) -> str:
    """The share as the rung reports it: a passing one exactly; a failing one as the count at
    which the shuffles stopped, since the rest were not run (`docs/DECISIONS.md`, S3)."""
    if share <= SHARE:
        return f"{share:.3f}"
    return f"at least {share * (SHUFFLES + 1):.0f} of {SHUFFLES + 1}"


def _t(
    c: Cell, bars: Sequence[Bar], settings: Settings, rates: Rates, made: Sequence[Reproduction]
) -> Decimal | None:
    return judge(cell.run(c, bars), bars, settings, rates, made).t


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
