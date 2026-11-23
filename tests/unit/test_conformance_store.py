"""A conformance run is sized from the desk's store (IBKR first), never from the archive alone."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from test_conformance import FRI, FX, MON, SPY, STAMP, VUAG, _fetch, _run, _world

from desk import archive, conformance, keeper
from desk.lines import Line
from desk.store import Bar


def test_a_run_is_sized_from_the_stores_bar_and_never_asks_the_archive(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    held: dict[Line, tuple[Bar, ...]] = {VUAG: (Bar(FRI, *(Decimal(110),) * 4, 400_000),)}
    monkeypatch.setattr(archive, "fetch", lambda *_: pytest.fail("the archive was asked"))
    monkeypatch.setattr(keeper, "saved", lambda _home, _day, _lines: (held, frozenset()))
    run = conformance.plan([VUAG], SPY, MON.date(), FX, STAMP, tmp_path)
    assert run.first.price == Decimal(110)
    held[VUAG] = ()  # the store lacks it too: refused, named
    with pytest.raises(ValueError, match="VUAG: the store has no bar of 2026-11-13"):
        conformance.plan([VUAG], SPY, MON.date(), FX, STAMP, tmp_path)

    def stale(_home: Path, _day: date, _lines: object) -> None:
        raise keeper.Stale("VUAG: no LSE bars")

    monkeypatch.setattr(keeper, "saved", stale)
    with pytest.raises(ValueError, match="VUAG: the store has no bar"):
        conformance.plan([VUAG], SPY, MON.date(), FX, STAMP, tmp_path)


def test_the_command_sizes_its_round_from_the_desks_store_never_the_archive(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _world(monkeypatch)

    def archive_gap(_line: Line, _before: date) -> None:
        raise AssertionError("the archive was asked")

    monkeypatch.setattr(archive, "fetch", archive_gap)
    asked: list[Path] = []

    def saved(
        home: Path, day: date, lines: list[Line]
    ) -> tuple[dict[Line, tuple[Bar, ...]], frozenset[Line]]:
        asked.append(home)
        return {x: _fetch(x, day) for x in lines}, frozenset()

    monkeypatch.setattr(keeper, "saved", saved)
    assert _run(tmp_path, MON, "london") == 0
    assert set(asked) == {tmp_path}
    assert "VUAG" in capsys.readouterr().out
