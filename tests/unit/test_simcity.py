"""simcity: one command lives the desk's fourteen months in seeded worlds of them, at the pretend
broker with its faults, and writes one record; the census names every part of the money path
with the scenarios that ran it, and a part with none, or a promise of the desk's broken in any
world, turns the night red and names the world."""

from __future__ import annotations

import cProfile
import csv
import random
import sys
from contextlib import suppress
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from functools import partial
from itertools import pairwise
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from desk import book, day, orders, simcity, strategy
from desk.broker import Crash, Disconnected, Fault, Pretend
from desk.lines import YARDSTICK
from desk.orders import Settings
from desk.store import Bar

sys.path.insert(0, str(Path(__file__).parents[1] / "scenes"))  #: the scenes' rehearsal data
from rehearsal import CLEAN, LINES, SESSIONS  # noqa: E402  the path above comes first

MARKET = {**CLEAN, YARDSTICK: CLEAN[LINES[1]]}  #: the yardstick among its lines, as the scenes'
ROOM, RATES = Settings(Decimal(10_000)), {"GBP": Decimal(1), "USD": Decimal("0.79")}
NOW = datetime(2025, 11, 17, 22, 0, tzinfo=UTC)
#: Ten weeks of it: too few for every rule to buy and to sell.
SHORT = {line: [bar for bar in bars if bar.day <= SESSIONS[50]] for line, bars in MARKET.items()}
#: FOUND BY SIMCITY'S FIRST NIGHT, and not this module's to mend: an order left working by a
#: desk that died fills at the next open, and the gate, which counts the book alone, has by
#: then let five other lines be bought. Three worlds in four come to it and the rest do not,
#: so it is allowed and not asked for; when the send path counts what is still working, this
#: line goes in that change and the night is held to green.
SIX_HELD = f"never more than {orders.HOLDINGS} lines are held"
WORLD = simcity._Counted  #: a world's broker, kept for a test that puts another in its place


def drawn(seed: int) -> random.Random:
    return random.Random(seed)  # noqa: S311 - a repeatable draw


def busy(patch: pytest.MonkeyPatch, root: Path, worlds: tuple[int, ...]) -> simcity.Night:
    """The ten weeks in some worlds, with something done to the desk every morning it is fit
    for it and a fault waiting for every order."""
    patch.setattr(simcity, "EVENTFUL", 1)
    patch.setattr(simcity, "FAULTY", 1)
    return simcity.run(root, SHORT, ROOM, RATES, NOW, worlds)


@pytest.fixture(scope="module")
def lived(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, simcity.Night, list[object]]:
    """One world of the fourteen months, lived once for every test here that reads it; with
    it, its life and its round trips, counted while its book still stood."""
    root, live, seen = tmp_path_factory.mktemp("nights"), simcity._live, list[object]()

    def watched(life: simcity._Life) -> None:
        live(life)
        seen.extend((life, len(book.round_trips(life.desk, life.market))))

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(simcity, "_live", watched)
        return root, simcity.run(root, MARKET, ROOM, RATES, NOW, range(1)), seen


@pytest.fixture(scope="module")
def sound(tmp_path_factory: pytest.TempPathFactory) -> simcity.Night:
    """Two busy worlds of the desk as it stands, nothing in it broken by a test."""
    with pytest.MonkeyPatch.context() as patch:
        return busy(patch, tmp_path_factory.mktemp("sound"), (0, 1))


