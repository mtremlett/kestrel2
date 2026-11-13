"""emergency: an emergency, a crash and a black swan are each a measured fall set in advance,
each with what the desk does; a fall is read from dated bars, in its market's terms, and the
gravest it meets is said. What cannot be read is unread, never calm."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal

import pytest

from desk import emergency, venues
from desk.emergency import Definition, Level, Response, Unread
from desk.lines import YARDSTICK, Line
from desk.orders import STOP_FALL
from desk.store import Bar

PLAIN, TRIPLE = Line("ONE", "US", "USD", 1), Line("THREE", "LSE", "GBP", 3)
DAY, CALM = date(2025, 11, 12), [100] * emergency.MONTH


def _bar(on: date, close: int) -> Bar:
    return Bar(on, Decimal(close), Decimal(close), Decimal(close), Decimal(close), 1)


def _bars(line: Line, closes: Sequence[int]) -> list[Bar]:
    """Daily bars closing at closes, on the line's sessions up to the one before DAY."""
    days = venues.sessions(line.venue, DAY - timedelta(days=60), DAY)[-len(closes) - 1 : -1]
    return [_bar(on, close) for on, close in zip(days, closes, strict=True)]


def _fall(line: Line, day: str, high: str | None = None) -> emergency.Fall:
    return emergency.Fall(line, DAY, Decimal(day), Decimal(high or day))


def test_each_of_the_three_is_defined_in_numbers_set_in_advance_with_what_the_desk_does() -> None:
    """The definitions themselves: a number changed here is a ruling changed (EMG-01)."""
    assert [(level.name, *vars(level.value).values()) for level in Level] == [
        ("EMERGENCY", False, Decimal("0.10"), None, Response.PARK),
        ("CRASH", True, Decimal("0.04"), Decimal("0.12"), Response.HALT),
        ("BLACK_SWAN", True, Decimal("0.10"), Decimal("0.30"), Response.CASH),
    ]
    assert Level.EMERGENCY.value.day is STOP_FALL, "a shock is the stop's whole fall in one day"
    assert emergency.MONTH == 20
    odd = Definition(True, Decimal("0.125"), Decimal("1"), Response.HALT)
    assert odd.words() == "the market (VUAG) down 12.5% in a day, or 100% below its month's high"
    for day, high in (("0", None), ("1", None), ("0.2", "0.2"), ("0.2", "1.01"), ("-0.1", "0.2")):
        with pytest.raises(ValueError, match="no emergency is a fall of"):
            Definition(False, Decimal(day), Decimal(high) if high else None, Response.PARK)


def test_a_fall_is_measured_from_the_close_before_and_the_months_high_or_is_unread() -> None:
    closes = [200, 100, 100, 160, *[100] * 16, 125]  #: 200 is a day too old; the high is mid-month
    bars = _bars(PLAIN, closes)
    assert emergency.measure(PLAIN, bars, DAY, Decimal(100)) == _fall(PLAIN, "0.2", "0.375")
    today = [*bars, _bar(DAY, 100)]  #: the day's own bar is no close to fall from
    assert emergency.measure(PLAIN, today, DAY, Decimal(100)).day == Decimal("0.2")
    assert emergency.measure(TRIPLE, _bars(TRIPLE, CALM), DAY, Decimal(70)) == _fall(TRIPLE, "0.3")
    assert emergency.measure(PLAIN, bars, DAY, Decimal(130)).day == 0, "a rise is no fall"
    shut = replace(PLAIN, suspended=frozenset({bars[-1].day}))  #: its own session before is older
    assert emergency.measure(shut, bars[:-1], DAY, Decimal(90)) == _fall(shut, "0.1", "0.55")
    for unread, on, price in (
        (bars[-19:], DAY, "100"),  #: a day short of the month: a slow crash could hide behind it
        (bars[:-1], DAY, "100"),  #: the last close a day stale: two days' fall read as one
        (bars, DAY + timedelta(days=3), "100"),  #: a Saturday is no session
        (bars, DAY, "0"),
        (bars, DAY, "NaN"),
        (bars, DAY, "Infinity"),
    ):
        with pytest.raises(Unread, match="ONE: no fall is read on 2025-11-1.* at a price of"):
            emergency.measure(PLAIN, unread, on, Decimal(price))
    for day, high in (("-0.01", "0.2"), ("0.2", "0.1"), ("0.2", "1")):
        with pytest.raises(ValueError, match="ONE: no line has fallen"):
            _fall(PLAIN, day, high)
    with pytest.raises(ValueError, match="is not the yardstick as the master records it"):
        _fall(Line(YARDSTICK.symbol, "LSE", "GBP", 3), "0.3")


