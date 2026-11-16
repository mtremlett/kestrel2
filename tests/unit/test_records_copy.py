"""The backup: the desk's csv records copied twice with hashes, a restore drilled each quarter."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from desk.backup import FIRST, SECOND, back_up, drill, drill_due, verify

NOW = datetime(2026, 11, 16, 3, 0, tzinfo=UTC)


def _desk(tmp_path: Path) -> tuple[Path, Path]:
    data = tmp_path / "data"
    (data / "desk").mkdir(parents=True)
    (data / "desk" / "ledger.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    (data / "desk" / "records.csv").write_text("day\n2026-11-13\n", encoding="utf-8")
    return data, data / "desk"


def test_two_verified_copies_then_a_drill_that_restores_and_catches_damage(tmp_path: Path) -> None:
    data, root = _desk(tmp_path)
    assert drill_due(data, NOW)
    first, second = back_up(root, NOW, data)
    assert first.parent.name == FIRST and second.parent.name == SECOND
    assert (second / "ledger.csv").read_text(encoding="utf-8") == "a,b\n1,2\n"
    scratch = tmp_path / "scratch"
    assert drill(data, NOW, scratch) == 2
    assert not drill_due(data, NOW + timedelta(days=91))
    assert drill_due(data, NOW + timedelta(days=92))
    (second / "records.csv").write_text("day\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="records.csv"):
        verify(second)


def test_back_up_refuses_with_nothing_to_copy_or_for_a_moment_already_kept(tmp_path: Path) -> None:
    data, root = _desk(tmp_path)
    with pytest.raises(FileNotFoundError, match="nothing to back up"):
        back_up(tmp_path, NOW, data)
    back_up(root, NOW, data)
    with pytest.raises(FileExistsError, match="already kept"):
        back_up(root, NOW, data)
