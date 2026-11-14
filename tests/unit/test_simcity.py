"""simcity: one command lives the desk's fourteen months at the pretend broker with its faults
and writes one record; the census names every part of the money path with the scenarios that
ran it, and a part with none, or a promise of the desk's broken, turns the night red."""

from __future__ import annotations

import csv
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from desk import book, orders, simcity, strategy
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
#: FOUND BY SIMCITY'S FIRST NIGHT, and not this module's to mend: an order left working by a
#: desk that died fills at the next open, and the gate, which counts the book alone, has by
#: then let five other lines be bought. When the send path counts what is still working this
#: promise is kept, the night is green, and this line goes in the same change.
SIX_HELD = (f"never more than {orders.HOLDINGS} lines are held",)


@pytest.fixture(scope="module")
def lived(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, simcity.Night]:
    """The fourteen months, lived once for every test here that reads them."""
    root = tmp_path_factory.mktemp("nights")
    return root, simcity.run(root, MARKET, ROOM, RATES, NOW)


def test_the_fourteen_months_are_lived_with_every_fault_and_the_night_is_recorded(
    lived: tuple[Path, simcity.Night],
) -> None:
    root, night = lived
    assert not night.bare, night.words()
    assert night.broken == SIX_HELD and not night.green, night.words()
    assert night.days == len(SESSIONS) - 1, "a session of the fourteen months without its day"
    assert all(night.met.values()), f"no order without a fault, or a fault never met: {night.met}"
    assert night.deaths == night.met[Fault.CRASH] + night.met[Fault.STRAND] >= 2
    assert night.withheld >= 2 and night.trips, "no day's profit withheld, or no round trip"
    assert night.profit != 0 != night.market
    assert set(night.idle) < set(strategy.STRATEGIES), "no rule ever held a line"
    said = ("SIMCITY RED", "2025-11-17 22:00", f"{night.days} days", "0 with no", *night.idle)
    for part in (*said, f"BROKEN: {SIX_HELD[0]}", *(fault.value for fault in Fault)):
        assert part in night.words(), f"the night did not say {part!r}: {night.words()}"
    with (root / simcity.NIGHTS).open(newline="", encoding="utf-8") as kept:
        header, row = csv.reader(kept)  #: one record for the night, each number under its name
    assert header == list(simcity.HEADER)
    assert dict(zip(header, row, strict=True)) == {
        **{"at": NOW.isoformat(), "verdict": "RED", "days": "310", "clean": str(night.met[None])},
        **{fault.name.lower(): str(night.met[fault]) for fault in Fault},
        **{"deaths": str(night.deaths), "withheld": str(night.withheld), "bare": ""},
        **{"trips": str(night.trips), "profit": str(night.profit), "market": str(night.market)},
        **{"idle": "; ".join(night.idle), "broken": SIX_HELD[0]},
    }


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
    assert any("every rule asks" in broken for broken in night.broken), "ten weeks is too few"
    assert {"kill.pull", "kill.drill", "broker.Pretend.cancel", "book.turn"} <= {
        *night.bare
    }, "a part no scenario ran was not named"
    assert all(part in night.words() for part in night.bare + night.broken)
    assert "broker.Pretend.inject" not in night.bare, "a part that ran was called bare"
    assert simcity.run(tmp_path, SHORT, ROOM, RATES, NOW) == night, "the same data, another night"

    #: the same ten weeks with the kill switch pulled first, and no morning left for the last
    monkeypatch.setattr(simcity, "EVENTS", simcity.EVENTS[::-1])
    again = simcity.run(tmp_path, SHORT, ROOM, RATES, NOW)
    assert again.census["kill.pull"] == (simcity.KILLED,) and "kill.drill" not in again.bare
    assert f"never happened: {simcity.BEHIND}" in again.broken, again.broken
    assert "broker.Pretend.inject" in again.bare, "bare follows the scenario that did not run"
    with (tmp_path / simcity.NIGHTS).open(newline="", encoding="utf-8") as kept:
        assert [row[1] for row in csv.reader(kept)] == ["verdict", *["RED"] * 3], "a night lost"


def test_a_night_that_cannot_be_kept_or_lived_is_an_error_and_leaves_nothing_running(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with pytest.raises(ValueError, match="UTC"):
        simcity.run(tmp_path, SHORT, ROOM, RATES, NOW.replace(tzinfo=None))
    with pytest.raises(ValueError, match="no close of"):  #: the yardstick is not in the data
        simcity.run(tmp_path, {line: SHORT[line] for line in LINES}, ROOM, RATES, NOW)
    assert sys.getprofile() is None, "the census went on watching after the night died"
    assert not list(tmp_path.iterdir()), "a night that died was kept"
    (tmp_path / simcity.NIGHTS).write_text("something else\n", encoding="utf-8")
    monkeypatch.setattr(simcity, "_live", None)  #: refused before the night is lived at all
    with pytest.raises(ValueError, match="not SimCity's nights"):
        simcity.run(tmp_path, SHORT, ROOM, RATES, NOW)


@pytest.mark.parametrize(
    ("owner", "name", "broken_desk", "promise"),
    [  #: the shares never appear; the broker forgets its orders; the stop stays; the record
        (Pretend, "inject", lambda *_: None, "did not make"),  #: differs alone; no fill is kept
        (Pretend, "report", lambda *_: None, "reached the broker twice"),
        (Pretend, "cancel_stop", lambda *_: None, "lost its stop"),
        (book, "reconcile", lambda *_: ("L01",), "nothing is bought"),
        (book, "collect", lambda *_: None, "the ledger is the broker's own fills"),
    ],
)
def test_a_promise_the_desk_breaks_turns_the_night_red_and_is_named(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    owner: object,
    name: str,
    broken_desk: Callable[..., object],
    promise: str,
) -> None:
    kept = simcity.run(tmp_path, SHORT, ROOM, RATES, NOW)
    assert not [broken for broken in kept.broken if promise in broken], "broken on a sound desk"
    monkeypatch.setattr(owner, name, broken_desk)
    night = simcity.run(tmp_path, SHORT, ROOM, RATES, NOW)
    assert [broken for broken in night.broken if promise in broken], night.broken
    assert not night.green and f"BROKEN: {'; '.join(night.broken)}." in night.words()