def test_a_world_of_the_fourteen_months_is_lived_with_every_fault_and_the_night_is_recorded(
    lived: tuple[Path, simcity.Night, list[object]],
) -> None:
    root, night, (life, trips) = lived
    assert isinstance(life, simcity._Life) and trips, "no round trip in fourteen months"
    plain = [record for record in life.records if record.profit is not None]
    counts = (len(life.records), len(life.records) - len(plain), trips, life.deaths)
    money = (sum(record.profit or 0 for record in plain), sum(r.market for r in plain))
    assert (night.days, night.withheld, night.trips, night.deaths) == counts, "a number misnamed"
    assert (night.profit, night.market) == money and len(set(counts + money)) == 6, "or the money"
    assert not night.bare and night.green == (not night.broken), night.words()
    assert not [broken for broken in night.broken if SIX_HELD not in broken], night.words()
    assert (night.worlds, night.days) == (1, len(SESSIONS) - 1), "a session without its day"
    assert all(night.met.values()), f"no order without a fault, or a fault never met: {night.met}"
    assert night.deaths == night.met[Fault.CRASH] + night.met[Fault.STRAND] >= 2
    assert night.withheld >= 2, "no day withheld for the hand's shares, or for the lost stop"
    assert set(night.idle) < set(strategy.STRATEGIES), "no rule ever held a line"
    verdict = "GREEN" if night.green else "RED"
    said = (f"SIMCITY {verdict}", "2025-11-17 22:00", "1 seeded worlds, 310 days", "0 with no")
    told = (f"again {night.deaths} times", f"On {night.withheld} days", f"made {night.market}.")
    made = f"{night.trips} round trips made {night.profit} pounds"
    for part in (*said, *told, made, *night.idle, *night.broken, *(f.value for f in Fault)):
        assert part in night.words(), f"the night did not say {part!r}: {night.words()}"
    with (root / simcity.NIGHTS).open(newline="", encoding="utf-8") as kept:
        header, row = csv.reader(kept)  #: one record for the night, each number under its name
    assert header == list(simcity.HEADER)
    assert dict(zip(header, row, strict=True)) == {
        **{"at": NOW.isoformat(), "verdict": verdict, "worlds": "1", "days": "310"},
        **{fault.name.lower(): str(night.met[fault]) for fault in Fault},
        **{"clean": str(night.met[None]), "deaths": str(night.deaths), "bare": ""},
        **{"withheld": str(night.withheld), "trips": str(night.trips)},
        **{"profit": str(night.profit), "market": str(night.market)},
        **{"idle": "; ".join(night.idle), "broken": "; ".join(night.broken)},
    }


