"""simcity_incidents: the night of 16 November (a held line with no bar for a session) lived as
a scenario of its own: green when the desk refuses the day naming the line, red without that."""

from __future__ import annotations

from pathlib import Path

import pytest
from test_simcity import NOW, RATES, ROOM, SHORT

from desk import book, day, day_money, simcity
from desk.simcity_incidents import (
    CANCELLED,
    HOLE,
    LEFT,
    NAMED,
    PROMISE,
    SOLD,
    beside,
    cancelled,
    hole,
)


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


def test_shares_beside_the_book_under_a_stop_are_sold_with_it_and_the_census_counts_it(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(simcity, "EVENTS", ((LEFT, beside),))
    monkeypatch.setattr(simcity, "EVENTFUL", 1)
    result = simcity.run(tmp_path, SHORT, ROOM, RATES, NOW, (1, 2, 3))
    assert not any(SOLD in broken for broken in result.broken)
    assert LEFT in result.census["day.run"]


def test_without_taking_the_shares_in_the_scenario_is_red(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(book, "adopt", lambda *_a: None)  #: no sale of shares the book lacks
    monkeypatch.setattr(simcity, "EVENTS", ((LEFT, beside),))
    monkeypatch.setattr(simcity, "EVENTFUL", 1)
    result = simcity.run(tmp_path, SHORT, ROOM, RATES, NOW, (1, 2, 3))
    assert any(SOLD in broken for broken in result.broken)


def cancelled_night(patch: pytest.MonkeyPatch, root: Path) -> simcity.Night:
    patch.setattr(simcity, "EVENTS", ((CANCELLED, cancelled),))
    patch.setattr(simcity, "EVENTFUL", 1)
    return simcity.run(root, SHORT, ROOM, RATES, NOW, (1, 2, 3))


def test_orders_the_broker_cancels_unfilled_are_named_and_the_census_counts_it(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    result = cancelled_night(monkeypatch, tmp_path)
    assert not any(NAMED in broken for broken in result.broken)
    assert CANCELLED in result.census["day.run"]


def test_without_naming_the_cancelled_orders_the_scenario_is_red(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(day, "_answer", lambda _root, _day, sent: sent)  #: no list is written
    assert any(NAMED in broken for broken in cancelled_night(monkeypatch, tmp_path).broken)
