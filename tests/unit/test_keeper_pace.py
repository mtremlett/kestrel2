"""The keeper's polling ramp: a refusal halves it, a clean round raises it."""

from __future__ import annotations

import pytest

from desk import keeper


@pytest.mark.parametrize(
    ("minutes", "rate", "refusals", "expected"),
    [(5, 27, 0, 33), (5, 100, 1, 50), (5, 30, 3, 27), (5, 270, 0, 270), (60, 324, 0, 405)],
)
def test_pace(minutes: int, rate: int, refusals: int, expected: int) -> None:
    """A refusal halves to the floor at least; a clean round rises to the ceiling at most."""
    assert keeper.pace(minutes, rate, refusals) == expected
