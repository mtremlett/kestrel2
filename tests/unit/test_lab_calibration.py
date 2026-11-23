"""The calibration line (R-MONEY-43): each rung's pass rate on seeded noise worlds."""

from __future__ import annotations

import pytest

from lab import calibration, rung, rung_sample


def test_noise_passes_every_rung_at_about_its_stated_rate_and_the_line_names_them_all() -> None:
    worlds = 200
    count = calibration.passes(worlds)
    declared, _ = rung.found()
    assert list(count) == ["first", *(one.name for one in declared)]
    low, high = rung_sample.band(worlds)
    assert low <= count["first"] <= high, "the first rung lands in its stated band"
    assert all(n <= 0.10 * worlds for n in count.values()), count
    line = calibration.words(worlds)
    assert line.startswith("Calibration: first ") and f"of {worlds} noise worlds" in line
    assert calibration.words(worlds) == line, "seeded, so repeatable"


def test_the_command_takes_one_number_of_worlds_or_refuses() -> None:
    with pytest.raises(SystemExit, match="usage"):
        calibration.main(["many"])
    assert calibration.main(["3"]) == 0
