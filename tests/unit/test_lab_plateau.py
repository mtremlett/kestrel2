"""Plateaus over peaks: the centre of a plateau promoted, never a lone peak."""

from __future__ import annotations

from collections.abc import Callable
from datetime import timedelta
from decimal import Decimal
from itertools import product

import pytest
from test_lab_luck import DAY
from test_lab_rung import FREE

from lab import cell, plateau, rung
from lab.cell import Cell, Key, Trade
from lab.plateau import Grid, Setting
from lab.rung import Priced, Verdict

PASS, FAIL, PEAK = "0.010", "0.005", "0.030"  #: mean gains: 2.7, 1.3 and 8 standard errors
FIVE = (10, 20, 30, 40, 50)
SEVEN = (*FIVE, 60, 70)
Days = tuple[int, int]
Edge = Callable[[Setting], str]


class _AnyRule:
    """The desk's five rules have no settings yet: here every setting is a rule by name."""

    def __contains__(self, name: str) -> bool:
        return True


@pytest.fixture(autouse=True)
def _a_rule_at_every_setting(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cell, "STRATEGIES", _AnyRule())


def _verdict(edge: str, rule: str = "r", symbol: str = "VUSA", days: Days = (0, 9)) -> Verdict:
    """Thirty trades around this mean gain, judged by the first rung's own rule."""
    gains = [Decimal(edge) + Decimal("0.02") * (-1) ** n for n in range(30)]
    priced = tuple(Priced(Trade(DAY, DAY), 1, Decimal(1), 1 + g, FREE) for g in gains)
    start, end = (DAY + timedelta(days=n) for n in days)
    return rung.verdict(Key(Cell(rule, symbol, start, end), "code", "data"), priced)


def _surface(edge: Edge | str, *axes: tuple[int, ...]) -> dict[Setting, Verdict]:
    """A verdict at every setting of the grid: of one mean gain, or of each setting's own."""
    return {s: _verdict(edge if isinstance(edge, str) else edge(s), str(s)) for s in product(*axes)}


def _none(rule: str) -> Verdict:
    """One trade: no standard errors at all, so it fails and stands lowest."""
    whole = _verdict(PASS, rule)
    return rung.verdict(whole.key, whole.trades[:1])


def _square(setting: Setting) -> str:
    """A plateau three settings square at 20 to 40, a rise at its corner (20, 20), and a
    lone peak at (60, 60), the best score on the grid."""
    if setting == (60, 60):
        return PEAK
    inside = all(20 <= value <= 40 for value in setting)
    return ("0.015" if setting == (20, 20) else PASS) if inside else FAIL


def test_the_centre_of_a_plateau_is_promoted_and_the_lone_peak_is_not() -> None:
    grid, surface = (SEVEN, SEVEN), _surface(_square, SEVEN, SEVEN)
    assert plateau.DEPTH == 2 and Decimal("0.1") == plateau.STEP
    assert _verdict(PEAK).passed and _verdict(PASS).passed and not _verdict(FAIL).passed
    depths = plateau.depths(grid, surface)
    assert depths[60, 60] == 1, "a peak alone: every setting beside it failed"
    assert depths[30, 30] == 2 and depths[20, 20] == depths[40, 30] == 1 and depths[50, 50] == 0
    chosen = plateau.choose(grid, surface)
    assert chosen.setting == (30, 30) and chosen.passed and chosen.depth == 2
    assert chosen.verdict is surface[30, 30] and chosen.floor == surface[30, 30].t
    best = max(surface, key=lambda s: surface[s].t or 0)
    assert best == (60, 60) != chosen.setting, "the best score on the grid is not the choice"
    #: the peak alone on the grid: the deepest there is, shown, and not promoted
    flat = {s: _verdict(FAIL, str(s)) for s in product((20, 30, 40), repeat=2)}
    alone = plateau.choose(grid, surface | flat)
    assert (alone.setting, alone.depth, alone.passed) == ((60, 60), 1, False)
    assert alone.floor == _verdict(FAIL).t
    #: nothing passed anywhere: shown at depth nothing, on the best of the worst ground,
    #: where a score below nothing still stands above no score at all
    low = {(10,): _verdict("-0.010", "a"), (20,): _verdict("-0.010", "b"), (40,): _none("c")}
    none = plateau.choose((FIVE,), _surface(FAIL, FIVE) | low)
    assert (none.setting, none.depth, none.passed) == ((10,), 0, False)
    assert none.floor == low[10,].t and (none.floor or 0) < 0
    beside = plateau.choose((FIVE[:3],), _surface(FAIL, FIVE[:3]) | {(20,): _none("c")})
    assert beside.floor is None, "a neighbour with one trade has no score to stand on"


