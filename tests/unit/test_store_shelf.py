"""The store's shelf: older bars joined to the archive's, and what they replace."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

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


def test_a_frozen_run_the_archive_filled_is_replaced_by_shelved_bars_never_by_its_own_filler(
    tmp_path: Path,
) -> None:
    """VUAG, 23 May to 18 June 2019: the archive repeats one price for 27 sessions."""
    every = [replace(b, volume=900 + n) for n, b in enumerate(_bars(UK, LONG))]
    run = range(10, 17)
    c = every[9].close
    filler = [Bar(every[n].day, c, c, c, c, 0) for n in run]
    archive = (*every[:10], *filler, *every[17:])
    _parked(tmp_path, archive, UK)
    assert len(store.read(tmp_path, UK.symbol)) == len(every) - 7
    store.shelve(tmp_path, UK, every[8:20])  # the old desk's bars: its own prices on those days
    _parked(tmp_path, archive, UK)
    assert store.read(tmp_path, UK.symbol) == tuple(every)
    assert store.faults(tmp_path, UK.symbol) == ()
