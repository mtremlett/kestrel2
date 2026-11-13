"""emergency: an emergency, a crash and a black swan are each a measured fall set in advance,
each with its action; a fall is read in its market's terms, and the gravest it meets is said."""

from __future__ import annotations

from decimal import Decimal

import pytest

from desk import emergency
from desk.emergency import Action, Level
from desk.lines import YARDSTICK, Line
from desk.orders import STOP_FALL

PLAIN, TRIPLE = Line("ONE", "US", "USD", 1), Line("THREE", "LSE", "GBP", 3)
CALM = [Decimal(100)] * emergency.MONTH


def _fall(line: Line, day: str, high: str | None = None) -> emergency.Fall:
    return emergency.Fall(line, Decimal(day), Decimal(high or day))


def test_each_of_the_three_is_defined_in_numbers_set_in_advance_with_its_action() -> None:
    """The definitions themselves: a number changed here is a ruling changed (EMG-01)."""
    assert [(level.name, *vars(level.value).values()) for level in Level] == [
        ("EMERGENCY", False, Decimal("0.10"), None, Action.PARK),
        ("CRASH", True, Decimal("0.05"), Decimal("0.15"), Action.HALT),
        ("BLACK_SWAN", True, Decimal("0.13"), Decimal("0.35"), Action.CASH),
    ]
    assert Level.EMERGENCY.value.day is STOP_FALL, "a shock is the stop's whole fall in one day"
    assert emergency.MONTH == 20
    told = [action.value for action in Action]
    assert "of that line" in told[0] and "on any line" in told[1], told
    assert "sells every position" in told[2] and "until he says so" in told[2], told
    assert all("stop rests at the broker" in words for words in told[:2]), told


def test_a_fall_is_measured_in_its_markets_terms_from_the_last_close_and_the_months_high() -> None:
    climb = [Decimal(n) for n in (200, *range(81, 101))]  #: 200 is twenty-one sessions old
    assert emergency.measure(PLAIN, climb, Decimal(95)) == _fall(PLAIN, "0.05")
    dipped = [*climb, Decimal(90)]  #: the month's high is the close of 100, not the last close
    assert emergency.measure(PLAIN, dipped, Decimal(81)) == _fall(PLAIN, "0.1", "0.19")
    assert emergency.measure(TRIPLE, CALM, Decimal(85)) == _fall(TRIPLE, "0.05"), "a third"
    assert emergency.measure(PLAIN, CALM, Decimal(104)) == _fall(PLAIN, "0"), "a rise is no fall"
    assert emergency.measure(PLAIN, [Decimal(50)], Decimal(40)) == _fall(PLAIN, "0.2"), "new line"
    for closes, price in (([], 95), (CALM, 0), ([Decimal(0)], 95), ([*CALM, Decimal(-1)], 95)):
        with pytest.raises(ValueError, match="ONE: no fall .* to a price of"):
            emergency.measure(PLAIN, closes, Decimal(price))
    for day, high in (("-0.01", "0.2"), ("0.2", "0.1"), ("0.2", "1")):
        with pytest.raises(ValueError, match="ONE: no line has fallen"):
            _fall(PLAIN, day, high)


@pytest.mark.parametrize(
    ("line", "day", "high", "level"),
    [
        (YARDSTICK, "0.0499", "0.1499", None),
        (YARDSTICK, "0.05", "0.05", Level.CRASH),
        (YARDSTICK, "0", "0.15", Level.CRASH),  #: no fall today: still a crash while it lasts
        (YARDSTICK, "0.1299", "0.3499", Level.CRASH),
        (YARDSTICK, "0.13", "0.13", Level.BLACK_SWAN),
        (YARDSTICK, "0.01", "0.35", Level.BLACK_SWAN),
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
    market, shock = _fall(YARDSTICK, "0.062", "0.171"), _fall(TRIPLE, "0.12")
    quiet, swan = _fall(PLAIN, "0.03", "0.4"), _fall(YARDSTICK, "0.14")
    assert emergency.alarms([quiet, shock, market]) == (market, shock)
    assert emergency.alarms([shock, market, swan, quiet]) == (swan, market, shock)
    assert emergency.alarms([quiet]) == ()
    said = market.words()
    for part in ("CRASH", "VUAG", "6.2%", "17.1%", "5% in a day", "15% below", "on any line"):
        assert part in said, f"the desk did not say {part!r}: {said}"
    said = shock.words()
    for part in ("EMERGENCY", "THREE", "12.0%", "3 times", "10% in a day", "of that line"):
        assert part in said, f"the desk did not say {part!r}: {said}"
    assert "BLACK SWAN" in swan.words() and "13% in a day, or 35% below" in swan.words()
    assert "none of the three" in quiet.words() and "ONE" in quiet.words(), quiet.words()
