"""The store's second source: Stooq fills what Yahoo lacks; where both hold a session they agree."""

from __future__ import annotations

from dataclasses import replace
from datetime import date
from decimal import Decimal
from pathlib import Path

from desk import store, venues
from desk.lines import Line
from desk.store import Bar, Refused

UK = Line("BBB", "LSE", "GBP", 1)
DAY = date(2025, 11, 17)
DAYS = venues.sessions("LSE", date(2025, 11, 3), date(2025, 11, 14))
YAHOO = tuple(
    Bar(d, Decimal(50 + n % 3), Decimal(52 + n % 3), Decimal(49 + n % 3), Decimal(51), 900)
    for n, d in enumerate(DAYS)
)
PENCE = tuple(
    Bar(b.day, b.open * 100, b.high * 100, b.low * 100, b.close * 100, b.volume) for b in YAHOO
)


def test_stooq_fills_a_hole_in_pounds_and_a_disagreement_is_a_fault_kept_from_neither(
    tmp_path: Path,
) -> None:
    holed = YAHOO[:3] + YAHOO[4:]
    assert store.prepare(tmp_path, {UK: holed}, DAY, second={UK: PENCE}) == ()
    assert store.read(tmp_path, "BBB") == YAHOO  # the hole filled, in pounds, and not parked
    assert "1 sessions offered by the second source" in store.faults(tmp_path, "BBB")[0]
    odd = replace(PENCE[6], close=PENCE[6].close * Decimal("1.1"))
    parked = store.prepare(tmp_path, {UK: YAHOO}, DAY, second={UK: PENCE[:6] + (odd,) + PENCE[7:]})
    assert [p.reason for p in parked] == [f"{DAYS[6]} the two sources disagree: none kept"]
    assert [b.day for b in store.read(tmp_path, "BBB")] == [d for d in DAYS if d != DAYS[6]]


def test_a_second_source_away_or_in_no_known_unit_parks_nothing_and_says_so(tmp_path: Path) -> None:
    strange = tuple(replace(b, close=b.close * 7) for b in PENCE)
    for other in (Refused("no key"), strange):
        assert store.prepare(tmp_path, {UK: YAHOO}, DAY, second={UK: other}) == ()
        assert store.read(tmp_path, "BBB") == YAHOO and len(store.faults(tmp_path, "BBB")) == 1