def test_the_centre_is_the_setting_deepest_inside_then_the_one_with_the_best_worst() -> None:
    #: one parameter, a plateau from 20 to 60 with its best score at its edge
    wide = _surface(
        lambda s: PEAK if s == (20,) else PASS if s[0] in range(20, 61) else FAIL, SEVEN
    )
    assert list(plateau.depths((SEVEN,), wide).values()) == [0, 1, 2, 3, 2, 1, 0]
    chosen = plateau.choose((SEVEN,), wide)
    assert chosen.setting == (40,) and chosen.depth == 3 and chosen.floor == wide[40,].t
    #: two centres as deep: the one whose worst neighbour is better, though the other is
    #: the higher score and the first in order
    edges: dict[Setting, str] = {(30,): "0.011", (40,): "0.020", (50,): "0.012", (60,): "0.012"}
    two = _surface(lambda s: edges.get(s, FAIL), SEVEN)
    chosen = plateau.choose((SEVEN,), two)
    assert plateau.depths((SEVEN,), two)[40,] == plateau.depths((SEVEN,), two)[50,] == 2
    assert chosen.setting == (50,) and chosen.floor == two[50,].t and chosen.depth == 2
    assert (two[40,].t or 0) > (two[50,].t or 0) > (two[30,].t or 0)
    #: as deep and as good: the first setting in order, whatever order they came in
    level = _surface(lambda s: PASS if 20 <= s[0] <= 50 else FAIL, SEVEN)
    assert plateau.choose((SEVEN,), level).setting == (30,)
    assert plateau.choose((SEVEN,), dict(reversed(level.items()))).setting == (30,)


def test_a_setting_never_tried_and_the_grids_own_edge_are_no_plateau() -> None:
    grid, level = (FIVE, FIVE), _surface(PASS, FIVE, FIVE)
    assert plateau.depths(grid, level)[30, 30] == 3 and plateau.depths(grid, level)[10, 30] == 1
    assert plateau.choose(grid, level).setting == (30, 30), "the edge is where the trying ended"
    #: a neighbour that failed breaks it, at a corner as at a side, and two steps off as one
    for hole, left in (((20, 20), 1), ((30, 20), 1), ((10, 10), 2), ((30, 10), 2)):
        failed = plateau.depths(grid, level | {hole: _verdict(FAIL, "hole")})
        untried = plateau.depths(grid, {s: v for s, v in level.items() if s != hole})
        assert failed[30, 30] == untried[30, 30] == left and hole not in untried
    #: a passing edge with no room beside it: the best on a slope still rising, not a plateau
    slope = plateau.choose((FIVE,), _surface(lambda s: PASS if s[0] >= 40 else FAIL, FIVE))
    assert not slope.passed and slope.depth == 1
    #: failures left off the surface are settings never tried: nothing is drawn together
    combs = _surface(lambda s: PASS if s[0] in (20, 40, 60) else FAIL, SEVEN)
    kept = {s: v for s, v in combs.items() if v.passed}
    assert plateau.depths((SEVEN,), kept) == dict.fromkeys(kept, 1)
    assert not plateau.choose((SEVEN,), kept).passed and not plateau.choose((SEVEN,), combs).passed
    #: steps are the grid's own, on exact numbers: 10 to 11 is a step, uneven steps too
    exact = (10, 11, Decimal("12.1"), Decimal("30"), 33)
    fine: dict[Setting, Verdict] = {(v,): _verdict(PASS, str(v)) for v in exact}
    chosen = plateau.choose((exact,), fine)
    assert chosen.setting == (Decimal("12.1"),) and chosen.depth == 3


def test_a_grid_or_a_surface_that_cannot_show_a_true_plateau_is_refused() -> None:
    line, big = _surface(PASS, FIVE), Decimal("1e30")
    refused: list[tuple[str, Grid, dict[Setting, Verdict]]] = [
        ("one parameter or more", (), line),
        ("no settings", (FIVE,), {}),
        ("three values or more", (FIVE, (10, 20)), line),
        ("three values or more", ((10,),), line),
        ("above nothing", ((0, 10, 20),), line),
        ("above nothing", ((-3, -2, -1),), line),
        ("a tenth apart", ((10, 20, 21, 30),), line),
        ("a tenth apart", ((30, 20, 10),), line),
        ("a tenth apart", ((10, 10, 20),), line),
        ("a tenth apart", ((Decimal("3"), Decimal("3.2"), Decimal("4")),), line),
        ("a tenth apart", ((big, Decimal("1" + "09" + "9" * 28), 2 * big),), line),
        ("exact decimals", ((10, 20.5, 30),), line),  # type: ignore[list-item]
        ("exact decimals", ((True, 2, 3),), line),
        ("exact decimals", ((10, 20, Decimal("Infinity")),), line),
        ("not a setting of the grid", (FIVE,), line | {(60,): _verdict(PASS)}),
        ("not a setting of the grid", (FIVE,), line | {(30, 30): _verdict(PASS)}),
        ("not a setting of the grid", (FIVE,), {(float(v),): x for (v,), x in line.items()}),  # type: ignore[misc]
        ("a cell of its own", (FIVE,), line | {(30,): line[40,]}),
        ("one line and window", (FIVE,), line | {(30,): _verdict(PASS, symbol="ISF")}),
        ("one line and window", (FIVE,), line | {(30,): _verdict(PASS, days=(0, 8))}),
        ("one line and window", (FIVE,), line | {(30,): _verdict(PASS, days=(1, 9))}),
    ]
    for why, grid, surface in refused:
        with pytest.raises(ValueError, match=why):
            plateau.choose(grid, surface)
    with pytest.raises(ValueError, match="a tenth apart"):
        plateau.depths(((10, 20, 21),), line)
    for field in ("code", "data"):
        key = Key(line[30,].key.cell, **{"code": "code", "data": "data", field: "other"})
        with pytest.raises(ValueError, match="one code and bars"):
            plateau.choose((FIVE,), line | {(30,): rung.verdict(key, line[30,].trades)})
