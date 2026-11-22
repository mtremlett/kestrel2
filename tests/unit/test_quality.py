"""The monitor: planted gaps filled and re-audited green; a gap no source fills named red."""

from __future__ import annotations

import shutil
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest

from desk import bars, quality, venues
from desk.lines import LINES
from desk.spans import FIVE, Five, Timed
from desk.store import Bar, Refused

SPY = next(line for line in LINES if line.symbol == "SPY")
TODAY = date(2026, 11, 17)
NOW = datetime.combine(TODAY, time(), UTC)
DAYS = [date(2026, 11, d) for d in (9, 10, 11, 12, 13, 16)]


@pytest.fixture(autouse=True)
def roomy_drive(monkeypatch: pytest.MonkeyPatch) -> None:
    """The monitor's disk check never reads this PC's real drive."""
    monkeypatch.setattr(shutil, "disk_usage", lambda _p: SimpleNamespace(total=100, free=50))


def bar(day: date) -> Bar:
    price = Decimal(600 + day.day)
    return Bar(day, price, price + 1, price - 1, price, 1000)


def refuse(_line: object, _day: date) -> Refused:
    return Refused("none")


def seeded(path: Path, planted: set[date]) -> Path:
    with bars.writing(path / bars.LIVE, bars.Source.IBKR) as held:
        held.days(SPY, [bar(d) for d in DAYS if d not in planted])
    return path / bars.LIVE


def test_planted_gaps_are_backfilled_and_the_line_is_green(tmp_path: Path) -> None:
    path = seeded(tmp_path, {DAYS[1], DAYS[3]})
    said = quality.monitor(path, [SPY], lambda _l, d: [bar(d)], lambda _l, _d: Refused("no"), NOW)
    assert said == "quality: green, 1 lines, 2 bars backfilled, 1 rolled up, coverage 0.00"
    assert quality.gaps(path, [SPY], TODAY) == []
    assert quality.covered(path, [SPY], NOW) == ("coverage 0.00", True)


def test_a_gap_with_five_minute_bars_is_rolled_up_from_them(tmp_path: Path) -> None:
    path = seeded(tmp_path, {DAYS[2]})
    start = datetime.combine(DAYS[2], time(14), UTC)
    price = Decimal(600)
    with bars.writing(path, bars.Source.IBKR) as held:
        held.five(SPY, [Five(start, price, price + 1, price - 1, price, 10)])
    said = quality.monitor(path, [SPY], refuse, refuse, NOW)
    assert "1 bars backfilled" in said
    assert bars.sources(path, SPY, "daily")[bars.Source.ROLLUP_5M] == 1


def test_a_gap_no_source_fills_is_named_red(tmp_path: Path) -> None:
    path = seeded(tmp_path, {DAYS[2]})
    said = quality.monitor(path, [SPY], refuse, refuse, NOW)
    assert said.startswith(
        "quality: RED, 0 bars backfilled, 0 rolled up, coverage 0.00; SPY: 1 ses"
    )


def test_rolled_bars_are_built_and_a_pulled_bar_that_differs_is_red(tmp_path: Path) -> None:
    path = seeded(tmp_path, set())
    start = datetime(2026, 11, 16, 15, 0, tzinfo=UTC)
    price = Decimal(600)
    half = [Timed("30m", start + timedelta(minutes=30 * n), price, price + 1, price - 1, price, 5)
            for n in range(2)]  # fmt: skip
    with bars.writing(path, bars.Source.IBKR) as held:
        held.timed(SPY, "30m", half)
    first = quality.monitor(path, [SPY], refuse, refuse, NOW)
    assert first == "quality: green, 1 lines, 0 bars backfilled, 2 rolled up, coverage 0.00"
    odd = Timed("1h", start, price, price + 3, price - 1, price + 2, 10)
    with bars.writing(path, bars.Source.IBKR) as held:
        held.timed(SPY, "1h", [odd])
    assert "rolled and held differ" in quality.monitor(path, [SPY], refuse, refuse, NOW)


def test_a_session_with_no_30m_bar_between_held_ones_is_named_red(tmp_path: Path) -> None:
    path = seeded(tmp_path, set())
    price = Decimal(600)
    ends = [datetime(2026, 11, d, 15, 0, tzinfo=UTC) for d in (10, 13)]
    with bars.writing(path, bars.Source.IBKR) as held:
        held.timed(SPY, "30m", [Timed("30m", t, price, price, price, price, 5) for t in ends])
    assert quality.thin(path, SPY, TODAY) == [
        "SPY: 2 sessions with no 30m bar, the first 2026-11-11, no source holds them yet"
    ]


