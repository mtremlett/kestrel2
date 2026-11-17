"""simcity_incidents: the night of 16 November (a held line with no bar for a session) lived as
a scenario of its own: green when the desk refuses the day naming the line, red without that."""

from __future__ import annotations

from pathlib import Path

import pytest
from test_simcity import NOW, RATES, ROOM, SHORT

from desk import day_money, simcity
from desk.simcity_incidents import HOLE, PROMISE, hole


def night(patch: pytest.MonkeyPatch, root: Path) -> simcity.Night:
    patch.setattr(simcity, "EVENTS", ((HOLE, hole),))
    patch.setattr(simcity, "EVENTFUL", 1)
    return simcity.run(root, SHORT, ROOM, RATES, NOW, (1, 2, 3))


def test_a_held_line_with_no_bar_refuses_the_day_by_name_and_the_census_counts_it(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    result = night(monkeypatch, tmp_path)
    assert not any(PROMISE in broken for broken in result.broken)
    assert HOLE in result.census["day.run"]


def test_without_the_refusal_the_scenario_is_red(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(day_money, "close", lambda a, line, _upto: a[line][-1].close)
    assert any(PROMISE in broken for broken in night(monkeypatch, tmp_path).broken)
