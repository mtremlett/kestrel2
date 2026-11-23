"""backup - the fill ledger and the day records copied twice, and a restore drilled each quarter
(DQ-05, DQ-09). Every csv the desk keeps (ledger, records, stops...) is copied whole into a stamped
folder in two places, each with the hash of every file; his own backup of PYTHON carries both off
the PC (the first beside the data folder's `backup`, the second a sibling of the data folder). A
copy is built under a name of its own and named only when complete. The drill restores the newest
copy into a scratch folder, checks every hash, and is logged; it falls due after 92 days. The desk
never writes to E:."""

from __future__ import annotations

import hashlib
import os
import shutil
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

SUMS, DRILLS, KEEP, QUARTER = "SHA256SUMS", "drills.log", 30, timedelta(days=92)
STAMP = "%Y%m%dT%H%M%SZ"
FIRST, SECOND = "backup_records", "kestrel2_backup"  #: folder names: in the data folder, beside it


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _copy(source: Path, home: Path, stamp: str) -> Path:
    final, building = home / stamp, home / f"{stamp}.partial"
    if final.exists():
        raise FileExistsError(f"a backup named {stamp} is already kept in {home}")
    shutil.rmtree(building, ignore_errors=True)  # the leftover of a run that was stopped
    building.mkdir(parents=True)
    names = sorted(p.name for p in source.glob("*.csv"))
    for name in names:
        shutil.copy2(source / name, building / name)
    (building / SUMS).write_text("".join(f"{_hash(building / n)}  {n}\n" for n in names), "utf-8")
    building.rename(final)
    for old in sorted(p for p in home.iterdir() if p.is_dir() and p.suffix != ".partial")[:-KEEP]:
        shutil.rmtree(old)
    return final


def verify(copy: Path) -> int:
    """Check every file of a copy against its recorded hash; return how many files it holds."""
    lines = (copy / SUMS).read_text("utf-8").splitlines()
    for line in lines:
        digest, _, name = line.partition("  ")
        if not (copy / name).is_file() or _hash(copy / name) != digest:
            raise RuntimeError(f"backup {copy}: {name} is missing or differs from its hash")
    return len(lines)


def back_up(root: Path, now: datetime, data: Path) -> tuple[Path, Path]:
    """Copy the csv files under `root` twice; both copies are verified before this returns."""
    if not any(root.glob("*.csv")):
        raise FileNotFoundError(f"no csv under {root}: nothing to back up")
    stamp = now.astimezone(UTC).strftime(STAMP)
    copies = (_copy(root, data / FIRST, stamp), _copy(root, data.parent / SECOND, stamp))
    for copy in copies:
        verify(copy)
    return copies


def drill_due(data: Path, now: datetime) -> bool:
    """True when no restore drill is logged, or the last was 92 or more days ago."""
    log = data / FIRST / DRILLS
    if not log.is_file():
        return True
    last = datetime.strptime(log.read_text("utf-8").split()[-1], STAMP).replace(tzinfo=UTC)
    return now - last >= QUARTER


def drill(data: Path, now: datetime, scratch: Path) -> int:
    """Restore the second copy's newest backup into `scratch`, verify it, and log it."""
    newest = max(p for p in (data.parent / SECOND).iterdir() if p.is_dir() and not p.suffix)
    restored = scratch / newest.name
    shutil.copytree(newest, restored)
    count = verify(restored)
    with (data / FIRST / DRILLS).open("a", encoding="utf-8") as log:
        log.write(f"{count} files restored from {newest.name} at {now.astimezone(UTC):{STAMP}}\n")
    return count


if __name__ == "__main__":
    import tempfile

    kept, moment = Path(os.environ["KESTREL2_DATA"]), datetime.now(UTC)
    try:
        made = back_up(kept / "desk", moment, kept)
        with tempfile.TemporaryDirectory() as scratch:
            drilled = drill(kept, moment, Path(scratch)) if drill_due(kept, moment) else None
    except (KeyError, OSError, RuntimeError) as error:
        sys.exit(f"backup failed: {error!r}")
    sys.stdout.write(f"backup: {made[0]} and {made[1]}; restore drill: {drilled or 'not due'}\n")
