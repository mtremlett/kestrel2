"""emergency: an emergency, a crash and a black swan are each a measured fall set in advance,
each with its action; a fall is read in its market's terms, and the gravest it meets is said."""

from __future__ import annotations

from decimal import Decimal

import pytest

from desk import emergency
from desk.emergency import Action, Definition, Level
from desk.lines import YARDSTICK, Line
from desk.orders import STOP_FALL

PLAIN, TRIPLE = Line("ONE", "US", "USD", 1), Line("THREE", "LSE", "GBP", 3)
MARKET = Line(
    YARDSTICK.symbol, "LSE", "GBP", 1
)  #: the market by its symbol, whatever else it records
CALM = [Decimal(100)] * emergency.MONTH


def _fall(line: Line, day: str, high: str | None = None) -> emergency.Fall:
    return emergency.Fall(line, Decimal(day), Decimal(high or day))


def test_each_of_the_three_is_defined_in_numbers_set_in_advance_with_its_action() -> None:
    """The definitions themselves: a number changed here is a ruling changed (EMG-01)."""
    assert [(level.name, *vars(level.value).values()) for level in Level] == [
        ("EMERGENCY", False, Decimal("0.10"), None, Action.PARK),
        ("CRASH", True, Decimal("0.04"), Decimal("0.12"), Action.HALT),
        ("BLACK_SWAN", True, Decimal("0.10"), Decimal("0.30"), Action.CASH),
    ]
    assert Level.EMERGENCY.value.day is STOP_FALL, "a shock is the stop's whole fall in one day"
    assert emergency.MONTH == 20
    odd = Definition(True, Decimal("0.125"), Decimal("1"), Action.HALT)
    assert odd.words() == "the market down 12.5% in a day, or 100% below its month's high"
    for day, high in (("0", None), ("1", None), ("0.2", "0.2"), ("0.2", "1.01"), ("-0.1", "0.2")):
        with pytest.raises(ValueError, match="no emergency is a fall of"):
            Definition(False, Decimal(day), Decimal(high) if high else None, Action.PARK)


def test_a_fall_is_measured_in_its_markets_terms_from_the_last_close_and_the_months_high() -> None:
    month = [Decimal(200), Decimal(150), *CALM[1:]]  #: 150 opens the month; 200 is a day too old
    assert emergency.measure(PLAIN, month, Decimal(90)) == _fall(PLAIN, "0.1", "0.4")
    assert emergency.measure(TRIPLE, CALM, Decimal(85)) == _fall(TRIPLE, "0.05"), "a third"
    assert emergency.measure(PLAIN, CALM, Decimal(104)) == _fall(PLAIN, "0"), "a rise is no fall"
    nan, endless = Decimal("NaN"), Decimal("Infinity")
    for closes, price in (
        (CALM[1:], Decimal(95)),  #: a day short of the month: a slow crash could hide behind it
        (CALM, Decimal(0)),
        ([*CALM, Decimal(0)], Decimal(95)),
        ([Decimal(-1), *CALM[1:]], Decimal(95)),
        (CALM, nan),
        (CALM, endless),
        ([endless, *CALM[1:]], Decimal(95)),
    ):
        with pytest.raises(ValueError, match="ONE: no fall .* to a price of"):
            emergency.measure(PLAIN, closes, price)
    for day, high in (("-0.01", "0.2"), ("0.2", "0.1"), ("0.2", "1")):
        with pytest.raises(ValueError, match="ONE: no line has fallen"):
            _fall(PLAIN, day, high)


@pytest.mark.parametrize(
    ("line", "day", "high", "level"),
    [
        (MARKET, "0.0399", "0.1199", None),
        (MARKET, "0.04", "0.04", Level.CRASH),
        (MARKET, "0", "0.12", Level.CRASH),  #: no fall today: still a crash while the month says so
        (MARKET, "0.0999", "0.2999", Level.CRASH),
        (MARKET, "0.10", "0.10", Level.BLACK_SWAN),
        (YARDSTICK, "0.01", "0.30", Level.BLACK_SWAN),
        (PLAIN, "0.0999", "0.9", None),  #: far below its high is the rules' business
        (PLAIN, "0.10", "0.10", Level.EMERGENCY),
        (PLAIN, "0.60", "0.60", Level.EMERGENCY),  #: one line is never the market
        (TRIPLE, "0.10", "0.10", Level.EMERGENCY),
    ],
)
def test_a_fall_is_the_gravest_of_the_three_it_meets(
    line: Line, day: str, high: str, level: Level | None
) -> None:
    assert _fall(line, day, high).level is level


def test_the_alarms_are_the_falls_that_are_one_of_the_three_gravest_first_and_said() -> None:
    market, shock = _fall(MARKET, "0.062", "0.171"), _fall(TRIPLE, "0.12")
    quiet, swan, calm = (
        _fall(PLAIN, "0.03", "0.4"),
        _fall(MARKET, "0.14"),
        _fall(MARKET, "0", "0.11996"),
    )
    assert emergency.alarms([quiet, shock, market]) == (market, shock)
    assert emergency.alarms(iter([shock, market, swan, quiet])) == (swan, market, shock)
    assert emergency.alarms([quiet, calm]) == ()
    with pytest.raises(ValueError, match="the market, VUAG, is not among the 2 falls read"):
        emergency.alarms([quiet, shock])
    assert market.words() == (
        "CRASH, which is the market down 4% in a day, or 12% below its month's high: VUAG is 6.2%"
        " below its last close and 17.1% below its month's high. The desk buys nothing on any line"
        " until a session closes clear of it, and sells nothing: every holding is left to its stop."
    )
    assert shock.words() == (
        "EMERGENCY, which is any one line's market down 10% in a day: THREE is 36.0% below its"
        " last close (its market 12.0%: it moves 3 times as far). The desk buys no more of that"
        " line until a session closes clear of it, and sells nothing: a holding is left to its"
        " stop."
    )
    assert swan.words() == (
        "BLACK SWAN, which is the market down 10% in a day, or 30% below its month's high: VUAG is"
        " 14.0% below its last close and 14.0% below its month's high. The desk sells every"
        " position, and buys nothing until he says so."
    )
    assert quiet.words() == "ONE is 3.0% below its last close: none of the three emergencies."
    assert calm.words() == (
        "VUAG is not below its last close and 11.9% below its month's high: none of the three"
        " emergencies."
    )
