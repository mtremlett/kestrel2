"""simcity_incidents: the night of 2026-11-16, when the deep job ran to its time limit (no end
after 21600 seconds), lived again; the desk tells him which job and how, and its day goes on."""

from __future__ import annotations

from pathlib import Path

import pytest
from test_simcity import busy

from desk import simcity, supervisor
from desk.simcity_incidents import RAN_OUT, ran_out

TOLD = "a job that ran to its time limit is told to him, by name and how"


def lived(patch: pytest.MonkeyPatch, root: Path) -> simcity.Night:
    patch.setattr(simcity, "EVENTS", ((RAN_OUT, ran_out),))
    return busy(patch, root, (0, 1))


def test_a_job_that_runs_out_of_time_is_told_and_the_census_counts_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    night = lived(monkeypatch, tmp_path)
    assert not [b for b in night.broken if TOLD in b or "never happened" in b], night.broken
    assert RAN_OUT in night.census["day.run"], "the census counts the scenario"


def test_the_scenario_is_red_when_the_desk_says_nothing_of_the_job(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(supervisor, "health", lambda *_: ())
    assert any(TOLD in broken for broken in lived(monkeypatch, tmp_path).broken)
