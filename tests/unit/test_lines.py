"""The instrument master: the twenty frozen lines of the operator's ruling of 13 November."""

from __future__ import annotations

from collections import Counter

from desk.lines import LINES


def test_the_master_holds_twenty_lines_ten_on_each_venue_each_in_its_own_currency() -> None:
    assert len({line.symbol for line in LINES}) == len(LINES) == 20
    assert Counter((line.venue, line.currency) for line in LINES) == {
        ("LSE", "GBP"): 10,
        ("US", "USD"): 10,
    }


def test_leverage_is_a_fact_in_the_master_never_read_from_a_name() -> None:
    leveraged = {line.symbol: line.leverage for line in LINES if line.leverage != 1}
    assert leveraged == {"3LGO": 3, "2MU": 2, "5QQQ": 5}
