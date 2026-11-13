"""plateau - PLATEAUS OVER PEAKS: of a rule's many settings, the one promoted is the centre
of a plateau, never a lone peak (canon B6).

Try a rule at many settings and the best score among them is the one luck helped most. A
real edge does not care whether a breakout looks back 20 days or 22: it shows as a stretch of
neighbouring settings that all earn, a plateau. A setting that earns while the settings beside
it do not is a peak, and a peak is the shape luck makes. So the setting promoted is never
picked for the best score: it is the setting deepest inside a plateau.

THE GRID AND THE SURFACE. The grid is declared first: each parameter's values, lowest first.
A setting is one value of each, and the surface holds the first rung's verdict
(`lab/rung.py`) at each setting tried, every one a cell of its own on one line, window, code
and bars. A setting of the grid with no verdict was never tried, and a failure left off the
surface is that: leaving it out cannot draw its neighbours together. What this module cannot
see is the caller's to keep: that the grid was written down before any result; that the
window is in-sample, a setting being chosen on history only and judged afterwards by the
folds rung (`lab/folds.py`); and that every setting of the grid is entered as a trial the
luck rung counts (`lab/trials.py`), the centre's neighbours as much as the centre.

THE DEPTH. One step from a setting is every setting whose parameters are each the same value
or the next one on the grid, above or below: eight neighbours for two parameters, the corners
with the sides. A setting's depth is the steps from it to the nearest setting that did not
pass the first rung or was never tried. One that failed has depth nothing; a lone peak has
depth 1, and so has any setting on the grid's own edge, where the trying ended and nothing
is known of the other side: the best on a slope still rising is not a plateau, and a
parameter is never promoted at the end of its grid. A plateau begins at DEPTH: the setting
and every setting one step from it tried, and passed.

THE CENTRE. The setting chosen is the deepest, however it scored against a shallower one. Of
two as deep, the one whose worst score among itself and the tried settings beside it is the
better, a setting with no score standing lowest; then the first in the grid's order. It is
promoted only at DEPTH or deeper: with no plateau the deepest is still shown, and it has not
passed.

WHAT A PLATEAU IS NOT. Neighbouring settings share most of their trades, so a plateau is not
so many separate proofs: it shows the result does not hang on one value, and no more. Whether
it beat luck is the luck rungs' to say, on every setting counted.

THE GRID'S LIMITS, refused as faults in the test. Values a hair apart are one rule tried
twice, and a plateau of them is a peak: neighbouring values are at least STEP apart, as a
share of the lower, so whole numbers above ten cannot be tried one by one. A parameter is
above nothing. A parameter with under three values has no setting with a neighbour on both
sides. Values are whole numbers or exact decimals, compared exactly.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from itertools import product

from lab.rung import Verdict

Value = int | Decimal
#: A setting: one value of each parameter, in the grid's order.
Setting = tuple[Value, ...]
Grid = Sequence[Sequence[Value]]  #: each parameter's values, lowest first
Place = tuple[int, ...]  #: a setting's rank along each parameter of the grid

#: The least depth promoted: the setting and every setting one step from it passed.
DEPTH = 2
#: The least step between neighbouring values of a parameter, as a share of the lower.
STEP = Decimal("0.1")


@dataclass(frozen=True)
class Chosen:
    setting: Setting
    verdict: Verdict  #: the first rung's, at the setting
    depth: int  #: steps to the nearest setting that failed or was never tried
    floor: Decimal | None  #: the worst t among it and the tried settings beside it

    @property
    def passed(self) -> bool:
        """Promoted: the centre of a plateau, not a peak."""
        return self.depth >= DEPTH


def depths(grid: Grid, surface: Mapping[Setting, Verdict]) -> dict[Setting, int]:
    """Every tried setting's depth: 0 where it failed, 1 on a lone peak or an edge."""
    at, deep = _laid(grid, surface)
    return {setting: deep.get(place, 0) for place, setting in at.items()}


