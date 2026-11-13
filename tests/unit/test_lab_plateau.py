"""Plateaus over peaks: the centre of a plateau promoted, never a lone peak."""

from __future__ import annotations

from collections.abc import Callable
from datetime import timedelta
from decimal import Decimal
from itertools import product

import pytest
from test_lab_luck import DAY

from lab import plateau, rung
from lab.cell import Cell, Key, Trade
from lab.plateau import Setting
from lab.rung import Priced, Verdict

PASS, FAIL, PEAK = "0.010", "0.005", "0.030"  #: mean gains: 2.7, 1.3 and 8 standard errors
FIVE = (10, 20, 30, 40, 50)


def _verdict(edge: str, symbol: str = "VUSA", days: int = 0) -> Verdict:
    """Thirty trades around this mean gain, judged by the first rung's own rule."""
    gains = [Decimal(edge) + Decimal("0.02") * (-1) ** n for n in range(30)]
    priced = tuple(Priced(Trade(DAY, DAY), 1, Decimal(1), 1 + g, g) for g in gains)
    window = Cell("breakout_20_10", symbol, DAY, DAY + timedelta(days=days))
    return rung.verdict(Key(window, "code", "data"), priced)


def _surface(
    edge: Callable[[Setting], str] | str, *axes: tuple[int, ...]
) -> dict[Setting, Verdict]:
    """A verdict at every setting of the grid: of one mean gain, or of each setting's own."""
    return {s: _verdict(edge if isinstance(edge, str) else edge(s)) for s in product(*axes)}


def _square(setting: Setting) -> str:
    """A plateau three settings square at 20 to 40, a rise at its corner (20, 20), and a
    lone peak at (60, 60), the best score on the grid."""
    if setting == (60, 60):
        return PEAK
    inside = all(20 <= value <= 40 for value in setting)
    return ("0.015" if setting == (20, 20) else PASS) if inside else FAIL


def test_the_centre_of_a_plateau_is_promoted_and_the_lone_peak_is_not() -> None:
    surface = _surface(_square, (10, 20, 30, 40, 50, 60, 70), (10, 20, 30, 40, 50, 60, 70))
    assert plateau.DEPTH == 2 and Decimal("0.1") == plateau.STEP
    assert _verdict(PEAK).passed and _verdict(PASS).passed and not _verdict(FAIL).passed
    depths = plateau.depths(surface)
    assert depths[60, 60] == 1, "a peak alone: every setting beside it failed"
    assert depths[30, 30] == 2 and depths[20, 20] == depths[40, 30] == 1 and depths[50, 50] == 0
    chosen = plateau.choose(surface)
    assert chosen.setting == (30, 30) and chosen.passed and chosen.depth == 2
    assert chosen.verdict is surface[30, 30] and chosen.floor == surface[30, 30].t
    best = max(surface, key=lambda s: surface[s].t or 0)
    assert best == (60, 60) != chosen.setting, "the best score on the grid is not the choice"
    #: the peak alone on the grid: the best there is, shown, and not promoted
    alone = plateau.choose(surface | {s: _verdict(FAIL) for s in product((20, 30, 40), repeat=2)})
    assert (alone.setting, alone.depth, alone.passed) == ((60, 60), 1, False)
    assert alone.floor == _verdict(FAIL).t
    #: nothing passed anywhere: the best of them is shown at depth nothing
    none = plateau.choose(_surface(FAIL, FIVE) | {(30,): _v0()})
    assert (none.setting, none.depth, none.passed) == ((10,), 0, False)
    beside = plateau.choose(_surface(FAIL, (10, 20, 30)) | {(20,): _v0()})
    assert beside.floor is None, "a neighbour with one trade has no score to stand on"


def _v0() -> Verdict:
    """One trade: no standard errors at all, so it fails and stands lowest."""
    return rung.verdict(_verdict(PASS).key, _verdict(PASS).trades[:1])


