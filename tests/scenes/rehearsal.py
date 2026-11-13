"""THE SCENES' REHEARSAL DATA: twenty synthetic lines, one spoilt, on a fixed calendar.

Owned by the data lane (docs/PLAN.md). The scenes in test_scenes.py read it and never
build prices of their own, so lengthening it is one change in one file.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal

from desk.lines import Line
from desk.store import Bar

#: Six weeks with no UK or US market holiday in them, so every weekday trades on both.
FIRST, LAST = date(2025, 10, 1), date(2025, 11, 14)
TODAY = date(2025, 11, 17)  #: the Monday after: the desk prepares to trade on this day
SESSIONS = tuple(
    FIRST + timedelta(n)
    for n in range((LAST - FIRST).days + 1)
    if (FIRST + timedelta(n)).weekday() < 5
)
#: Twenty synthetic lines: eight on the London venue in pounds, twelve in the US in dollars.
LINES = tuple(
    Line(f"L{n:02}", "LSE", "GBP", 1) if n <= 8 else Line(f"L{n:02}", "US", "USD", 1)
    for n in range(1, 21)
)
BAD = LINES[4]

Archive = Mapping[Line, Sequence[Bar]]


def _bar(n: int, t: int, on: date) -> Bar:
    """A slow wave around a level of its own, so strategies have something to trade."""
    close = Decimal(40 + 3 * n) + Decimal((t * 7 + n * 3) % 11 - 5) / 2
    open_ = close - Decimal("0.25")
    return Bar(on, open_, close + 1, open_ - 1, close, 10_000 + 100 * n)


CLEAN: Archive = {
    line: tuple(_bar(n, t, on) for t, on in enumerate(SESSIONS)) for n, line in enumerate(LINES, 1)
}
#: The bad line's three faults: a price in pence among pounds, a date twice, a day missing.
WRONG_UNIT = replace(
    CLEAN[BAD][10],
    open=CLEAN[BAD][10].open * 100,
    high=CLEAN[BAD][10].high * 100,
    low=CLEAN[BAD][10].low * 100,
    close=CLEAN[BAD][10].close * 100,
)
SPOILT: Archive = {
    **CLEAN,
    BAD: (*CLEAN[BAD][:10], WRONG_UNIT, *CLEAN[BAD][11:21], *CLEAN[BAD][20:30], *CLEAN[BAD][31:]),
}


def before(archive: Archive, on: date) -> Archive:
    """What the archive holds before the market opens on a day."""
    return {line: tuple(bar for bar in bars if bar.day < on) for line, bars in archive.items()}
