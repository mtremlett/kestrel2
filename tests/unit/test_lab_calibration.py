"""The calibration line (R-MONEY-43): each rung's pass rate on seeded noise worlds. And the first
rung proven alone: a planted edge passes, five hundred cells of pure noise pass at the stated rate
and no more, a power curve rises, a broken rung is caught, and the old desk's audit defects
(LAD-09, LAD-03, LAD-08) stay cases that must fail."""

from __future__ import annotations

import random
from datetime import date
from decimal import Decimal

import pytest
from test_lab_rung import FREE

from desk.lines import LINES
from lab import calibration, luck, rung
from lab.cell import Cell, Key, Trade
from lab.rung import Answer, Priced, Verdict, noise_band

VUSA = next(line for line in LINES if line.symbol == "VUSA")
DAY, CELLS = date(2020, 1, 1), 500
#: The most a no-edge cell passes at, fixed from the rung as built when this loads: a rung altered
#: afterwards (a bar lowered, a minimum dropped) drifts from it and falls out of its band.
STATED = luck.tail(float(rung.T_PASS), rung.MIN_TRADES - 1)


def _cell(seed: int, edge: float, trades: int = rung.MIN_TRADES) -> Verdict:
    """One cell of so many trades, each gain drawn around the edge with a spread of 2%."""
    rng = random.Random(seed)  # noqa: S311 - a repeatable test draw, not a secret
    back = [Decimal(f"{100 * (1 + rng.gauss(edge, 0.02)):.4f}") for _ in range(trades)]
    priced = tuple(
        Priced(Trade(DAY, DAY), 1, Decimal(100), b, FREE, (DAY, DAY), None) for b in back
    )
    return rung.verdict(Key(Cell("breakout_20_10", VUSA, DAY, DAY), "code", str(seed)), priced)


def _noise() -> list[Verdict]:
    return [_cell(seed, 0) for seed in range(CELLS)]


def test_the_stated_rate_is_students_published_one() -> None:
    #: the textbook's 2.5% beyond 2.0452 at 29 degrees of freedom: 2.0 is a little nearer
    assert 0.025 < STATED < 0.03
    assert pytest.approx(0.0274, abs=0.0001) == STATED
    #: Feller's exact binomial: ten fair-coin flips, 0.002 missed, hold 0 to 10 and 1 to 9
    assert noise_band(10, 0.5, 0.002) == (1, 9)
    assert noise_band(10, 0.5, 0.0005) == (0, 10)
    for wrong in ((0, 0.5, 0.1), (10, 0.0, 0.1), (10, 0.5, 1.0)):
        with pytest.raises(ValueError, match="out of range"):
            noise_band(*wrong)


def test_a_planted_edge_passes() -> None:
    assert all(_cell(seed, 0.02).passed for seed in range(CELLS))


def test_pure_noise_passes_at_about_the_stated_rate_and_no_more() -> None:
    passes = sum(v.passed for v in _noise())
    low, high = noise_band(CELLS, STATED)
    assert low <= passes <= high, f"{passes} of {CELLS}, band {low}-{high}, stated {STATED}"
    assert passes > 0, "a rung that never passes noise has a bar that nothing could clear"


def test_the_power_curve_rises_with_the_edge() -> None:
    power = [
        sum(_cell(s, e, 40).passed for s in range(CELLS)) / CELLS for e in (0.004, 0.008, 0.016)
    ]
    assert power[0] < 0.4 < 0.6 < power[1] < 0.95 < power[2] == 1.0, power


@pytest.mark.parametrize("damage", [("T_PASS", Decimal(1)), ("MIN_TRADES", 5)])
def test_a_broken_copy_of_the_rung_is_caught(
    monkeypatch: pytest.MonkeyPatch, damage: tuple[str, object]
) -> None:
    monkeypatch.setattr(rung, *damage)
    noise = [_cell(seed, 0, 30 if damage[0] == "T_PASS" else 5) for seed in range(CELLS)]
    low, high = noise_band(CELLS, STATED)
    assert (
        sum(v.passed for v in noise) > high
    ), "a bar lowered or a minimum dropped passes more noise"


def test_the_old_audits_defects_stay_failing_cases() -> None:
    #: LAD-09: a strong run of too few trades is not enough evidence, and not a pass
    strong = _cell(1, 0.02, rung.MIN_TRADES - 1)
    assert strong.t is not None and strong.t > 5 and strong.answer is Answer.THIN
    #: LAD-03, LAD-08: of five hundred noise cells about fourteen pass alone, and none is
    #: believed once each is corrected for the whole set at the one 5%
    noise = _noise()
    assert sum(v.passed for v in noise) > 0
    assert not any(c.passed for c in luck.correct(noise, 0))


def test_noise_passes_every_rung_at_about_its_stated_rate_and_the_line_names_them_all() -> None:
    worlds = 200
    count = calibration.passes(worlds)
    declared, _ = rung.found()
    assert list(count) == ["first", *(one.name for one in declared)]
    low, high = noise_band(worlds, STATED)
    assert low <= count["first"] <= high, "the first rung lands in its stated band"
    assert all(n <= 0.10 * worlds for n in count.values()), count
    line = calibration.words(worlds)
    assert line.startswith("Calibration: first ") and f"of {worlds} noise worlds" in line
    assert calibration.words(worlds) == line, "seeded, so repeatable"


def test_the_command_takes_one_number_of_worlds_or_refuses() -> None:
    with pytest.raises(SystemExit, match="usage"):
        calibration.main(["many"])
    assert calibration.main(["3"]) == 0