@pytest.mark.parametrize(
    ("line", "day", "high", "level"),
    [
        (YARDSTICK, "0.0399", "0.1199", None),
        (YARDSTICK, "0.04", "0.04", Level.CRASH),
        (YARDSTICK, "0", "0.12", Level.CRASH),  #: no fall today: a crash while the month says so
        (YARDSTICK, "0.0999", "0.2999", Level.CRASH),
        (YARDSTICK, "0.10", "0.10", Level.BLACK_SWAN),
        (YARDSTICK, "0.01", "0.30", Level.BLACK_SWAN),
        (PLAIN, "0.0999", "0.9", None),  #: far below its high is the rules' business
        (PLAIN, "0.10", "0.10", Level.EMERGENCY),
        (PLAIN, "0.60", "0.60", Level.EMERGENCY),  #: one line is never the market
        (TRIPLE, "0.2999", "0.2999", None),  #: its market has fallen a third as far
        (TRIPLE, "0.30", "0.30", Level.EMERGENCY),
    ],
)
def test_a_fall_is_the_gravest_of_the_three_it_meets(
    line: Line, day: str, high: str, level: Level | None
) -> None:
    assert _fall(line, day, high).level is level


def test_the_alarms_are_one_sessions_falls_that_are_one_of_the_three_gravest_first() -> None:
    market = emergency.measure(YARDSTICK, _bars(YARDSTICK, [110, *CALM[1:]]), DAY, Decimal("93.8"))
    shock = emergency.measure(TRIPLE, _bars(TRIPLE, CALM), DAY, Decimal(70))
    quiet, swan, calm = (
        _fall(PLAIN, "0.03", "0.4"),
        _fall(YARDSTICK, "0.14"),
        _fall(YARDSTICK, "0.0009", "0.11996"),
    )
    assert emergency.alarms([quiet, shock, market]) == (market, shock)
    assert emergency.alarms(iter([shock, swan, quiet])) == (swan, shock)
    assert emergency.alarms([quiet, calm]) == ()
    for unread in (
        [quiet, shock],
        [market, quiet, swan],  #: two readings of the market that disagree
        [market, replace(quiet, on=DAY - timedelta(days=1))],
    ):
        with pytest.raises(Unread, match="hold [012] readings of the market, VUAG, and [12] days"):
            emergency.alarms(unread)
    assert market.words() == (
        "CRASH, which is the market (VUAG) down 4% in a day, or 12% below its month's high: VUAG,"
        " on 2025-11-12, is 14.7% below its month's high and 6.2% below its last close. The desk"
        " buys nothing on any line until the market ends a day clear of a crash, and sells nothing"
        " because of it: the rules and the stops sell as ever."
    )
    assert shock.words() == (
        "EMERGENCY, which is any one line down 10% in a day (a leveraged line: its market): THREE,"
        " on 2025-11-12, is 30.0% below its last close (its market 10.0%: it moves 3 times as far)."
        " The desk buys no more of that line until it ends a day clear of an emergency, and sells"
        " nothing because of it: the rules and the stops sell as ever."
    )
    assert swan.words() == (
        "BLACK SWAN, which is the market (VUAG) down 10% in a day, or 30% below its month's high:"
        " VUAG, on 2025-11-12, is 14.0% below its month's high and 14.0% below its last close. The"
        " desk sells every position, and buys nothing until the operator says so."
    )
    none = "none of the three emergencies."
    assert quiet.words() == f"ONE, on 2025-11-12, is 3.0% below its last close: {none}"
    assert calm.words() == (
        f"VUAG, on 2025-11-12, is 11.9% below its month's high and not below its last close: {none}"
    )