def test_the_centre_is_the_setting_deepest_inside_then_the_one_with_the_best_worst() -> None:
    #: one parameter, a plateau from 20 to 60 with its best score at its edge
    wide = _surface(lambda s: PEAK if s == (20,) else PASS, (20, 30, 40, 50, 60))
    wide |= {(10,): _verdict(FAIL), (70,): _verdict(FAIL)}
    assert plateau.depths(wide) == dict(zip(sorted(wide), (0, 1, 2, 3, 2, 1, 0), strict=True))
    assert plateau.choose(wide).setting == (40,) and plateau.choose(wide).depth == 3
    #: two centres as deep: the one whose worst neighbour is better, not the higher score
    edges: dict[Setting, str] = {(30,): "0.012", (40,): "0.012", (50,): "0.020", (60,): "0.011"}
    two = _surface(lambda s: edges.get(s, FAIL), (20, 30, 40, 50, 60, 70))
    chosen = plateau.choose(two)
    assert plateau.depths(two)[40,] == plateau.depths(two)[50,] == 2
    assert chosen.setting == (40,) and chosen.floor == two[40,].t and chosen.depth == 2
    assert (two[50,].t or 0) > (two[40,].t or 0) > (two[60,].t or 0)
    #: as deep and as good: the first setting in order, whatever order they came in
    level = _surface(lambda s: PASS if 20 <= s[0] <= 50 else FAIL, (10, 20, 30, 40, 50, 60))
    assert plateau.choose(level).setting == (30,)
    assert plateau.choose(dict(reversed(level.items()))).setting == (30,)


def test_a_setting_never_tried_and_the_grids_own_edge_are_no_plateau() -> None:
    level = _surface(PASS, FIVE, FIVE)
    assert plateau.depths(level)[30, 30] == 3 and plateau.depths(level)[10, 30] == 1
    assert plateau.choose(level).setting == (30, 30), "the grid's edge is where the trying ended"
    #: a diagonal neighbour that failed breaks it as a side one does
    for hole in ((20, 20), (30, 20)):
        failed = plateau.depths(level | {hole: _verdict(FAIL)})
        untried = plateau.depths({s: v for s, v in level.items() if s != hole})
        assert failed[30, 30] == untried[30, 30] == 1 and hole not in untried
    #: a passing edge with no room beside it: the best on a slope still rising, not a plateau
    slope = _surface(lambda s: PASS if s[0] >= 40 else FAIL, FIVE)
    assert not plateau.choose(slope).passed and plateau.choose(slope).depth == 1
    #: steps are the grid's own, on exact numbers: 2 to 2.2 is a step, uneven steps too
    fine: dict[Setting, Verdict] = {
        (Decimal(v),): _verdict(PASS) for v in ("2", "2.2", "3.3", "30", "33")
    }
    assert plateau.choose(fine).setting == (Decimal("3.3"),) and plateau.choose(fine).depth == 3


def test_a_surface_that_cannot_show_a_plateau_is_refused() -> None:
    line = _surface(PASS, FIVE)
    refused: list[tuple[str, dict[Setting, Verdict]]] = [
        ("no settings", {}),
        ("one parameter or more", {(): _verdict(PASS)}),
        ("the same parameters", line | {(30, 30): _verdict(PASS)}),
        ("three values or more", _surface(PASS, FIVE, (10, 20))),
        ("above nothing", line | {(0,): _verdict(PASS)}),
        ("a tenth apart", line | {(21,): _verdict(PASS)}),
        ("one line and window", line | {(60,): _verdict(PASS, "ISF")}),
        ("one line and window", line | {(60,): _verdict(PASS, days=1)}),
    ]
    for why, surface in refused:
        with pytest.raises(ValueError, match=why):
            plateau.choose(surface)
    with pytest.raises(ValueError, match="a tenth apart"):
        plateau.depths({(Decimal(v),): _verdict(PASS) for v in ("3", "3.2", "4")})
