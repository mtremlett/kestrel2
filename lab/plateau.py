"""plateau - PLATEAUS OVER PEAKS: of a rule's many settings, the one promoted is the centre
of a plateau, never a lone peak (canon B6).

Try a rule at many settings and the best score among them is the one luck helped most. A
real edge does not care whether a breakout looks back 20 days or 22: it shows as a stretch of
neighbouring settings that all earn, a plateau. A setting that earns while the settings beside
it do not is a peak, and a peak is the shape luck makes. So the setting promoted is never the
best score: it is the setting deepest inside a plateau, and its own score is not asked.

THE SURFACE. A setting is its parameters' values, in one fixed order, and the surface holds
the first rung's verdict (`lab/rung.py`) at each setting tried, all on one line and window.
The window is in-sample: a setting is chosen on history only, and what it earns afterwards
is the folds rung's to judge (`lab/folds.py`). Every setting on the surface is a trial the
luck rung counts (`lab/luck.py`), the centre's neighbours as much as the centre.

THE DEPTH. One step from a setting is every setting whose parameters are each the same value
or the next one tried, above or below: eight neighbours for two parameters, the corners with
the sides. A setting's depth is the steps from it to the nearest setting that did not pass
the first rung or was never tried. One that failed has depth nothing; a lone peak has depth
1, and so has any setting on the grid's own edge, where the trying ended and nothing is
known of the other side: the best on a slope still rising is not a plateau. A plateau begins
at DEPTH: the setting and every setting one step from it tried, and passed.

THE CENTRE. The setting chosen is the deepest. Of two as deep, the one whose worst score
among itself and its neighbours is the better, so a centre is ranked by the weakest ground
it stands on; then the first in the settings' own order. It is promoted only at DEPTH or
deeper: with no plateau the best there is is still shown, and it has not passed.

THE GRID is fixed before any result, and it cannot be made to flatter. Values a hair apart
are one rule tried twice, and a plateau of them is a peak: so neighbouring values of a
parameter are at least STEP apart, as a share of the lower, and a parameter is above nothing.
A parameter tried at under three values has no setting with a neighbour on both sides: such
a surface is refused, not failed, as a fault in the test. Values are whole numbers or exact
decimals, so a step is never lost to rounding.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from itertools import product

from lab.rung import Verdict

#: A setting: its parameters' values, in the rule's own fixed order.
Setting = tuple[int | Decimal, ...]
Place = tuple[int, ...]  #: a setting's rank along each parameter, among the values tried

#: The least depth promoted: the setting and every setting one step from it passed.
DEPTH = 2
#: The least step between neighbouring values of a parameter, as a share of the lower.
STEP = Decimal("0.1")


@dataclass(frozen=True)
class Chosen:
    setting: Setting
    verdict: Verdict  #: the first rung's, at the setting
    depth: int  #: steps to the nearest setting that failed or was never tried
    floor: Decimal | None  #: the worst standard errors among it and the tried settings beside it

    @property
    def passed(self) -> bool:
        """Promoted: the centre of a plateau, not a peak."""
        return self.depth >= DEPTH


def depths(surface: Mapping[Setting, Verdict]) -> dict[Setting, int]:
    """Every setting's depth: 0 where it failed, 1 on a lone peak or an edge."""
    at = _places(surface)
    passing = {place for place, setting in at.items() if surface[setting].passed}
    return {setting: _depth(place, passing) for place, setting in at.items()}


def choose(surface: Mapping[Setting, Verdict]) -> Chosen:
    """The surface's centre: the deepest setting, then the one on the best worst ground."""
    at = _places(surface)
    deep = depths(surface)

    def ground(place: Place) -> tuple[bool, Decimal]:
        beside = (surface[at[near]].t for near in _box(place, 1) if near in at)
        return min((t is not None, t or Decimal(0)) for t in beside)

    best = max(sorted(at), key=lambda place: (deep[at[place]], ground(place)))
    scored, floor = ground(best)
    return Chosen(at[best], surface[at[best]], deep[at[best]], floor if scored else None)


def _box(place: Place, reach: int) -> list[Place]:
    """Every place within so many steps of this one, itself included, on the grid or off it."""
    moves = product(range(-reach, reach + 1), repeat=len(place))
    return [tuple(p + m for p, m in zip(place, move, strict=True)) for move in moves]


def _depth(place: Place, passing: set[Place]) -> int:
    reach = 0
    while all(near in passing for near in _box(place, reach)):
        reach += 1
    return reach


def _places(surface: Mapping[Setting, Verdict]) -> dict[Place, Setting]:
    """Each setting's place on the grid of the values tried; a surface that could show no
    plateau, or could be made to show a false one, is refused."""
    sizes = {len(setting) for setting in surface}
    if not surface:
        raise ValueError("no settings: there is no surface to find a plateau on")
    if len(sizes) > 1 or sizes == {0}:
        raise ValueError(
            f"settings of {sorted(sizes)} parameters: the same parameters, in the same "
            "order, at every setting, and one parameter or more"
        )
    cells = {verdict.key.cell for verdict in surface.values()}
    if len({(cell.line, cell.start, cell.end) for cell in cells}) > 1:
        raise ValueError(f"a surface is one line and window: given {sorted(map(str, cells))}")
    ranks = [_ranks(n, sorted({setting[n] for setting in surface})) for n in range(sizes.pop())]
    return {tuple(ranks[n][value] for n, value in enumerate(s)): s for s in surface}


def _ranks(n: int, values: list[int | Decimal]) -> dict[int | Decimal, int]:
    """Each value's rank among those one parameter was tried at, lowest first."""
    tried = f"parameter {n + 1} tried at {', '.join(map(str, values))}"
    if len(values) <= DEPTH:
        raise ValueError(f"{tried}: three values or more, or no setting has both neighbours")
    if values[0] <= 0:
        raise ValueError(f"{tried}: a parameter is above nothing")
    if any(upper < lower * (1 + STEP) for lower, upper in zip(values, values[1:], strict=False)):
        raise ValueError(f"{tried}: neighbouring values are at least a tenth apart ({STEP})")
    return {value: rank for rank, value in enumerate(values)}
