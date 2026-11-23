"""ONE DOOR FOR PRICES (his ruling, Sun 22 Nov ~10:00, "paramount"): every price the desk and
the lab read comes from market_history.db or market_live.db, through the store's readers.
Only the WRITERS, which let outside prices into those two databases, may ask the archive or
read a price file. Any other line in desk/ or lab/ that does is refused here, one line at a
time (failure pattern 1); the words are built from pieces, so this file never flags itself.
It is the last of the conditions on the price-one-door hold (the ladder and grid jobs)."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
#: The modules that let outside prices into the two databases, each so named in manifest.toml.
WRITERS = frozenset(
    {
        "desk/keeper.py",
        "desk/keeper_live.py",
        "desk/backfill.py",
        "lab/universe.py",
        "lab/universe_history.py",
        "lab/headstart.py",
        "lab/headstart_days.py",
    }
)
OUTSIDE = re.compile(
    "arch" + r"ive\.(fetch|fetch_five|gather)\b|" + "st" + r"ore\.(read|load)\(|read" + r"_csv\b"
)


def test_only_the_writers_read_prices_from_outside_the_two_databases() -> None:
    strays = [
        f"{name}:{number}: {line.strip()}"
        for folder in ("desk", "lab")
        for path in sorted((ROOT / folder).glob("*.py"))
        if (name := path.relative_to(ROOT).as_posix()) not in WRITERS
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if OUTSIDE.search(line)
    ]
    assert not strays, (
        "a price read from outside the two databases, outside the writers: "
        f"{strays}. Read through the store's readers (desk/bars.py, lab/history_bars.py)."
    )


def test_every_writer_exists() -> None:
    assert sorted(w for w in WRITERS if not (ROOT / w).is_file()) == []
