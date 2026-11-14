"""The nightly snapshot: whole copies of the databases and the ledger, the last few kept."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from desk.snapshot import snapshot

START = datetime(2026, 11, 15, 1, 30, tzinfo=UTC)


def _data(root: Path) -> Path:
    (root / "daily").mkdir()
    (root / "daily" / "SPY.csv").write_text("d,c\n1,2\n", encoding="utf-8")
    for name in ("market_history.db", "market_live.db", "bars.db"):
        with closing(sqlite3.connect(root / name)) as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("CREATE TABLE t (x)")
            db.execute("INSERT INTO t VALUES (?)", (name,))
            db.commit()
    (root / "desk").mkdir()
    (root / "desk" / "ledger.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    return root


def test_snapshot_copies_each_store_and_the_ledger_and_keeps_the_last_few(tmp_path: Path) -> None:
    data = _data(tmp_path)
    for night in range(4):
        made = snapshot(data, START + timedelta(days=night), keep=3)
    assert made.name == "20261118T013000Z"
    assert sorted(p.name for p in (data / "backup").iterdir()) == [
        "20261116T013000Z", "20261117T013000Z", "20261118T013000Z",
    ]  # fmt: skip
    assert sorted(p.name for p in made.iterdir()) == [
        "bars.db", "daily", "ledger.csv", "market_history.db", "market_live.db",
    ]  # fmt: skip
    assert (made / "daily" / "SPY.csv").read_text(encoding="utf-8") == "d,c\n1,2\n"
    with closing(sqlite3.connect(made / "bars.db")) as copy:
        assert copy.execute("SELECT x FROM t").fetchall() == [("bars.db",)]
    with closing(sqlite3.connect(made / "market_live.db")) as copy:
        assert copy.execute("SELECT x FROM t").fetchall() == [("market_live.db",)]
    assert (made / "ledger.csv").read_text(encoding="utf-8") == "a,b\n1,2\n"


def test_snapshot_refuses_without_a_database_or_for_a_night_already_kept(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="nothing to snapshot"):
        snapshot(tmp_path, START)
    (tmp_path / "d").mkdir()
    data = _data(tmp_path / "d")
    snapshot(data, START)
    with pytest.raises(FileExistsError, match="already kept"):
        snapshot(data, START)
