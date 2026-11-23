"""The master and the calendars agree: every line's venue has a calendar, and every SimCity
world's dates are trading days for its lines (R-RUNNER-107)."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from desk import simcity, venues
from desk.lines import LINES, Line
from desk.orders import Settings
from desk.store import Bar

sys.path.insert(0, str(Path(__file__).parents[1] / "scenes"))  #: the scenes' rehearsal data
from rehearsal import CLEAN  # noqa: E402  the path above comes first


def test_every_line_of_the_master_has_a_calendar_for_its_venue() -> None:
    bare = [
        ln.symbol for ln in LINES if ln.venue not in venues.RULES or ln.venue not in venues.CLOCKS
    ]
    assert (
        not bare
    ), f"lines on a venue with no calendar in desk.venues (holidays and hours): {bare}"


def test_every_simcity_world_is_dated_on_trading_days_of_its_lines(tmp_path: Path) -> None:
    worlds: list[dict[Line, tuple[Bar, ...]]] = []  #: the worlds as SimCity deals them
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(simcity, "_live", lambda life: worlds.append(dict(life.market)))
        at, rates = datetime(2025, 11, 17, tzinfo=UTC), {"GBP": Decimal(1), "USD": Decimal("0.79")}
        simcity.run(tmp_path, CLEAN, Settings(Decimal(10_000)), rates, at, range(3))
    off = [
        f"world {seed}: {ln.symbol} is dated {bar.day}, which is no {ln.venue} session"
        for seed, market in enumerate(worlds)
        for ln, bars in market.items()
        for bar in bars
        if venues.sessions(ln.venue, bar.day, bar.day) != (bar.day,)
    ]
    assert len(worlds) == 3 and not off, off[:3]
