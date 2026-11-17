"""The monitor: planted gaps filled and re-audited green; a gap no source fills named red."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from desk import bars, quality
from desk.lines import LINES
from desk.spans import Timed
from desk.store import Bar, Refused

SPY = next(line for line in LINES if line.symbol == "SPY")
TODAY = date(2026, 11, 17)
DAYS = [date(2026, 11, d) for d in (9, 10, 11, 12, 13, 16)]


def bar(day: date) -> Bar:
    price = Decimal(600 + day.day)
    return Bar(day, price, price + 1, price - 1, price, 1000)


def refuse(_line: object, _day: date) -> Refused:
    return Refused("none")


def seeded(path: Path, planted: set[date]) -> Path:
    with bars.writing(path / bars.LIVE) as held:
        held.days(SPY, [bar(d) for d in DAYS if d not in planted])
    return path / bars.LIVE


def test_planted_gaps_are_backfilled_and_the_line_is_green(tmp_path: Path) -> None:
    path = seeded(tmp_path, {DAYS[1], DAYS[3]})
    said = quality.monitor(path, [SPY], lambda _l, d: [bar(d)], lambda _l, _d: Refused("no"), TODAY)
    assert said == "quality: green, 1 lines, 2 bars backfilled, 0 rolled up"
    assert quality.gaps(path, [SPY], TODAY) == []


def test_a_gap_no_source_fills_is_named_red(tmp_path: Path) -> None:
    path = seeded(tmp_path, {DAYS[2]})
    said = quality.monitor(path, [SPY], refuse, refuse, TODAY)
    assert said.startswith("quality: RED, 0 bars backfilled, 0 rolled up; SPY: 1 sessions missing")


def test_rolled_bars_are_built_and_a_pulled_bar_that_differs_is_red(tmp_path: Path) -> None:
    path = seeded(tmp_path, set())
    start = datetime(2026, 11, 16, 15, 0, tzinfo=UTC)
    price = Decimal(600)
    half = [Timed("30m", start + timedelta(minutes=30 * n), price, price + 1, price - 1, price, 5)
            for n in range(2)]  # fmt: skip
    with bars.writing(path, bars.Source.IBKR) as held:
        held.timed(SPY, "30m", half)
    first = quality.monitor(path, [SPY], refuse, refuse, TODAY)
    assert first == "quality: green, 1 lines, 0 bars backfilled, 2 rolled up"
    odd = Timed("1h", start, price, price + 3, price - 1, price + 2, 10)
    with bars.writing(path, bars.Source.IBKR) as held:
        held.timed(SPY, "1h", [odd])
    assert "rolled and held differ" in quality.monitor(path, [SPY], refuse, refuse, TODAY)


def test_a_session_with_no_30m_bar_between_held_ones_is_named_red(tmp_path: Path) -> None:
    path = seeded(tmp_path, set())
    price = Decimal(600)
    ends = [datetime(2026, 11, d, 15, 0, tzinfo=UTC) for d in (10, 13)]
    with bars.writing(path, bars.Source.IBKR) as held:
        held.timed(SPY, "30m", [Timed("30m", t, price, price, price, price, 5) for t in ends])
    assert quality.thin(path, SPY, TODAY) == [
        "SPY: 2 sessions with no 30m bar, the first 2026-11-11"
    ]
