"""The one price store: what enters it is clean, and a line it cannot clean is parked."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from desk import store, venues
from desk.lines import Line
from desk.store import Bar

US, UK = Line("AAA", "US", "USD"), Line("BBB", "LSE", "GBP")
DAY = date(2025, 11, 17)  #: a Monday; the last session before it is Friday the 14th


def _bars(line: Line, first: date = date(2025, 11, 3)) -> tuple[Bar, ...]:
    days = venues.sessions(line.venue, first, date(2025, 11, 14))
    return tuple(
        Bar(d, Decimal(50 + n % 3), Decimal(52 + n % 3), Decimal(49 + n % 3), Decimal(51), 900)
        for n, d in enumerate(days)
    )


def _parked(tmp_path: Path, bars: tuple[Bar, ...], line: Line = US) -> list[str]:
    return [p.reason for p in store.prepare(tmp_path, {line: bars}, DAY)]


def test_a_clean_line_is_stored_exactly_and_not_parked(tmp_path: Path) -> None:
    assert store.prepare(tmp_path, {US: _bars(US), UK: _bars(UK)}, DAY) == ()
    assert store.read(tmp_path, US.symbol) == _bars(US)
    assert store.read(tmp_path, UK.symbol) == _bars(UK)


BAD_BARS: dict[str, Callable[[Bar], Bar]] = {
    "the high is below the low": lambda b: replace(b, high=b.low - 1),
    "the close is outside the range": lambda b: replace(b, close=b.high + 1),
    "a price is not positive": lambda b: replace(b, low=Decimal(0)),
    "the volume is negative": lambda b: replace(b, volume=-1),
    "the price is in the wrong unit": lambda b: replace(
        b, open=b.open * 100, high=b.high * 100, low=b.low * 100, close=b.close * 100
    ),
}


@pytest.mark.parametrize("fault", sorted(BAD_BARS))
def test_a_bad_bar_never_enters_and_its_line_is_parked(tmp_path: Path, fault: str) -> None:
    bars = list(_bars(US))
    bars[4] = BAD_BARS[fault](bars[4])
    reasons = _parked(tmp_path, tuple(bars))
    assert len(reasons) == 1 and "2025-11-07" in reasons[0]
    assert store.read(tmp_path, US.symbol) == _bars(US)[:4] + _bars(US)[5:]


def test_one_date_with_two_different_bars_keeps_neither(tmp_path: Path) -> None:
    bars = _bars(US)
    reasons = _parked(tmp_path, (*bars, replace(bars[2], close=bars[2].close + 1)))
    assert len(reasons) == 1 and "2025-11-05" in reasons[0]
    assert bars[2].day not in [b.day for b in store.read(tmp_path, US.symbol)]


@pytest.mark.parametrize(
    ("line", "on"),
    [(US, date(2025, 11, 8)), (US, date(2025, 11, 27)), (UK, date(2025, 12, 26)), (US, DAY)],
    ids=["a Saturday", "a US holiday", "a UK holiday", "the day not yet traded"],
)
def test_a_bar_on_a_day_the_venue_was_shut_is_refused(tmp_path: Path, line: Line, on: date) -> None:
    bars = _bars(line)
    reasons = _parked(tmp_path, (*bars, replace(bars[0], day=on)), line)
    assert len(reasons) == 1 and str(on) in reasons[0]
    assert store.read(tmp_path, line.symbol) == bars


def test_a_uk_holiday_is_no_gap_in_a_us_line(tmp_path: Path) -> None:
    us, uk = _bars(US, date(2025, 8, 20)), _bars(UK, date(2025, 8, 20))
    assert date(2025, 8, 25) in [b.day for b in us]
    assert date(2025, 8, 25) not in [b.day for b in uk]
    assert store.prepare(tmp_path, {US: us, UK: uk}, DAY) == ()


@pytest.mark.parametrize(
    "kept",
    [_bars(US)[:-1], (*_bars(US)[:3], *_bars(US)[4:]), ()],
    ids=["stale: the last session missing", "a hole in the middle", "no bars at all"],
)
def test_a_line_missing_a_session_is_parked(tmp_path: Path, kept: tuple[Bar, ...]) -> None:
    reasons = _parked(tmp_path, kept)
    assert len(reasons) == 1 and "missing" in reasons[0]


def test_a_parked_line_comes_back_when_its_bars_are_clean(tmp_path: Path) -> None:
    assert _parked(tmp_path, _bars(US)[:-1])
    assert _parked(tmp_path, _bars(US)) == []
    assert store.read(tmp_path, US.symbol) == _bars(US)
