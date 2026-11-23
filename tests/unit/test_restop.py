"""restop: the stop is set from the fill (R-RUNNER-220): a buy sized on the signal close leaves
its stop there, and the next step moves it to 10% under the fill's own price, once."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from desk import book, day, restop, venues
from desk.broker import Pretend
from desk.lines import Line
from desk.orders import Settings
from desk.store import Bar

DAYS = venues.sessions("LSE", date(2025, 1, 6), date(2025, 2, 28))[:23]
LINE = Line("A", "LSE", "GBP", 1)
ROOM, POUNDS = Settings(Decimal(10_000)), {"GBP": Decimal(1)}


def _bars(open_: str) -> tuple[Bar, ...]:
    """Twenty flat days, a close of 9 that Bollinger buys, then a morning opening at open_."""
    flat = [Bar(on, *(Decimal(10),) * 4, 10**7) for on in DAYS[:20]]
    signal = Bar(DAYS[20], *(Decimal(9),) * 4, 10**7)
    opened = Decimal(open_)
    return (
        *flat,
        signal,
        Bar(DAYS[21], opened, opened + 1, opened - Decimal("0.2"), opened, 10**7),
    )


@pytest.mark.parametrize(
    ("open_", "first", "due"), [("8.5", "8.1", "7.65"), ("9.5", "8.1", "8.55"), ("9", "8.1", None)]
)
def test_a_fills_stop_rests_ten_percent_under_the_fill_and_is_moved_once(
    tmp_path: Path, open_: str, first: str, due: str | None
) -> None:
    bars = _bars(open_)
    broker = Pretend({LINE: bars}, {})
    broker.open(DAYS[21])
    before = {LINE: bars[:21]}
    day.trade(tmp_path, before, broker, ROOM, DAYS[21], POUNDS)
    restop.move(tmp_path, broker, before)
    level = Decimal(due or first)
    assert broker.resting_stops()["A"][1] == level and book.positions(tmp_path)["A"] > 0
    assert list(book.levels(tmp_path).values()) == [level], "the level is kept as it was set"
    sends = []
    broker.restop = lambda *a: sends.append(a)  # type: ignore[method-assign]
    restop.move(tmp_path, broker, before)  #: the step run again
    assert sends == [], "a stop already under its fill is not moved again"


def test_a_thin_line_is_bought_to_one_percent_of_its_traded_pounds(tmp_path: Path) -> None:
    """SIZ-10 through the day: bars trading 100 shares a day cap the buy at 1% of ~20,000 pounds."""
    thin = tuple(Bar(b.day, b.open, b.high, b.low, b.close, 100) for b in _bars("9"))
    broker = Pretend({LINE: thin}, {})
    broker.open(DAYS[21])
    day.trade(tmp_path, {LINE: thin[:21]}, broker, ROOM, DAYS[21], POUNDS)
    assert 0 < book.positions(tmp_path)["A"] * 9 <= Decimal("0.01") * 20_000
