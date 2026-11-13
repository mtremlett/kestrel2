"""THE SCENES' REHEARSAL DATA: twenty synthetic lines, one spoilt, on the venues' own calendars.

Owned by the data lane (docs/PLAN.md). The scenes in test_scenes.py read it and never
build prices of their own, so lengthening it is one change in one file.

Fourteen months of made-up prices (the operator's ruling of 13 November 2026): a steady
rise, a slow fall, a breakout, a sharp three-day dip, a recovery and a last fall, so that
each of the five rules buys and sells. Each line trades on its own venue's sessions, so a
UK holiday is not a US one. The scenes see all of it.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import replace
from datetime import date
from decimal import Decimal

from desk import venues
from desk.lines import NO_TAX, STAMP_DUTY, Line
from desk.store import Bar

FIRST, LAST = date(2024, 9, 2), date(2025, 11, 14)
TODAY = date(2025, 11, 17)  #: the Monday after: the desk prepares to trade on this day
#: Twenty synthetic lines: eight on the London venue in pounds, twelve in the US in dollars.
#: The first is a UK share, whose purchase pays stamp duty; the rest pay no UK tax.
LINES = tuple(
    Line(f"L{n:02}", "LSE", "GBP", 1, STAMP_DUTY if n == 1 else NO_TAX)
    if n <= 8
    else Line(f"L{n:02}", "US", "USD", 1, NO_TAX)
    for n in range(1, 21)
)
BAD = LINES[4]
#: The shape every line follows, as (session, level in hundredths of the line's own base),
#: straight between: a rise, a fall, a breakout, a sharp three-day dip, a last fall.
SHAPE = ((0, 100), (110, 130), (190, 105), (235, 145), (238, 123), (242, 142), (-1, 105))
CENT = Decimal("0.01")

Archive = Mapping[Line, Sequence[Bar]]


def _level(t: int, last: int) -> Decimal:
    """The shape's level at session t of a line's last + 1 sessions."""
    knots = [(last if at < 0 else at, Decimal(level)) for at, level in SHAPE]
    for (t0, v0), (t1, v1) in zip(knots, knots[1:], strict=False):
        if t0 <= t <= t1:
            return v0 + (v1 - v0) * (t - t0) / (t1 - t0)
    raise ValueError(f"session {t} is outside the shape's {last + 1} sessions")


def _bars(n: int, days: Sequence[date]) -> tuple[Bar, ...]:
    """Line n's bars: the shape at a base of its own, with a small ripple of its own."""
    bars: list[Bar] = []
    for t, on in enumerate(days):
        ripple = 1 + Decimal((t * 7 + n * 3) % 11 - 5) / 400
        close = ((40 + 3 * n) * _level(t, len(days) - 1) / 100 * ripple).quantize(CENT)
        open_ = bars[-1].close if bars else close
        high = (max(open_, close) * Decimal("1.004")).quantize(CENT)
        low = (min(open_, close) * Decimal("0.996")).quantize(CENT)
        bars.append(Bar(on, open_, high, low, close, 10_000 + 100 * n))
    return tuple(bars)


CLEAN: Archive = {
    line: _bars(n, venues.sessions(line.venue, FIRST, LAST)) for n, line in enumerate(LINES, 1)
}
HISTORY = CLEAN  #: scene 5's name for it, until the money lane reads CLEAN (R-DATA-6)
SESSIONS = tuple(sorted({bar.day for bars in CLEAN.values() for bar in bars}))
#: The bad line's three faults, all in its last sixty sessions so that they park it: a price
#: in pence among pounds, a date given twice, a day missing.
_OWN = CLEAN[BAD]
WRONG_UNIT = replace(
    _OWN[-23],
    open=_OWN[-23].open * 100,
    high=_OWN[-23].high * 100,
    low=_OWN[-23].low * 100,
    close=_OWN[-23].close * 100,
)
SPOILT: Archive = {
    **CLEAN,
    BAD: (*_OWN[:-23], WRONG_UNIT, *_OWN[-22:-12], *_OWN[-13:-3], *_OWN[-2:]),
}


def before(archive: Archive, on: date) -> Archive:
    """What the archive holds before the market opens on a day."""
    return {line: tuple(bar for bar in bars if bar.day < on) for line, bars in archive.items()}
