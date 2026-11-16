"""rung_folds - THE LADDER'S WALK-FORWARD FOLDS (rung 10), alone: is the rule's worst stretch of
history, one no choice of it had seen, still a stretch it earned in after costs?

A window of days is cut into FOLDS + 1 equal calendar parts, oldest first (Pardo, The Evaluation
and Optimization of Trading Strategies, 2008, ch. 14: the test windows follow the data the rule
was chosen on, in time order). The first part is in-sample only; every later part is a fold. A
trade is kept by the part holding both its buy and its sale: one held across a cut belongs to
neither side. Each fold is read twice, on the gains after costs of the trades in it (out of
sample) and of those before it (in sample, all a chooser had seen), both by the first rung's own
rule (`lab/rung.py`): MIN_TRADES trades and T_PASS standard errors above nothing.

The answer is the WORST fold's: a fold with no trade is a FAULT (cut too fine, the test's fault,
LAD-09), then a FAIL, then THIN (too few trades, never a fail, LAD-03), then a PASS. Of equal
answers the worst is the lowest t. The rung passes when every fold passes. Noise therefore passes
at the t-table's tail to the power of the folds (LAD-08): taking the best fold, or the pooled
folds, passes it far more often, and is the defect the tests keep as a case that must fail.
The folds of the ladder's own set (whole years, lines pooled) are `lab/folds.py`'s `pool`.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, localcontext

from desk.strategy import ARITHMETIC
from lab import rung
from lab.rung import Answer

#: One trade after costs: the day it was bought, the day it was sold, its gain.
Gain = tuple[date, date, Decimal]


@dataclass(frozen=True)
class Stretch:
    """The gains of the trades in one stretch of days, judged by the first rung's rule."""

    trades: int
    t: Decimal | None  #: the mean gain in standard errors; None under two trades
    answer: Answer


@dataclass(frozen=True)
class Fold:
    """One fold, its two stretches side by side."""

    inside: Stretch  #: in-sample: the history before the fold
    outside: Stretch  #: out-of-sample: the fold alone


@dataclass(frozen=True)
class Walked:
    """The folds of one window, and the one answer on the worst."""

    folds: tuple[Fold, ...]  #: oldest first

    def __post_init__(self) -> None:
        if not self.folds:
            raise ValueError("no folds: there is no worst fold to judge on")

    @property
    def worst(self) -> Fold:
        """The fold judged on; of two equally bad, the older."""
        return min(
            self.folds,
            key=lambda f: (f.outside.answer, f.outside.t is not None, f.outside.t or 0),
        )

    @property
    def answer(self) -> Answer:
        """The worst fold's out-of-sample answer: the rung's."""
        return self.worst.outside.answer

    @property
    def passed(self) -> bool:
        """Whether every fold passed."""
        return self.answer is Answer.PASS


def stretch(gains: Sequence[Decimal]) -> Stretch:
    """The first rung's rule on gains: none a FAULT, under MIN_TRADES THIN, else PASS at T_PASS
    standard errors above nothing and FAIL below; gains with no spread are refused."""
    with localcontext(ARITHMETIC):
        t = rung.standard_errors(gains)
    if not gains:
        return Stretch(0, None, Answer.FAULT)
    if t is None or len(gains) < rung.MIN_TRADES:
        return Stretch(len(gains), t, Answer.THIN)
    return Stretch(len(gains), t, Answer.PASS if t >= rung.T_PASS else Answer.FAIL)


def judge(trades: Sequence[Gain], start: date, end: date, folds: int) -> Walked:
    """The trades of the window [start, end] walked forward in `folds` folds."""
    parts, days = folds + 1, (end - start).days + 1
    if folds < 1 or days < parts:
        raise ValueError(f"{start} to {end}: {days} days cannot be cut into {folds} folds")
    edges = [start + (end - start + date.resolution) * n // parts for n in range(parts)] + [
        end + date.resolution
    ]
    return Walked(
        tuple(
            Fold(
                stretch(_within(trades, start, edges[n])),
                stretch(_within(trades, edges[n], edges[n + 1])),
            )
            for n in range(1, parts)
        )
    )


def _within(trades: Sequence[Gain], first: date, after: date) -> list[Decimal]:
    """The gains of trades bought and sold in [first, after)."""
    return [g for bought, sold, g in trades if first <= bought and sold < after]
