"""universe_history - THE RESEARCH BARS IN THE HISTORY DATABASE (R-RUNNER-221, 16 November 2026).
Research's daily bars were CSV files in grid/store, filled from Yahoo; the ladder's pound per
dollar a table of closes beside its results. Here both enter market_history.db through the one
writer, each bar keeping its source: a bar the store's shelf also holds (the Stooq matrices'
fill of a missing day) under Source.MATRIX_DAILY, every other under Source.ARCHIVE (Yahoo).
The bars were cleaned by the store when the CSV was written, so they are not judged again. Only
days the database holds no bar for are written, so a second run adds nothing and a bar already
in is never restated. A session with no bar is named, for quality-backfill, never invented.
`python -m lab.universe history` imports the whole research list and the pound."""

from __future__ import annotations

import json
import os
from collections.abc import Iterable
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from urllib.request import urlopen

from desk import bars, venues
from desk.bars import Source
from desk.lines import POUND, Line
from desk.store import Bar


def fill(path: Path, line: Line, source: Source, given: Iterable[Bar]) -> int:
    """The given bars on days the database holds none for, kept under the source; how many."""
    try:
        held = {bar.day for bar in bars.daily(path, line)}
    except (LookupError, FileNotFoundError):  # a line never written holds nothing
        held = set()
    new = [bar for bar in given if bar.day not in held]
    if not new:
        return 0
    with bars.writing(path, source) as opened:
        return opened.days(line, new)


FED = "https://api.stlouisfed.org/fred/series/observations?series_id=DEXUSUK&file_type=json"
KEY = "FRED_API_KEY"  #: handed to the job by the runner's session environment alone


def enter_noon(path: Path, answer: str) -> int:
    """The pound's noon rates (FRED's DEXUSUK observations as JSON, "." for a day with none) on
    every day the database holds no pound for: before the archive's first (December 2003), and a
    day it lacks since, a series of its own kind and label. A day the Fed gave none stays a gap."""
    rows = json.loads(answer)["observations"]
    given = [
        (date.fromisoformat(r["date"]), Decimal(r["value"])) for r in rows if r["value"] != "."
    ]
    return fill(path, POUND, Source.FED_NOON, (Bar(d, r, r, r, r, 0) for d, r in given))


def noon(path: Path) -> str:
    """The noon rates asked of FRED and let in; one line saying how many days."""
    if not (key := os.environ.get(KEY)):
        raise KeyError(f"universe_history.noon: {KEY} is not in the session environment")
    with urlopen(f"{FED}&observation_start=1993-01-01&api_key={key}", timeout=60) as answer:  # noqa: S310 - one fixed public address
        added = enter_noon(path, answer.read().decode("utf-8"))
    return f"the pound's noon rates: {added} days added"


def enter_pound(table: Path, path: Path) -> int:
    """The ladder's table of the pound's daily closes (one [day, close] a line) into the
    database as its own series, a bar of one price and no volume."""
    rows = map(json.loads, table.read_text(encoding="utf-8").splitlines())
    closes = [(date.fromisoformat(day), Decimal(close)) for day, close in rows]
    return fill(path, POUND, Source.ARCHIVE, (Bar(d, c, c, c, c, 0) for d, c in closes))


def missing(path: Path, line: Line, until: date) -> tuple[date, ...]:
    """The sessions from the line's first bar to before `until` that the database holds no bar
    for; none for a line it holds nothing of."""
    try:
        held = {bar.day for bar in bars.daily(path, line)}
    except (LookupError, FileNotFoundError):
        return ()
    if not held:
        return ()
    return tuple(
        d for d in venues.sessions(line.venue, min(held), until - timedelta(1)) if d not in held
    )


def run(path: Path, table: Path, named: Iterable[Line], day: date) -> str:
    """The pound imported; one line saying the days added and, for the named lines (the
    yardsticks), the sessions missing before day."""
    pounds = enter_pound(table, path)
    gaps = "".join(
        f"; {line.symbol} has no bar on {', '.join(map(str, lost))}"
        for line in named
        if (lost := missing(path, line, day))
    )
    return f"research history: {pounds} pound days added{gaps}"
