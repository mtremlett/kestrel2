"""handpark - A LINE PARKED BY HAND (R-RUNNER-397): a symbol named in `parked.csv` under the
desk's data folder (symbol, who, why; one per row) is never bought by any rule while it is
listed. It is sold and stopped as ever. Delete its row and the next round buys it again."""

from __future__ import annotations

import csv
from pathlib import Path

FILE = "parked.csv"
HEAD = ["symbol", "who", "why"]


def parked(root: Path) -> dict[str, str]:
    """Each symbol parked by hand, with the words the buy's answer carries: who parked it, why.
    No file means none. A file with another head is an error, never an empty list."""
    path = root / FILE
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as kept:
        rows = list(csv.reader(kept))
    if rows[:1] != [HEAD]:
        raise ValueError(f"{path}: not a list of lines parked by hand (symbol, who, why)")
    return {symbol: f"{who}: {why}" for symbol, who, why in rows[1:]}
