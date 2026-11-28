"""The command's time limits: the worlds' phase gets time for each world it lives."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import TypeVar

import pytest

from desk import command, keeper, simcity, simcitycmd

T = TypeVar("T")


@pytest.mark.parametrize(
    ("argv", "worlds"), [([], len(simcitycmd.QUICK)), (["--full"], len(simcity.WORLDS))]
)
def test_the_worlds_phase_is_allowed_time_for_each_world_it_was_asked_to_live(
    argv: list[str], worlds: int, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A hundred worlds are given a hundred worlds' time and twenty twenty's, from one named
    allowance; the price store's read keeps its own limit, so a real hang is still caught."""
    limits: dict[str, float] = {}

    def within(limit: float, phase: str, work: Callable[[], T]) -> T:
        limits[phase] = limit
        return work()

    class Stop(Exception):  # noqa: N818 - the stub ends the night before the worlds are lived
        pass

    def stop(*_args: object) -> None:
        raise Stop

    monkeypatch.setattr(simcitycmd, "within", within)
    monkeypatch.setattr(keeper, "saved", lambda *_: ({}, frozenset()))
    monkeypatch.setattr(command, "rates", lambda *_: {})
    monkeypatch.setattr(simcity, "run", stop)
    with pytest.raises(Stop):
        simcitycmd.main(
            argv, {"KESTREL2_DATA": str(tmp_path)}, lambda: datetime(2025, 1, 1, tzinfo=UTC)
        )
    assert limits["the worlds"] == simcitycmd.PER_WORLD * worlds
    assert limits["reading the price store"] == simcitycmd.LIMIT
