"""universe_history - THE RESEARCH BARS IN THE HISTORY DATABASE (R-RUNNER-221, 16 November 2026).
Research's daily bars were CSV files in grid/store, filled from Yahoo; the pound's noon rates
enter market_history.db through the one
writer, each bar keeping its source: a bar the store's shelf also holds (the Stooq matrices'
fill of a missing day) under Source.MATRIX_DAILY, every other under Source.ARCHIVE (Yahoo).
The bars were cleaned by the store when the CSV was written, so they are not judged again. Only
days the database holds no bar for are written, so a second run adds nothing and a bar already
in is never restated. A session with no bar is named, for quality-backfill, never invented.
`python -m lab.universe history` names the research list's missing sessions."""

from __future__ import annotations

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


FED = (
    "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DEXUSUK&cosd=1993-01-01"  #: keyless, public
)


def enter_noon(path: Path, table: str) -> int:
    """The pound's noon rates (FRED's DEXUSUK, a day a line `date,dollars`, a blank for a day with
    none) on the days before the archive's first pound, a series of its own kind, labelled as
    such: the archive gives the pound only from December 2003 (R-RUNGS-3). Nothing after that."""
    first = min(bar.day for bar in bars.daily(path, POUND))
    rows = (line.split(",") for line in table.splitlines()[1:])
    given = [(date.fromisoformat(day), Decimal(rate)) for day, rate in rows if rate]
    return fill(
        path, POUND, Source.FED_NOON, (Bar(d, r, r, r, r, 0) for d, r in given if d < first)
    )


def noon(path: Path) -> str:
    """The noon rates asked of FRED and let in; one line saying how many days."""
    with urlopen(FED, timeout=60) as answer:  # noqa: S310 - one fixed public address
        added = enter_noon(path, answer.read().decode("utf-8"))
    return f"the pound before the archive's: {added} noon-rate days added"


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


def run(path: Path, named: Iterable[Line], day: date) -> str:
    """One line naming, for the named lines (the yardsticks), the sessions missing before day."""
    gaps = "".join(
        f"; {line.symbol} has no bar on {', '.join(map(str, lost))}"
        for line in named
        if (lost := missing(path, line, day))
    )
    return f"research history{gaps}"
