"""The instrument master: the frozen lines of the operator's rulings of 13 November."""

from __future__ import annotations

from collections import Counter
from datetime import date
from decimal import Decimal

import pytest

from desk.lines import (
    ADJUSTED,
    LINES,
    NO_TAX,
    REFERENCE,
    STAMP_DUTY,
    YARDSTICK,
    Line,
    require_traded,
    valid_isin,
)

#: Still in the master only because the ladder's tests name them; they leave when those do not.
LEAVING = {"SPY", "QQQ"}


def test_the_master_holds_the_twenty_of_the_ruling_thirteen_in_london_and_seven_in_the_us() -> None:
    symbols = {line.symbol for line in LINES}
    assert len(symbols) == len(LINES) and "GLD" not in symbols
    assert symbols >= {"VUAG", "EQQQ", "IDTL"}
    twenty = Counter((ln.venue, ln.currency) for ln in LINES if ln.symbol not in LEAVING)
    #: the one London line in dollars is IDTL
    assert twenty == {("LSE", "GBP"): 12, ("LSE", "USD"): 1, ("US", "USD"): 7}
    leaving = {ln.symbol: ln.venue for ln in LINES if ln.symbol in LEAVING}
    assert leaving == dict.fromkeys(LEAVING, "US")


def test_every_line_says_whether_an_isa_can_hold_it_and_a_retail_customer_buy_it() -> None:
    flags = {line.symbol: (line.isa, line.retail) for line in LINES}
    refused = {s: held for s, held in flags.items() if held != (True, True)}
    #: a US fund has no UK papers; a bitcoin note a retail customer can buy and an ISA cannot
    assert refused == {**dict.fromkeys(LEAVING, (False, False)), "IB1T": (False, True)}
    unrecorded = Line("AAA", "US", "USD", 1)  #: nobody has recorded either: neither yes nor no
    assert unrecorded.isa is None and unrecorded.retail is None
    for isa, retail in ((1, True), (True, 0), ("yes", "yes")):
        with pytest.raises(ValueError, match="BBB: whether an ISA can hold it"):
            Line("BBB", "LSE", "GBP", 1, NO_TAX, isa, retail)  # type: ignore[arg-type]


def test_simply_holding_the_market_is_the_s_and_p_500_in_pounds_an_isa_can_hold() -> None:
    assert YARDSTICK in LINES and YARDSTICK.symbol == "VUAG"
    assert (YARDSTICK.venue, YARDSTICK.currency, YARDSTICK.leverage) == ("LSE", "GBP", 1)
    assert (YARDSTICK.isa, YARDSTICK.retail) == (True, True)


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


def test_the_lines_record_what_a_second_source_confirmed() -> None:
    held = {line.symbol: line for line in LINES}
    assert held["5QQQ"].starts == date(2024, 8, 22)
    moves = {sym: len(line.real_moves) for sym, line in held.items() if line.real_moves}
    assert moves == {"2MU": 4, "5QQQ": 2, "SGLN": 1}


def test_spy_and_qqq_are_read_as_reference_series_and_refused_as_traded_lines() -> None:
    assert {line.symbol for line in REFERENCE} == LEAVING
    traded = [require_traded(line) for line in LINES if line not in REFERENCE]
    assert traded and all(line.retail for line in traded), "a retail customer can buy each"
    for line in LINES:
        if line.symbol in LEAVING:
            with pytest.raises(ValueError, match=f"{line.symbol}: a reference series"):
                require_traded(line)
        else:
            assert require_traded(line) is line
    assert [a.symbol for a in ADJUSTED] == [f"{r.symbol}-ADJUSTED" for r in REFERENCE]
    with pytest.raises(ValueError, match="SPY-ADJUSTED: a reference series"):
        require_traded(ADJUSTED[0])


def test_every_traded_line_has_an_isin_with_a_good_check_digit() -> None:
    traded = [ln for ln in LINES if ln not in REFERENCE]
    assert all(ln.isin and len(ln.isin) == 12 and valid_isin(ln.isin) for ln in traded)
    assert {ln.symbol: ln.isin for ln in LINES}["IDTL"] == "IE00BSKRJX20"
    assert len({ln.isin for ln in LINES}) == len(LINES)
    assert not valid_isin("IE00BSKRJX21") and not valid_isin("IE00BSKRJX2")
    with pytest.raises(ValueError, match="check digit"):
        Line("X", "LSE", "GBP", 1, isin="IE00BSKRJX21")


def test_every_line_names_its_underlying_market_and_source_and_one_index_is_one_underlying() -> (
    None
):
    assert all(line.underlying and line.source for line in LINES)
    by_market: dict[str, set[str]] = {}
    for line in LINES:
        by_market.setdefault(line.underlying, set()).add(line.symbol)
    assert by_market["S&P 500"] == {"VUSA", "VUAG", "SPY"}
    assert by_market["NASDAQ 100"] == {"EQQQ", "QQQ", "5QQQ"}
    assert by_market["GOLD"] == {"3LGO", "SGLN"} and by_market["MU"] == {"MU", "2MU"}
