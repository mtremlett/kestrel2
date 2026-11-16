"""A missing daily bar filled from the broker, else the archive, once; else named."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from desk import backfill, bars
from desk.bars import Source
from desk.lines import LINES
from desk.store import Bar, Refused

SPY = next(line for line in LINES if line.symbol == "SPY")
ISF = next(line for line in LINES if line.symbol == "ISF")
FRIDAY, LOST = date(2026, 11, 13), date(2025, 10, 24)


def bar(day: date, close: str) -> Bar:
    price = Decimal(close)
    return Bar(day, price, price + 1, price - 1, price, 1000)


def test_the_broker_first_the_archive_for_the_rest_a_second_run_nothing(tmp_path: Path) -> None:
    path = tmp_path / bars.LIVE
    thursday = date(2026, 11, 12)
    with bars.writing(path) as held:
        held.days(SPY, [bar(thursday, "600")])
        held.days(ISF, [bar(date(2025, 10, 23), "10")])
    asked: list[str] = []

    def broker(_line: object, day: date) -> list[Bar] | Refused:
        asked.append(f"broker {day}")
        return [bar(FRIDAY, "601")] if day == FRIDAY else Refused("the broker's 200: no data")

    def archived(_line: object, day: date) -> list[Bar] | Refused:
        asked.append(f"archive {day}")
        return [bar(LOST, "10")] if day == LOST else Refused("empty")

    wanted = [(SPY, FRIDAY), (ISF, LOST)]
    wrote, named = backfill.fill(path, wanted, broker, archived)
    assert wrote == [f"SPY {FRIDAY}: IBKR paper", f"ISF {LOST}: archive, backfilled"] and not named
    assert bars.sources(path, SPY, bars.DAILY)[Source.IBKR] == 1
    assert [b.day for b in bars.daily(path, ISF)] == [date(2025, 10, 23), LOST]
    asked.clear()
    assert backfill.fill(path, wanted, broker, archived) == ([], []) and not asked


def test_a_day_neither_source_gives_is_named_and_never_filled(tmp_path: Path) -> None:
    path = tmp_path / bars.LIVE
    with bars.writing(path) as held:
        held.days(ISF, [bar(date(2025, 10, 23), "10")])
    nothing = Refused("no bar")
    wrote, named = backfill.fill(path, [(ISF, LOST)], lambda *_: nothing, lambda *_: [])
    assert wrote == [] and len(named) == 1 and "no source gives it" in named[0]
    assert "no bar" in named[0] and "gave no bar for the day" in named[0]
    assert [b.day for b in bars.daily(path, ISF)] == [date(2025, 10, 23)]
