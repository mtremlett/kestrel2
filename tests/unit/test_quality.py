"""The monitor: planted gaps filled and re-audited green; a gap no source fills named red."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from desk import bars, quality
from desk.lines import LINES
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
    assert said == "quality: green, 1 lines, 2 bars backfilled"
    assert quality.gaps(path, [SPY], TODAY) == []


def test_a_gap_no_source_fills_is_named_red(tmp_path: Path) -> None:
    path = seeded(tmp_path, {DAYS[2]})
    said = quality.monitor(path, [SPY], refuse, refuse, TODAY)
    assert said.startswith(
        "quality: RED, 0 bars backfilled; SPY: 1 sessions missing, the first 2026-11-11"
    )
