"""snapshot - the nightly backup copy (R-RUNNER-13, DAT-11): one consistent copy of each price
database and of the ledger, written into the `backup` folder of the data folder, for his own
backup of the PC to pick up. A database is copied by SQLite's own backup, so a copy taken while a
keeper writes is whole; the ledger is a file swapped in whole, so a plain copy is whole too. A
snapshot is built in a folder of its own and named only when complete, so a stopped run leaves no
half snapshot among the kept ones. The last few are kept. Nothing is ever written elsewhere."""

from __future__ import annotations

import os
import shutil
import sqlite3
import sys
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

BACKUP, KEEP = "backup", 7  #: the folder inside the data folder; how many snapshots stay
DATABASES = ("market_history.db", "market_live.db", "market.db")  #: those present are copied
LEDGER = Path("desk") / "ledger.csv"
STAMP = "%Y%m%dT%H%M%SZ"


def _copy_database(source: Path, target: Path) -> None:
    with (
        closing(sqlite3.connect(f"{source.as_uri()}?mode=ro", uri=True)) as read,
        closing(sqlite3.connect(target)) as write,
    ):
        read.backup(write)
        verdict = write.execute("PRAGMA integrity_check").fetchone()[0]
    if verdict != "ok":
        raise RuntimeError(f"snapshot of {source} fails SQLite's integrity check: {verdict}")


def snapshot(data: Path, now: datetime, keep: int = KEEP) -> Path:
    """Write one snapshot of everything held under `data`; keep the newest `keep`."""
    held = [data / name for name in DATABASES if (data / name).is_file()]
    if not held:
        raise FileNotFoundError(f"no price database under {data}: nothing to snapshot")
    folder = data / BACKUP
    folder.mkdir(exist_ok=True)
    final = folder / now.astimezone(UTC).strftime(STAMP)
    if final.exists():
        raise FileExistsError(f"a snapshot named {final.name} is already kept in {folder}")
    building = folder / f"{final.name}.partial"
    shutil.rmtree(building, ignore_errors=True)  # the leftover of a run that was stopped
    building.mkdir()
    for path in held:
        _copy_database(path, building / path.name)
    if (data / LEDGER).is_file():
        shutil.copy2(data / LEDGER, building / LEDGER.name)
    building.rename(final)
    for old in sorted(p for p in folder.iterdir() if p.is_dir() and p.suffix != ".partial")[:-keep]:
        shutil.rmtree(old)
    return final


if __name__ == "__main__":
    try:
        made = snapshot(Path(os.environ["KESTREL2_DATA"]), datetime.now(UTC))
    except (KeyError, OSError, RuntimeError, sqlite3.Error) as error:
        sys.exit(f"snapshot failed: {error!r}")
    sys.stdout.write(f"snapshot: {made}\n")
