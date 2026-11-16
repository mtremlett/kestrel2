"""The one Stooq client: it reads the price table exactly, and refuses anything else."""

from __future__ import annotations

from dataclasses import replace
from datetime import date
from decimal import Decimal

import pytest

from desk import stooq
from desk.lines import YARDSTICK

TABLE = (
    b"Date,Open,High,Low,Close,Volume\n2020-03-12,36.1,36.9,34.7,35.5,1200\n"
    b"2020-03-13,35.5,36,35,35.8,\n"
)


def test_the_table_is_read_exactly_and_the_address_asks_for_the_whole_history() -> None:
    first, second = stooq.parse(YARDSTICK, TABLE)
    assert (first.day, first.high, first.volume) == (date(2020, 3, 12), Decimal("36.9"), 1200)
    assert (second.close, second.volume) == (Decimal("35.8"), 0)
    assert stooq.address(YARDSTICK, date(2026, 11, 16)) == (
        "https://stooq.com/q/d/l/?s=vuag.uk&i=d&d1=20100101&d2=20261115"
    )


@pytest.mark.parametrize(
    "payload",
    [b"No data", b"<html><script>verify</script></html>", TABLE.replace(b"36.9", b"x")],
    ids=["no data", "script page", "unreadable price"],
)
def test_anything_but_the_table_is_refused_with_what_was_said(payload: bytes) -> None:
    with pytest.raises(ValueError, match="VUAG"):
        stooq.parse(YARDSTICK, payload)


def test_the_unit_is_matched_by_the_closes_both_sources_hold() -> None:
    first = list(stooq.parse(YARDSTICK, TABLE))
    pence = [replace(b, **{p: getattr(b, p) * 100 for p in stooq.PRICES}) for b in first]
    assert stooq.matched(first, pence) == {b.day: b for b in first}
    odd = [replace(b, close=b.close * 10) for b in first]  # no unit: left as it is
    assert stooq.matched(first, odd)[first[0].day].close == first[0].close * 10
