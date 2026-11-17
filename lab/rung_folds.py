"""rung_folds - THE SHAPE OF A WALK-FORWARD FOLD (rung 10): one fold with its two sides side by
side, and the walk of them with the one answer on the worst. The cutting and the judging are
`lab/folds.py`'s (`judge` for one cell, `pool` for the ladder's whole years); this holds only
what they share.

The answer is the WORST fold's: a fold with no trade is a FAULT (cut too fine, the test's fault,
LAD-09), then a FAIL, then THIN (too few trades, never a fail, LAD-03), then a PASS. Of equal
answers the worst is the lowest t. The rung passes when every fold passes. Noise therefore passes
at the t-table's tail to the power of the folds (LAD-08): taking the best fold, or the pooled
folds, passes it far more often.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Generic, Protocol, TypeVar

from lab import rung
from lab.rung import Answer


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