def test_every_short_timeframe_is_audited_for_thin_sessions(tmp_path: Path) -> None:
    path = seeded(tmp_path, set())
    price = Decimal(600)
    ends = [datetime(2026, 11, d, 15, 0, tzinfo=UTC) for d in (10, 13)]
    with bars.writing(path, bars.Source.IBKR) as held:
        held.timed(SPY, "1m", [Timed("1m", t, price, price, price, price, 5) for t in ends])
        held.five(SPY, [Five(t, price, price, price, price, 5) for t in ends])
    assert quality.thin(path, SPY, TODAY) == [
        "SPY: 2 sessions with no 1m bar, the first 2026-11-11, no source holds them yet",
        "SPY: 2 sessions with no five-minute bar, the first 2026-11-11, no source holds them yet",
    ]


def test_five_minute_volume_over_the_daily_is_named_red(tmp_path: Path) -> None:
    path = seeded(tmp_path, set())
    price = Decimal(600)
    marks = [datetime(2026, 11, d, 15, 0, tzinfo=UTC) for d in (10, 11)]
    with bars.writing(path, bars.Source.IBKR) as held:
        held.five(
            SPY,
            [
                Five(t, price, price, price, price, v)
                for t, v in zip(marks, (900, 2000), strict=True)
            ],
        )
    assert quality.volumes(path, SPY, TODAY) == [
        "SPY: 1 days with five-minute volume over the daily, first 2026-11-11"
    ]


def test_a_thin_session_says_which_finer_span_could_rebuild_it(tmp_path: Path) -> None:
    path = seeded(tmp_path, set())
    price = Decimal(600)
    ends = [datetime(2026, 11, d, 15, 0, tzinfo=UTC) for d in (10, 11, 12, 13)]
    with bars.writing(path, bars.Source.IBKR) as held:
        held.timed(SPY, "1m", [Timed("1m", t, price, price, price, price, 5) for t in ends])
        held.five(SPY, [Five(t, price, price, price, price, 5) for t in ends[::3]])
    assert quality.thin(path, SPY, TODAY) == [
        "SPY: 2 sessions with no five-minute bar, the first 2026-11-11, rollable from 1m"
    ]


def test_a_daily_series_mixing_adjustment_bases_is_named_red(tmp_path: Path) -> None:
    path = seeded(tmp_path, {DAYS[0]})
    assert quality.basis(path, SPY) == []
    with bars.writing(path, bars.Source.STOOQ_DAILY) as held:
        held.days(SPY, [bar(DAYS[0])])
    assert quality.basis(path, SPY) == [
        "SPY: daily series mixes bases: IBKR, old desk: stooq_store daily rows"
    ]


def test_todays_bar_is_green_once_its_venue_has_closed_and_named_while_open(tmp_path: Path) -> None:
    path = seeded(tmp_path, set())
    with bars.writing(path, bars.Source.IBKR) as held:
        held.days(SPY, [bar(TODAY)])
    closed = datetime(2026, 11, 17, 22, 15, tzinfo=UTC)
    assert quality.audit(path, SPY, closed) == []
    assert quality.audit(path, SPY, datetime(2026, 11, 17, 12, 0, tzinfo=UTC)) == [
        "SPY: 2026-11-17 is not a closed session on the US calendar, or too early"
    ]


