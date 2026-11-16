"""The second source at the one writer: it fills the first's holes, recorded and not parked;
where both hold a session their closes must agree, else it is a recorded fault."""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest
from test_store import DAY, LONG, US, _bars, _scaled

from desk import store
from desk.store import Bar

CLEAN = list(_bars(US, LONG))
HOLE = [*CLEAN[:-3], *CLEAN[-2:]]  # a session in the last sixty that the first gave none
APART = [*CLEAN[:-3], replace(CLEAN[-3], close=CLEAN[-3].close * Decimal("1.1")), *CLEAN[-2:]]
SECOND: dict[str, tuple[list[Bar], list[Bar], str]] = {  # rule site -> (first, second, fault seen)
    "_filled:1": (CLEAN, APART, "the sources disagree"),
    "_filled:2": (HOLE, CLEAN, "filled from the second source"),
}


def _prepare(tmp_path: Path, first: list[Bar], second: list[Bar]) -> list[str]:
    return [p.reason for p in store.prepare(tmp_path, {US: first}, DAY, second={US: second})]


def test_a_hole_the_second_source_fills_is_kept_and_recorded_but_not_parked(tmp_path: Path) -> None:
    assert store.prepare(tmp_path, {US: HOLE}, DAY) != ()  # alone, the hole parks the line
    assert _prepare(tmp_path, HOLE, CLEAN) == []
    assert store.read(tmp_path, US.symbol) == tuple(CLEAN)
    assert any("filled from the second source" in f for f in store.faults(tmp_path, US.symbol))


def test_the_second_sources_unit_is_matched_by_the_closes_both_hold(tmp_path: Path) -> None:
    pence = [_scaled(bar, Decimal(100)) for bar in CLEAN]
    assert _prepare(tmp_path, HOLE, pence) == []
    assert store.read(tmp_path, US.symbol) == tuple(CLEAN)


def test_a_session_the_sources_disagree_on_is_a_fault_and_neither_bar_is_kept(
    tmp_path: Path,
) -> None:
    assert _prepare(tmp_path, CLEAN, APART) != []
    assert CLEAN[-3].day not in {b.day for b in store.read(tmp_path, US.symbol)}


@pytest.mark.parametrize("site", sorted(SECOND))
def test_each_second_source_rule_fires_on_its_row(tmp_path: Path, site: str) -> None:
    first, second, seen = SECOND[site]
    _prepare(tmp_path, first, second)
    assert any(seen in f for f in store.faults(tmp_path, US.symbol)), site
