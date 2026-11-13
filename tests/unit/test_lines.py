"""The instrument master: the frozen lines of the operator's rulings of 13 November."""

from __future__ import annotations

from collections import Counter
from datetime import date
from decimal import Decimal

import pytest

from desk.lines import LINES, NO_TAX, STAMP_DUTY, YARDSTICK, Line

#: Named by the ladder's tests, so still in the master, recorded as lines no ISA can hold;
#: they leave, and this with them, when those tests name another line (docs/PLAN.md).
LEAVING = {"SPY", "QQQ"}


def test_the_master_holds_the_twenty_of_the_ruling_thirteen_in_london_and_seven_in_the_us() -> None:
    assert len({line.symbol for line in LINES}) == len(LINES)
    twenty = [line for line in LINES if line.symbol not in LEAVING]
    assert Counter((line.venue, line.currency) for line in twenty) == {
        ("LSE", "GBP"): 12,
        ("LSE", "USD"): 1,  #: IDTL, which London prices in dollars
        ("US", "USD"): 7,
    }
    assert {line.symbol for line in LINES} >= {"VUAG", "EQQQ", "IDTL"}
    assert "GLD" not in {line.symbol for line in LINES}
    assert {(line.symbol, line.venue) for line in LINES} - {
        (line.symbol, line.venue) for line in twenty
    } == {(symbol, "US") for symbol in LEAVING}


def test_every_line_says_whether_an_isa_can_hold_it_and_a_retail_customer_buy_it() -> None:
    flags = {line.symbol: (line.isa, line.retail) for line in LINES}
    refused = {s: held for s, held in flags.items() if held != (True, True)}
    #: a US fund has no UK papers, so neither; a note on bitcoin a retail customer can buy,
    #: and a stocks and shares ISA cannot
    assert refused == {**dict.fromkeys(LEAVING, (False, False)), "IB1T": (False, True)}
    assert {type(flag) for held in flags.values() for flag in held} == {bool}
    unrecorded = Line("AAA", "US", "USD", 1)  #: nobody has recorded either: it carries neither
    assert (unrecorded.isa, unrecorded.retail) == (False, False)
    for isa, retail in ((1, True), (True, None), ("yes", "yes")):
        with pytest.raises(ValueError, match="BBB: whether an ISA can hold it"):
            Line("BBB", "LSE", "GBP", 1, NO_TAX, isa, retail)  # type: ignore[arg-type]


def test_simply_holding_the_market_is_the_s_and_p_500_in_pounds_an_isa_can_hold() -> None:
    assert YARDSTICK in LINES and YARDSTICK.symbol == "VUAG"
    assert (YARDSTICK.venue, YARDSTICK.currency, YARDSTICK.leverage) == ("LSE", "GBP", 1)
    assert YARDSTICK.isa and YARDSTICK.retail


def test_leverage_is_a_fact_in_the_master_never_read_from_a_name() -> None:
    leveraged = {line.symbol: line.leverage for line in LINES if line.leverage != 1}
    assert leveraged == {"3LGO": 3, "2MU": 2, "5QQQ": 5}


def test_a_line_on_a_venue_without_a_calendar_cannot_be_made() -> None:
    with pytest.raises(ValueError, match="NYSE"):
        Line("CCC", "NYSE", "USD", 1)


def test_a_suspension_can_be_recorded_only_on_a_day_its_venue_traded() -> None:
    assert Line("AAA", "US", "USD", 1, suspended=frozenset({date(2025, 11, 6)}))
    with pytest.raises(ValueError, match="2025-11-27"):
        Line("AAA", "US", "USD", 1, suspended=frozenset({date(2025, 11, 27)}))


def test_uk_tax_is_a_fact_on_the_line_and_each_of_the_london_lines_pays_none() -> None:
    london = "3LGO 2MU SMGB IITU VHYG 5QQQ IB1T ISF VUSA SGLN VUAG EQQQ IDTL".split()
    taxes = {line.symbol: line.uk_tax for line in LINES if line.venue == "LSE"}
    assert taxes == dict.fromkeys(london, NO_TAX) and NO_TAX == 0
    assert {line.uk_tax for line in LINES} == {NO_TAX}, "a US line pays no UK tax"
    assert Line("BARC", "LSE", "GBP", 1, STAMP_DUTY).uk_tax == Decimal("0.005")
    assert Line("IHG", "LSE", "USD", 1, STAMP_DUTY).uk_tax == STAMP_DUTY  #: quoted in dollars


def test_a_line_pays_nil_or_stamp_duty_and_only_a_london_line_can_pay_it() -> None:
    for tax in (Decimal("0.01"), Decimal("-0.005"), Decimal("0.5"), 0.005, 0):
        with pytest.raises(ValueError, match="BBB: no UK tax on a purchase is"):
            Line("BBB", "LSE", "GBP", 1, tax)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="AAA: a US line pays no UK tax"):
        Line("AAA", "US", "USD", 1, STAMP_DUTY)
