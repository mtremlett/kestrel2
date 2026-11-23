"""A missing daily bar filled from the broker, else the archive, once; else named."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from io import BytesIO
from pathlib import Path

import pytest

from desk import backfill, bars, history, keeper, paper, venues
from desk.bars import Source
from desk.lines import LINES, POUND
from desk.store import Bar, Refused

SPY = next(line for line in LINES if line.symbol == "SPY")
ISF = next(line for line in LINES if line.symbol == "ISF")
FRIDAY, LOST = date(2026, 11, 13), date(2025, 10, 24)
TODAY = date(2026, 11, 17)


def bar(day: date, close: str) -> Bar:
    price = Decimal(close)
    return Bar(day, price, price + 1, price - 1, price, 1000)


def test_the_broker_first_the_archive_for_the_rest_a_second_run_nothing(tmp_path: Path) -> None:
    path = tmp_path / bars.LIVE
    with bars.writing(path) as held:
        held.days(SPY, [bar(date(2026, 11, 12), "600")])
        held.days(ISF, [bar(date(2025, 10, 23), "10")])
    asked: list[str] = []

    def broker(_line: object, day: date) -> list[Bar] | Refused:
        asked.append("b")
        return [bar(FRIDAY, "601")] if day == FRIDAY else Refused("the broker's 200: no data")

    def archived(_line: object, day: date) -> list[Bar] | Refused:
        asked.append("a")
        return [bar(LOST, "10")] if day == LOST else Refused("empty")

    wanted = [(SPY, FRIDAY), (ISF, LOST)]
    wrote, named = backfill.fill(path, wanted, backfill.ordered(broker, archived), TODAY)
    assert wrote == [f"SPY {FRIDAY}: IBKR paper", f"ISF {LOST}: archive, backfilled"] and not named
    assert bars.sources(path, SPY, bars.DAILY)[Source.IBKR] == 1
    assert [b.day for b in bars.daily(path, ISF)] == [date(2025, 10, 23), LOST]
    asked.clear()
    assert (
        backfill.fill(path, wanted, backfill.ordered(broker, archived), TODAY) == ([], [])
        and not asked
    )


def test_a_day_neither_source_gives_is_named_and_never_filled(tmp_path: Path) -> None:
    path = tmp_path / bars.LIVE
    with bars.writing(path) as held:
        held.days(ISF, [bar(date(2025, 10, 23), "10")])
    nothing = Refused("no bar")
    wrote, named = backfill.fill(
        path, [(ISF, LOST)], backfill.ordered(lambda *_: nothing, lambda *_: []), TODAY
    )
    assert wrote == [] and len(named) == 1 and "no source gives it" in named[0]
    assert "no bar" in named[0] and "gave no bar" in named[0]
    assert [b.day for b in bars.daily(path, ISF)] == [date(2025, 10, 23)]


def test_a_hole_among_years_of_bars_is_judged_beside_both_sides_as_of_today(tmp_path: Path) -> None:
    path = tmp_path / bars.LIVE
    days = [
        d for d in venues.sessions(ISF.venue, date(2022, 1, 3), date(2026, 11, 16)) if d != LOST
    ]
    with bars.writing(path) as held:
        held.days(ISF, [bar(d, str(10 + d.day % 3)) for d in days])
    refusal = backfill.fill(
        path, [(ISF, LOST)], backfill.ordered(lambda *_: [bar(LOST, "1100")], lambda *_: []), TODAY
    )
    assert not refusal[0] and "out of line" in refusal[1][0]
    wrote, named = backfill.fill(
        path, [(ISF, LOST)], backfill.ordered(lambda *_: [bar(LOST, "11")], lambda *_: []), TODAY
    )
    assert wrote == [f"ISF {LOST}: IBKR paper"] and not named
    assert [b.day for b in bars.daily(path, ISF)] == sorted([*days, LOST])


def test_the_pounds_gaps_are_filled_from_the_fed_and_a_day_it_lacks_is_named(
    tmp_path: Path,
) -> None:
    path = tmp_path / bars.LIVE
    with bars.writing(path) as held:
        held.days(POUND, [bar(date(2020, 1, 6), "1")])
    table = "d,r\n2020-01-07,1.31\n2020-01-08,\n2020-01-09,1.32\n"
    wrote, named = backfill.fill_pound(path, table, date(2020, 1, 10))
    assert wrote == ["2020-01-07: 1.31", "2020-01-09: 1.32"] and named == ["2020-01-08"]
    assert bars.sources(path, POUND, bars.DAILY)[Source.FED_NOON] == 2
    assert backfill.fill_pound(path, table, date(2020, 1, 10))[0] == []


def test_the_brokers_pence_are_turned_into_pounds_on_entry() -> None:
    pence = Bar(FRIDAY, Decimal("7791"), Decimal("7823"), Decimal("7626"), Decimal("7716"), 9)
    pounds = Bar(FRIDAY, Decimal("77.91"), Decimal("78.23"), Decimal("76.26"), Decimal("77.16"), 9)
    assert backfill.in_currency([pence], 100) == [pounds]
    assert backfill.in_currency([pounds], 1) == [pounds]
    assert backfill.in_currency(Refused("no data"), 100) == Refused("no data")


def test_the_brokers_ask_reaches_the_gateway_as_the_history_reader_through_its_own_door(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    doors: list[paper.Door] = []

    def start(_wire: object, _send: object, door: paper.Door) -> int:
        doors.append(door)
        raise ConnectionRefusedError("the fake gateway has heard the knock")

    monkeypatch.setattr(paper, "dial", lambda talk: talk(BytesIO(), lambda _b: None))
    monkeypatch.setattr(paper, "start", start)
    ask = backfill._broker(tmp_path, datetime(2026, 11, 17, 12, tzinfo=UTC))
    with pytest.raises(ConnectionRefusedError):
        ask(LINES[0], date(2026, 11, 13))
    assert doors == [paper.Door(history.CLIENT)]


def test_a_day_the_broker_lacks_is_taken_from_local_stooq_before_the_archive(
    tmp_path: Path,
) -> None:
    path = tmp_path / bars.LIVE
    with bars.writing(path) as held:
        held.days(ISF, [bar(date(2025, 10, 23), "10")])
    asks = backfill.ordered(
        lambda *_: Refused("no data"),
        lambda *_: pytest.fail("archive asked"),
        lambda *_: [bar(LOST, "10")],
    )
    wrote, named = backfill.fill(path, [(ISF, LOST)], asks, TODAY)
    assert wrote == [f"ISF {LOST}: old desk: stooq_store daily rows"] and not named


def test_the_pound_command_fills_from_the_fed_and_exits_1_on_a_named_day(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / keeper.HOT
    with bars.writing(path) as held:
        held.days(POUND, [bar(date(2020, 1, 6), "1")])
    monkeypatch.setattr(backfill, "_fed", lambda: "d,r\n2020-01-07,1.31\n2020-01-08,\n")
    now = datetime(2020, 1, 10, 6, tzinfo=UTC)
    assert backfill.main(tmp_path, now, ["POUND"]) == 1
    assert [b.day for b in bars.daily(path, POUND)] == [date(2020, 1, 6), date(2020, 1, 7)]
