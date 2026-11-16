"""audit - THE STORE RE-CHECKED, read-only: every held line and ticker of the long-term database
passed again through the checks that let its bars in, one line of counts and faults by kind
(R-RUNNER-18). `KESTREL2_DATA=<data folder> python -m desk.audit`."""

from __future__ import annotations

import os
import re
import sqlite3
import sys
from collections import Counter
from contextlib import closing
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from desk import venues
from desk.bars import EPOCH, FIVE, HISTORY, WAIT, checked, daily, five
from desk.lines import LINES, Line
from desk.store import _clean as cleaned


def _audited(path: Path, venue: str, symbol: str, span: str) -> tuple[int, list[str]]:
    """One held line and span through the checks that let its bars in: how many bars, and
    every fault. A research ticker is no frozen line, so it is checked as a plain one."""
    if venue not in venues.RULES:
        return 0, [f"no calendar for venue {venue}"]
    plain = Line(symbol, venue, "GBP" if venue == "LSE" else "USD", 1)
    line = next((x for x in LINES if (x.venue, x.symbol) == (venue, symbol)), plain)
    if span == FIVE:
        every = five(path, line, EPOCH, datetime(9999, 12, 31, tzinfo=UTC))
        return len(every), checked(line, every)[1]
    every_day = daily(path, line)
    end = max((b.day for b in every_day), default=date.today()) + timedelta(1)
    return len(every_day), [f.what for f in cleaned(line, every_day, end, end)[1]]


def audit(path: Path) -> str:
    """Every line and ticker the store at path holds, re-checked read-only: one line of counts
    and faults by kind, the worst three lines named."""
    with closing(sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True, timeout=WAIT)) as held:
        keys = held.execute("SELECT venue, symbol, span FROM held ORDER BY 1, 2, 3").fetchall()
    total, kinds, worst = 0, Counter[str](), Counter[str]()
    for venue, symbol, span in keys:
        count, found = _audited(path, venue, symbol, span)
        total += count
        kinds.update(re.sub(r"\s+", " ", re.sub(r"[\d.:-]+", "", what)).strip() for what in found)
        worst[f"{symbol} on {venue} ({span})"] = len(found)
    named = ", ".join(f"{k} {n}" for k, n in worst.most_common(3) if n) or "none"
    by_kind = "; ".join(f"{n} {k}" for k, n in kinds.most_common()) or "none"
    return (
        f"bars audit: {len(keys)} lines, {total} bars, {sum(kinds.values())} faults"
        f" ({by_kind}); worst: {named}"
    )


if __name__ == "__main__":
    store = Path(os.environ.get("KESTREL2_DATA", "")) / HISTORY
    if not store.is_file():
        sys.exit(f"audit: no store at {store}")
    sys.stdout.write(audit(store) + "\n")
