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
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

from desk.orders import Settings
from desk.store import Bar
from lab import cell, rung
from lab.cell import Cell
from lab.rung import Answer, Verdict


@dataclass(frozen=True)
class Fold:
    inside: Verdict  #: in-sample: the window before the fold, all a chooser had seen
    outside: Verdict  #: out-of-sample: the fold alone


@dataclass(frozen=True)
class Folded:
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
        return self.worst.outside.answer

    @property
    def passed(self) -> bool:
        return self.answer is Answer.PASS

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
            Cell(window.strategy, window.symbol, window.start, days[first - 1]),
            Cell(window.strategy, window.symbol, days[first], days[after - 1]),
        )
        for first, after in zip(edges, edges[1:], strict=False)
    )


def judge(window: Cell, bars: Sequence[Bar], settings: Settings, fx: Decimal, folds: int) -> Folded:
    """The window in folds, each cell run and judged by the first rung on the line's bars;
    fx is pounds per unit of the line's currency, one rate for the window."""

    def first_rung(c: Cell) -> Verdict:
        return rung.judge(cell.run(c, bars), bars, settings, fx)

    return Folded(tuple(Fold(first_rung(i), first_rung(o)) for i, o in cut(window, bars, folds)))