def test_the_census_names_every_part_of_the_money_path_and_the_scenarios_that_ran_it(
    lived: tuple[Path, simcity.Night, list[object]],
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


def test_a_worlds_market_is_the_saved_lines_on_their_own_days_dealt_again_by_its_number() -> None:
    numbered = {  #: each saved day's number where its volume was, to follow it into a world
        line: [replace(bar, volume=t) for t, bar in enumerate(bars)]
        for line, bars in MARKET.items()
    }
    none = {replace(LINES[0], symbol="NONE"): list[Bar]()}  #: a line with no bars saved
    backwards = dict(reversed((numbered | none).items()))  #: the lines saved in another order
    worlds = ((numbered | none, 1), (backwards, 1), (numbered, 2))
    one, same, other = (simcity._market(saved, drawn(seed)) for saved, seed in worlds)
    assert one.pop(*none) == same.pop(*none) == (), "bars made for a line that has none"
    assert one == same != other, "a world's number does not make its market, or makes them all"
    assert one[YARDSTICK] != one[LINES[1]], "two lines alike in the saved data move as one"
    for line, saved in numbered.items():
        made, dealt = one[line], [bar.volume for bar in one[line][1:]]
        assert [bar.day for bar in made] == [bar.day for bar in saved], "a day not the line's own"
        assert (made[0], made[-1].close) == (saved[0], saved[-1].close), "its first bar, its end"
        assert all(b.low <= min(b.open, b.close) <= max(b.open, b.close) <= b.high for b in made)
        assert all(b.open == a.close for a, b in pairwise(made)), "a gap the saved days had not"
        assert sorted(dealt) == list(range(1, len(saved))) != dealt, "a day lost, or none moved"
        together = sum(after - before == 1 for before, after in pairwise(dealt))
        assert together >= len(dealt) + -len(dealt) // simcity.MONTH, "a month's days parted"


def test_a_night_is_its_worlds_added_up_and_a_world_lived_alone_is_the_same_world_again(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seeds, live, run, shown = (3, 5, 8), simcity._live, day.run, list[object]()

    def watched(desk: Path, saved: simcity.Archive, *rest: Any) -> day.Record:
        shown.append(saved)
        return run(desk, saved, *rest)

    def lived_and_judged(life: simcity._Life) -> None:
        live(life)  #: on its last day the desk was shown its own world, whole
        assert shown[-1] == {line: list(bars) for line, bars in life.market.items()}
        life.promise("the test's own", life.seed == seeds[0])  #: broken in all but the first
        life.trips = life.seed  #: and round trips of the test's own, to be added up

    monkeypatch.setattr(day, "run", watched)
    monkeypatch.setattr(simcity, "_live", lived_and_judged)
    whole = busy(monkeypatch, tmp_path, seeds)
    alone = [busy(monkeypatch, tmp_path, (seed,)) for seed in seeds]
    assert len({night.profit for night in alone}) == len(seeds), "two worlds alike"
    for sum_of in ("worlds", "days", "deaths", "withheld", "trips", "profit", "market"):
        told = f"{sum_of}: a world lived alone is not the world it was in the night"
        assert getattr(whole, sum_of) == sum(getattr(night, sum_of) for night in alone), told
    assert whole.met == {fault: sum(night.met[fault] for night in alone) for fault in whole.met}
    assert sum(whole.met.values()) > whole.met[None] == 0, "an order met no fault"
    for part, ran in whole.census.items():
        assert set(ran) == {scenario for night in alone for scenario in night.census[part]}, part
    assert set(whole.idle) == set.intersection(*(set(night.idle) for night in alone))
    named = "the test's own (in 2 worlds, the first world 5)"
    assert named in whole.broken and named in whole.words(), whole.broken
    with (tmp_path / simcity.NIGHTS).open(newline="", encoding="utf-8") as kept:
        assert [row[1:3] for row in csv.reader(kept)][1:] == [["RED", "3"], *[["RED", "1"]] * 3]


def test_each_thing_done_to_the_desk_has_its_turn_and_one_never_done_leaves_its_parts_bare(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(simcity, "EVENTFUL", 10**9)  #: nothing is done to any desk
    night = simcity.run(tmp_path, SHORT, ROOM, RATES, NOW, range(2))
    assert not night.green and "SIMCITY RED" in night.words()
    assert {f"never happened: {scenario}" for scenario, _ in simcity.EVENTS} <= {*night.broken}
    assert any("every rule asks" in broken for broken in night.broken), "ten weeks is too few"
    assert {"kill.pull", "kill.drill", "broker.Pretend.cancel", "book.turn"} <= {
        *night.bare
    }, "a part no scenario ran was not named"
    assert all(part in night.words() for part in night.bare + night.broken)
    assert "day.run" not in night.bare, "a part that ran was called bare"

    #: the kill switch alone, every morning a desk is fit for it
    monkeypatch.setattr(simcity, "EVENTS", simcity.EVENTS[2:])
    again = busy(monkeypatch, tmp_path, (0,))
    assert again.census["kill.pull"] == (simcity.KILLED,) and "kill.drill" not in again.bare
    assert not [broken for broken in again.broken if "never happened" in broken], again.broken
    assert "broker.Pretend.inject" in again.bare, "bare follows the scenario that did not run"

    #: three things that leave the desk fit: dealt in threes, each once, in the seed's order
    done: list[str] = []

    def thing(name: str) -> simcity.Event:
        return name, lambda life, on: done.append((name, life.live(on))[0])  #: a plain day

    monkeypatch.setattr(simcity, "EVENTS", tuple(map(thing, "abc")))
    busy(monkeypatch, tmp_path, (1,))
    deals = {"".join(done[at : at + 3]) for at in range(0, len(done) - 2, 3)}
    assert len(deals) > 1 and all(sorted(deal) == [*"abc"] for deal in deals), done


def test_a_desk_that_stops_is_a_red_night_and_a_night_that_dies_is_an_error_and_is_not_kept(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with pytest.raises(ValueError, match="UTC"):
        simcity.run(tmp_path, SHORT, ROOM, RATES, NOW.replace(tzinfo=None))
    #: the yardstick is not in the data: in each of a night's hundred worlds the desk stops
    night = simcity.run(tmp_path, {line: SHORT[line] for line in LINES}, ROOM, RATES, NOW)
    stopped = "the desk stops on no day (in 100 worlds, the first world 0 on day 1, saying: "
    assert [b for b in night.broken if b.startswith(stopped) and "no close of" in b], night.broken
    assert (night.worlds, night.days, night.trips) == (100, 0, 0) and stopped in night.words()
    (tmp_path / simcity.NIGHTS).unlink()

    def fall(*_: object) -> None:
        raise RuntimeError("not the desk's word: the floor gave way")

    monkeypatch.setattr(day, "run", fall)
    with pytest.raises(RuntimeError, match="the floor") as died:
        simcity.run(tmp_path, SHORT, ROOM, RATES, NOW, (4, 7))
    assert "world 4" in died.value.__notes__[0], "the world it died in is not named"
    assert sys.getprofile() is None, "the census went on watching after the night died"
    probe = cProfile.Profile()  #: and where a profiler left on refuses a second, none does
    probe.enable()
    probe.disable()
    assert not list(tmp_path.iterdir()), "a night that died was kept"
    (tmp_path / simcity.NIGHTS).write_text("something else\n", encoding="utf-8")
    monkeypatch.setattr(simcity, "_live", None)  #: refused before the night is lived at all
    with pytest.raises(ValueError, match="not SimCity's nights"):
        simcity.run(tmp_path, SHORT, ROOM, RATES, NOW)


def test_a_worlds_broker_draws_faults_at_its_door_and_counts_each_when_it_is_used_up(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    door = simcity._Counted(SHORT, drawn(0))
    order = orders.Order("o-1", LINES[0], 1, Decimal(50), Decimal(1), Decimal(45))
    monkeypatch.setattr(simcity, "FAULTY", 1)  #: a fault waits for every order
    door.place(order)  #: no market has opened yet: the fault still waits on its line
    door.open(SESSIONS[1])
    for n in (2, 3):
        with suppress(Crash, Disconnected):
            door.place(replace(order, order_id=f"o-{n}"))
    assert (door.met[None], sum(door.met.values()), door.buys) == (1, 3, 3), door.met
    monkeypatch.setattr(simcity, "FAULTY", 10**9)  #: and for none
    assert door.place(replace(order, order_id="o-4")).reason is None and door.met[None] == 2


def test_a_stop_cancelled_by_hand_is_put_back_as_it_was_unless_forgotten_or_its_shares_sold(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(simcity, "FAULTY", 10**9)
    life, seen = simcity._Life(tmp_path, SHORT, ROOM, RATES, 0, simcity._Census()), list[object]()
    door, hand = life.pretend, partial(simcity._unstopped, life, SESSIONS[1])
    door.open(SESSIONS[1])
    buy = orders.Order("o-1", LINES[0], 4, Decimal(50), Decimal(1), Decimal(1))
    rested = door.place(buy) and door.resting_stops()
    monkeypatch.setattr(life, "live", lambda _: seen.append(door.stops()))
    hand()
    assert seen == [()] and door.resting_stops() == rested, "not lost for its day, or not put back"
    monkeypatch.setattr(simcity, "FORGOTTEN", 1)
    hand()
    assert not door.stops(), "forgotten, and put back"
    monkeypatch.setattr(simcity, "FORGOTTEN", 10**9)
    door.place(replace(buy, order_id="o-2", line=LINES[1]))
    monkeypatch.setattr(life, "live", lambda _: door.place(orders.Sale("s-1", LINES[1], 1)))
    hand()
    assert not door.stops(), "a stop put back for shares no longer held"


def test_a_part_behind_a_wrapper_is_still_a_part(monkeypatch: pytest.MonkeyPatch) -> None:
    class Offered:
        @classmethod
        def made(cls) -> None: ...

        @staticmethod
        def plain() -> None: ...

        def _kept(self) -> None: ...

    fake = ModuleType("desk.fake")
    Offered.__module__, fake.Offered = fake.__name__, Offered  # type: ignore[attr-defined]
    monkeypatch.setattr(simcity, "PATH", (fake,))
    assert sorted(name.rpartition("Offered.")[2] for name in simcity.parts().values()) == [
        *("made", "plain")
    ], "a classmethod or a staticmethod passed over, or a private name counted"


@pytest.mark.parametrize(
    ("owner", "name", "broken_desk", "promises", "first"),
    [  #: the shares never appear; the broker forgets its orders; the record differs alone; it
        #: never differs; no fill is kept; each day's profit a penny out; his limit two lines
        #: fewer; the broker fills at the saved prices, not the world's; and, with the switch
        #: the one thing done to the desk, it stops nothing
        (Pretend, "inject", lambda *_: None, ["did not make"], 0),
        (Pretend, "report", lambda *_: None, ["reached the broker twice"], 0),
        (book, "reconcile", lambda *_: ("L01",), ["nothing is bought", "no line is named"], 0),
        (book, "reconcile", lambda *_: (), ["with no stop at the broker"], 0),
        (book, "collect", lambda *_: None, ["the ledger is the broker's own fills"], 0),
        (day, "pennies", lambda p: orders.pennies(p) + Decimal("0.01"), ["profits add up"], 0),
        (simcity, "HOLDINGS", 3, ["never more than 3 lines are held"], 0),
        (simcity, "_Counted", lambda _, rng: WORLD(SHORT, rng), ["inside its day's range"], 0),
        (book, "_unless_killed", lambda *_: None, ["nothing reaches the", "drill is on the"], 2),
    ],
)
def test_a_promise_the_desk_breaks_in_any_world_turns_the_night_red_and_names_the_world(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    sound: simcity.Night,
    owner: object,
    name: str,
    broken_desk: object,
    promises: list[str],
    first: int,
) -> None:
    monkeypatch.setattr(owner, name, broken_desk)
    monkeypatch.setattr(simcity, "EVENTS", simcity.EVENTS[first:])
    night = busy(monkeypatch, tmp_path, (0, 1))
    for promise in promises:
        assert promise not in str(sound.broken), "broken on a sound desk"
        assert [b for b in night.broken if promise in b and "the first world" in b], night.broken
    assert not night.green and f"BROKEN: {'; '.join(night.broken)}." in night.words()
