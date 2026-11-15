"""The store's shelf: older bars joined to the archive's, and what they replace."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
from test_store import DAY, LONG, UK, US, _bars, _parked

from desk import store
from desk.store import Bar


def test_shelved_older_bars_join_the_archives_and_outlast_every_rebuild(tmp_path: Path) -> None:
    every = _bars(UK, LONG)
    store.shelve(tmp_path, UK, every[:5])
    for _ in range(2):  # the store is rebuilt from the archive on every prepare
        assert store.prepare(tmp_path, {UK: every[3:]}, DAY) == ()
        assert store.read(tmp_path, UK.symbol) == every
    assert store.prepare(tmp_path, {US: _bars(US, LONG)}, DAY) == ()  # a line with none shelved


@pytest.mark.parametrize("shelf", [(8, 20), (12, 15), (0, 5)], ids=["all", "part", "none of it"])
def test_a_frozen_run_the_archive_filled_is_replaced_by_shelved_bars_never_by_its_own_filler(
    tmp_path: Path, shelf: tuple[int, int]
) -> None:
    """VUAG, 23 May to 18 June 2019: the archive repeats one price for 27 sessions."""
    every = [replace(b, volume=900 + n) for n, b in enumerate(_bars(UK, LONG))]
    c = every[9].close
    archive = (*every[:10], *[Bar(b.day, c, c, c, c, 0) for b in every[10:17]], *every[17:])
    _parked(tmp_path, archive, UK)
    assert store.read(tmp_path, UK.symbol) == (*every[:10], *every[17:])  # dropped, as ever
    store.shelve(tmp_path, UK, every[shelf[0] : shelf[1]])  # the old desk's own prices
    _parked(tmp_path, archive, UK)
    first, last = max(shelf[0], 10), min(shelf[1], 17)
    assert store.read(tmp_path, UK.symbol) == (*every[:10], *every[first:last], *every[17:])
    assert bool(store.faults(tmp_path, UK.symbol)) is (shelf != (8, 20))
