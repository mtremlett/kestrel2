"""simcity: one command lives the desk's fourteen months at the pretend broker with its faults
and writes one record; the census names every part of the money path with the scenarios that
ran it, and a part with none turns the night red."""

from __future__ import annotations

import csv
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from desk import simcity
from desk.broker import Fault, Pretend
from desk.lines import YARDSTICK
from desk.orders import Settings

sys.path.insert(0, str(Path(__file__).parents[1] / "scenes"))  #: the scenes' rehearsal data
from rehearsal import CLEAN, LINES, SESSIONS  # noqa: E402  the path above comes first

MARKET = {**CLEAN, YARDSTICK: CLEAN[LINES[1]]}  #: the yardstick among its lines, as the scenes'
ROOM, RATES = Settings(Decimal(10_000)), {"GBP": Decimal(1), "USD": Decimal("0.79")}
NOW = datetime(2025, 11, 17, 22, 0, tzinfo=UTC)
#: Ten weeks of it: the breakout rule buys, and nothing is ever sold.
SHORT = {line: [bar for bar in bars if bar.day <= SESSIONS[50]] for line, bars in MARKET.items()}


@pytest.fixture(scope="module")
def lived(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, simcity.Night]:
    """The fourteen months, lived once for every test here that reads them."""
    root = tmp_path_factory.mktemp("nights")
    return root, simcity.run(root, MARKET, ROOM, RATES, NOW)


def test_the_fourteen_months_are_lived_with_every_fault_and_the_night_is_green(
    lived: tuple[Path, simcity.Night],
) -> None:
    root, night = lived
    assert night.green and not night.bare and not night.broken, night.words()
    assert night.days == len(SESSIONS) - 1, "a session of the fourteen months without its day"
    assert all(night.met.values()), f"no order filled whole, or a fault never met: {night.met}"
    assert night.deaths >= 2, "the desk never died with an order filled, and with one left working"
    assert night.withheld >= 2 and night.trips, "no day's profit withheld, or no round trip"
    assert night.profit != 0 != night.market
    assert night.idle == ("trend_50_200",), "the rules that never hold a line in the rehearsal"
    for said in ("SIMCITY GREEN", "2025-11-17", f"{night.days} days", "trend_50_200", "0 with no"):
        assert said in night.words(), f"the night did not say {said!r}: {night.words()}"
    with (root / simcity.NIGHTS).open(newline="", encoding="utf-8") as kept:
        header, row = csv.reader(kept)  #: one record for the night, under its names
    assert header == list(simcity.HEADER) and row[:3] == [NOW.isoformat(), "GREEN", "310"]


def test_the_census_names_every_part_of_the_money_path_and_the_scenarios_that_ran_it(
    lived: tuple[Path, simcity.Night],
) -> None:
    census = lived[1].census
    ran = {
        "strategy.decide": simcity.RULES,
        "day.run": simcity.DAY,
        "book.send": simcity.RESTART,
        "broker.Pretend.inject": simcity.BEHIND,
        "broker.Pretend.cancel_stop": simcity.UNSTOPPED,
        "kill.pull": simcity.KILLED,
        "kill.Killed.words": simcity.KILLED,
        "orders.Charges.total": simcity.DAY,  #: a property is a part as a method is
        "book.round_trips": simcity.RECKONING,
        **{f"broker.Fault.{fault.name}": simcity.FAULTS for fault in Fault},
    }
    for part, scenario in ran.items():
        assert scenario in census[part], f"{part} not run by {scenario!r}: {census.get(part)}"
    assert census["kill.pull"] == (simcity.KILLED,), "a part put down to a scenario not its own"
    #: every name a module of the path offers, and nothing kept to itself or only a wording
    assert {part for part in census if part.startswith("kill.")} == {
        *("kill.pull", "kill.release", "kill.drill", "kill.drilled", "kill.Killed.words")
    }
    assert not [part for part in census if "._" in part or part.startswith("broker.Broker.")]


def test_a_scenario_that_never_ran_leaves_its_parts_bare_and_the_night_red(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    #: nothing is sold in ten weeks, so the line that lost its stop is never put right
    night = simcity.run(tmp_path, SHORT, ROOM, RATES, NOW)
    assert not night.green and "SIMCITY RED" in night.words()
    assert f"never happened: {simcity.KILLED}" in night.broken, night.broken
    assert any("ends plain" in broken for broken in night.broken), "it ended on a withheld day"
    assert {"kill.pull", "kill.drill", "broker.Pretend.cancel", "book.turn"} <= {
        *night.bare
    }, "a part no scenario ran was not named"
    assert all(part in night.words() for part in night.bare + night.broken)
    assert "broker.Pretend.inject" not in night.bare, "a part that ran was called bare"

    #: the same ten weeks with the kill switch pulled first, and no morning left for the last
    monkeypatch.setattr(simcity, "EVENTS", simcity.EVENTS[::-1])
    again = simcity.run(tmp_path, SHORT, ROOM, RATES, NOW)
    assert again.census["kill.pull"] == (simcity.KILLED,) and "kill.drill" not in again.bare
    assert f"never happened: {simcity.BEHIND}" in again.broken, again.broken
    assert "broker.Pretend.inject" in again.bare, "bare follows the scenario that did not run"
    with (tmp_path / simcity.NIGHTS).open(newline="", encoding="utf-8") as kept:
        assert [row[1] for row in csv.reader(kept)] == ["verdict", "RED", "RED"], "a night lost"
    (tmp_path / simcity.NIGHTS).write_text("something else\n", encoding="utf-8")
    with pytest.raises(ValueError, match="not SimCity's nights"):
        simcity.run(tmp_path, SHORT, ROOM, RATES, NOW)
    with pytest.raises(ValueError, match="UTC"):
        simcity.run(tmp_path, SHORT, ROOM, RATES, NOW.replace(tzinfo=None))


def test_a_promise_the_desk_breaks_turns_the_night_red_and_is_named(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(Pretend, "inject", lambda *_: None)  #: the position never appears
    night = simcity.run(tmp_path, SHORT, ROOM, RATES, NOW)
    assert any("did not make" in broken for broken in night.broken), night.broken
    assert not night.green and "BROKEN" in night.words()