def choose(grid: Grid, surface: Mapping[Setting, Verdict]) -> Chosen:
    """The surface's centre: the deepest setting, then the one on the best worst ground."""
    at, deep = _laid(grid, surface)
    most = max(deep.values(), default=0)

    def ground(place: Place) -> tuple[bool, Decimal]:
        moves = product((-1, 0, 1), repeat=len(place))
        beside = (tuple(p + m for p, m in zip(place, move, strict=True)) for move in moves)
        scores = (surface[at[near]].t for near in beside if near in at)
        return min((t is not None, t or Decimal(0)) for t in scores)

    best = max(sorted(place for place in at if deep.get(place, 0) == most), key=ground)
    scored, floor = ground(best)
    return Chosen(at[best], surface[at[best]], most, floor if scored else None)


def _laid(
    grid: Grid, surface: Mapping[Setting, Verdict]
) -> tuple[dict[Place, Setting], dict[Place, int]]:
    """Each tried setting by its place on the grid, and the depth of each place that passed.
    A place is one step deeper each time it and both its neighbours along every parameter
    in turn are still standing, which is every setting one step from it, corners included."""
    at = _places(grid, surface)
    left = {place for place, setting in at.items() if surface[setting].passed}
    deep: dict[Place, int] = {}
    while left:
        deep |= {place: deep.get(place, 0) + 1 for place in left}
        for n in range(len(grid)):
            left = {
                place
                for place in left
                if all((*place[:n], place[n] + move, *place[n + 1 :]) in left for move in (-1, 1))
            }
    return at, deep


def _places(grid: Grid, surface: Mapping[Setting, Verdict]) -> dict[Place, Setting]:
    """Each tried setting's place on the grid; a grid that could show no plateau, or a false
    one, and a surface that is not the grid's, are refused."""
    if not grid:
        raise ValueError("a grid of no parameters: one parameter or more")
    ranks = [_ranks(n, values) for n, values in enumerate(grid)]
    if not surface:
        raise ValueError("no settings: there is no surface to find a plateau on")
    for setting in surface:
        on = isinstance(setting, tuple) and len(setting) == len(ranks)
        if not on or any(
            type(v) not in (int, Decimal) or v not in rank
            for v, rank in zip(setting, ranks, strict=True)
        ):
            raise ValueError(f"{setting!r} is not a setting of the grid declared")
    keys = {verdict.key for verdict in surface.values()}
    if len({key.cell for key in keys}) < len(surface):
        raise ValueError("one verdict at two settings: a setting has a cell of its own")
    if len({(k.cell.line, k.cell.start, k.cell.end, k.code, k.data) for k in keys}) > 1:
        cells = sorted(str(key.cell) for key in keys)[:3]
        raise ValueError(f"a surface is one line and window, one code and bars: {cells}...")
    return {tuple(rank[v] for v, rank in zip(s, ranks, strict=True)): s for s in surface}


def _ranks(n: int, values: Sequence[Value]) -> dict[Value, int]:
    """Each value's rank among those declared for one parameter."""
    tried = f"parameter {n + 1} at {', '.join(map(str, values[:9]))}"
    if not all(type(v) in (int, Decimal) and Decimal(v).is_finite() for v in values):
        raise ValueError(f"{tried}: values are whole numbers or exact decimals")
    if len(values) < 2 * DEPTH - 1:
        raise ValueError(f"{tried}: three values or more, or no setting has both neighbours")
    if values[0] <= 0:
        raise ValueError(f"{tried}: a parameter is above nothing")
    least = 1 + Fraction(STEP)
    steps = zip(values, values[1:], strict=False)
    if any(Fraction(upper) < Fraction(lower) * least for lower, upper in steps):
        raise ValueError(f"{tried}: lowest first, neighbours at least a tenth apart ({STEP})")
    return {value: rank for rank, value in enumerate(values)}
