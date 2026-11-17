"""The benchmark rung's known answer: Student's paired sleep data, with its published numbers."""

from __future__ import annotations

import pytest

from lab import rung_benchmark

#: Extra hours of sleep, drug 2 less drug 1, ten patients (Student 1908; R's `sleep`): the
#: published mean is 1.58 and t = 4.0621 on 9 degrees of freedom, so the standard error is
#: 1.58 / 4.0621 = 0.38896. The rung's interval is two standard errors either side.
SLEEP = [1.2, 2.4, 1.3, 1.3, 0.0, 1.0, 1.8, 0.8, 4.6, 1.4]


def test_the_interval_is_the_sleep_case_as_published() -> None:
    mean, low, high = rung_benchmark.interval(SLEEP)
    assert mean == pytest.approx(1.58)
    assert (mean - low) / 2 == pytest.approx(1.58 / 4.0621, abs=1e-4)
    assert low == pytest.approx(0.8021, abs=1e-4) and high == pytest.approx(2.3579, abs=1e-4)
    assert rung_benchmark.beats(low)
    assert not rung_benchmark.beats(rung_benchmark.interval([-x for x in SLEEP])[1])