def test_a_drive_with_under_a_tenth_free_turns_the_monitor_red(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    path = seeded(tmp_path, set())
    for free, red in ((5, True), (50, False)):
        monkeypatch.setattr(
            shutil, "disk_usage", lambda _p, f=free: SimpleNamespace(total=100, free=f)
        )
        said = quality.monitor(path, [SPY], refuse, refuse, NOW)
        assert ("disk: 5% free" in said) is red


def test_an_archive_refusing_for_six_hours_turns_the_monitor_red(tmp_path: Path) -> None:
    path = seeded(tmp_path, set())
    state = tmp_path / "archive.json"
    for since, red in ((NOW - timedelta(hours=7), True), (NOW - timedelta(hours=1), False)):
        state.write_text(f'{{"refusing_since": "{since.isoformat()}"}}', "utf-8")
        said = quality.monitor(path, [SPY], refuse, refuse, NOW)
        assert ("the price archive has refused every ask since" in said) is red


def _minutes(day: date, price: Decimal) -> list[Timed]:
    """Ten one-minute bars from the session's open."""
    open_ = venues.hours(SPY.venue, day).open
    return [Timed("1m", open_ + timedelta(minutes=n), price, price + 1, price - 1, price, 5)
            for n in range(10)]  # fmt: skip


def test_thin_five_minute_sessions_are_built_from_one_minute_bars(tmp_path: Path) -> None:
    path = seeded(tmp_path, set())
    sessions, price = DAYS[:4], Decimal(600)
    with bars.writing(path, bars.Source.IBKR) as held:
        held.timed(SPY, "1m", [m for d in sessions for m in _minutes(d, price)])
        pulled = [m for d in (sessions[0], sessions[3]) for m in _minutes(d, price)[::5]]
        held.five(SPY, [Five(m.start, price, price + 1, price - 1, price, 25) for m in pulled])
    said = quality.monitor(path, [SPY], refuse, refuse, NOW)
    assert "no five-minute bar" not in said and "rolled and held differ" not in said
    assert bars.sources(path, SPY, FIVE)[bars.Source.ROLLUP_1M] == 4
    odd = _minutes(DAYS[4], price)
    with bars.writing(path, bars.Source.IBKR) as held:
        held.timed(SPY, "1m", odd)
        held.five(SPY, [Five(odd[0].start, price, price + 7, price - 1, price, 25)])
    assert "rolled and held differ" in quality.monitor(path, [SPY], refuse, refuse, NOW)


def test_hover_judges_every_span_and_the_alarm_tells_only_of_change(tmp_path: Path) -> None:
    path = seeded(tmp_path, set())
    price, last = Decimal(600), datetime(2026, 11, 16, 15, tzinfo=UTC)
    spans = {
        "1m": last,
        "15m": last,
        "30m": last,
        "4h": last.replace(hour=12),
        "1h": last - timedelta(6),
    }
    with bars.writing(path, bars.Source.IBKR) as held:
        held.five(SPY, [Five(last, price, price, price, price, 5)])
        for span, at in spans.items():
            held.timed(SPY, span, [Timed(span, at, price, price, price, price, 5)])
    said, ok = quality.hover(path, [SPY], NOW)
    assert said.startswith("data quality: 75% fresh, 1 faults, 1 gaps, worst SPY/")
    assert not ok
    with bars.writing(path, bars.Source.IBKR) as held:
        held.timed(SPY, "1h", [Timed("1h", last, price, price, price, price, 5)])
        held.timed(
            SPY,
            "1wk",
            [Timed("1wk", datetime(2026, 11, 9, tzinfo=UTC), price, price, price, price, 5)],
        )
    shown = quality.table(path, [SPY], NOW)
    assert "1h: 100% fresh, 0 faults, 0 gaps" in shown
    assert shown.endswith("sources: IBKR paper 1; replaced: none")
    assert quality.hover(path, [SPY], NOW) == (
        "data quality: 100% fresh, 0 faults, 0 gaps, worst none",
        True,
    )
    holed = seeded(tmp_path / "holed", {date(2026, 11, 12)})
    assert quality.cell(holed, SPY, "daily", NOW) == "1 sessions missing, the first 2026-11-12"
    first = quality.alarm(None, None, False, "SPY/1h", NOW)
    assert first == (NOW, NOW, "data quality RED: SPY/1h")
    soon = NOW + timedelta(minutes=10)
    assert quality.alarm(*first[:2], False, "SPY/1h", soon) == (NOW, NOW, None)
    later = NOW + timedelta(minutes=31)
    assert quality.alarm(NOW, NOW, False, "x", later)[2] == "data quality still RED: x"
    assert quality.alarm(NOW, later, True, "", later + timedelta(minutes=9)) == (
        None,
        None,
        "back to green, red for 40 minutes",
    )
    assert quality.alarm(None, None, True, "", later) == (None, None, None)
    state = tmp_path / "alarm.json"
    sent = [
        quality.watch(state, "x", ok, at) for ok, at in ((False, NOW), (False, soon), (True, later))
    ]
    assert sent == ["data quality RED: x", None, "back to green, red for 31 minutes"]
    assert quality.watch(state, "", True, later) is None
    assert quality.announce("l", "x") == "l\nSEND: x\n"
    assert quality.announce("l", None) == "l\n"


def test_the_register_names_the_source_of_each_newest_bar(tmp_path: Path) -> None:
    path = seeded(tmp_path, set())
    assert quality.register(path, [SPY]) == ("IBKR paper 1", [])
    with bars.writing(path, bars.Source.BACKFILL) as held:
        held.days(SPY, [bar(date(2026, 11, 17))])
    assert quality.register(path, [SPY]) == ("archive, backfilled 1", ["SPY: archive, backfilled"])
