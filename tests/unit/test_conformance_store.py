"""A conformance run is sized from the desk's store (IBKR first), never from the archive alone."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from test_conformance import FRI, FX, MON, SPY, STAMP, VUAG

from desk import archive, conformance, keeper
from desk.lines import Line
from desk.store import Bar


def test_a_run_is_sized_from_the_stores_bar_when_the_archive_lacks_it(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    held: dict[Line, tuple[Bar, ...]] = {VUAG: (Bar(FRI, *(Decimal(110),) * 4, 400_000),)}
    monkeypatch.setattr(archive, "fetch", lambda _line, _before: ())  # Yahoo has a gap
    monkeypatch.setattr(keeper, "saved", lambda _home, _day, _lines: (held, frozenset()))
    run = conformance.plan([VUAG], SPY, MON.date(), FX, STAMP, tmp_path)
    assert run.first.price == Decimal(110)
    held[VUAG] = ()  # the store lacks it too: refused, named
    with pytest.raises(ValueError, match="VUAG: the archive has no bar"):
        conformance.plan([VUAG], SPY, MON.date(), FX, STAMP)  # no store given: the archive
    with pytest.raises(ValueError, match="VUAG: the store has no bar of 2026-11-13"):
        conformance.plan([VUAG], SPY, MON.date(), FX, STAMP, tmp_path)

    def stale(_home: Path, _day: date, _lines: object) -> None:
        raise keeper.Stale("VUAG: no LSE bars")

    monkeypatch.setattr(keeper, "saved", stale)
    with pytest.raises(ValueError, match="VUAG: the store has no bar"):
        conformance.plan([VUAG], SPY, MON.date(), FX, STAMP, tmp_path)
