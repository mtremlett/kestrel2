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
    "the price is in the wrong unit": lambda b: _scaled(b, Decimal(100)),
    "only the high is in the wrong unit": lambda b: replace(b, high=b.high * 100),
    "only the low is in the wrong unit": lambda b: replace(b, low=b.low / 100),
    "a price is not a number": lambda b: replace(b, high=Decimal("NaN")),
    "a price is infinite": lambda b: replace(b, high=Decimal("Infinity")),
}


def _scaled(bar: Bar, by: Decimal) -> Bar:
    return replace(
        bar, open=bar.open * by, high=bar.high * by, low=bar.low * by, close=bar.close * by
    )


@pytest.mark.parametrize("at", [0, 4, -1], ids=["the first bar", "a middle bar", "the last bar"])
@pytest.mark.parametrize("fault", sorted(BAD_BARS))
def test_a_bad_bar_never_enters_and_its_line_is_parked(tmp_path: Path, fault: str, at: int) -> None:
    bars = list(_bars(US))
    bars[at] = BAD_BARS[fault](bars[at])
    reasons = _parked(tmp_path, tuple(bars))
    assert len(reasons) == 1 and str(bars[at].day) in reasons[0]
    assert store.read(tmp_path, US.symbol) == tuple(b for b in _bars(US) if b.day != bars[at].day)


def test_a_step_in_the_price_parks_the_line_and_keeps_every_bar(tmp_path: Path) -> None:
    bars = (*_bars(US)[:5], *(_scaled(b, Decimal("0.5")) for b in _bars(US)[5:]))
    reasons = _parked(tmp_path, bars)
    assert len(reasons) == 1 and str(bars[5].day) in reasons[0] and "split" in reasons[0]
    assert store.read(tmp_path, US.symbol) == bars


def test_two_bars_out_of_line_are_both_kept_for_no_one_can_tell_which_is_wrong(
    tmp_path: Path,
) -> None:
    bars = (*_bars(US)[-2:-1], _scaled(_bars(US)[-1], Decimal(100)))
    reasons = _parked(tmp_path, bars)
    assert len(reasons) == 1 and str(bars[1].day) in reasons[0] and "split" in reasons[0]
    assert store.read(tmp_path, US.symbol) == bars


def test_a_step_known_to_be_a_real_move_is_kept_and_not_parked(tmp_path: Path) -> None:
    bars = (*_bars(US)[:5], *(_scaled(b, Decimal("0.5")) for b in _bars(US)[5:]))
    line = replace(US, real_moves=frozenset({(bars[5].day, bars[5].close)}))
    assert _parked(tmp_path, bars, line) == []
    assert store.read(tmp_path, US.symbol) == bars


@pytest.mark.parametrize("at", [5, -1], ids=["a middle bar", "the newest bar"])
def test_a_recorded_real_move_lets_through_only_its_own_close(tmp_path: Path, at: int) -> None:
    bars = list(_bars(US))
    line = replace(US, real_moves=frozenset({(bars[at].day, bars[at].close / 2)}))
    bars[at] = _scaled(bars[at], Decimal(100))
    reasons = _parked(tmp_path, tuple(bars), line)
    assert len(reasons) == 1 and str(bars[at].day) in reasons[0]
    assert bars[at] not in store.read(tmp_path, US.symbol)


def test_a_line_that_cannot_be_read_never_stops_the_others(tmp_path: Path) -> None:
    early = replace(_bars(US)[0], day=date(2009, 12, 31))
    parked = store.prepare(tmp_path, {US: (early, *_bars(US)), UK: _bars(UK)}, DAY)
    assert [p.symbol for p in parked] == [US.symbol] and "2009-12-31" in parked[0].reason
    assert store.read(tmp_path, US.symbol) == _bars(US)
    assert store.read(tmp_path, UK.symbol) == _bars(UK)


def test_a_line_on_a_venue_without_a_calendar_cannot_be_made() -> None:
    with pytest.raises(ValueError, match="NYSE"):
        Line("CCC", "NYSE", "USD")


def test_one_bar_given_twice_is_kept_once_and_its_line_parked(tmp_path: Path) -> None:
    bars = _bars(US)
    reasons = _parked(tmp_path, (*bars, bars[2]))
    assert len(reasons) == 1 and "2025-11-05" in reasons[0]
    assert store.read(tmp_path, US.symbol) == bars


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
    ("kept", "named"),
    [
        (_bars(US)[:-1], "2025-11-14"),
        ((*_bars(US)[:3], *_bars(US)[4:]), "2025-11-06"),
        ((), "every session"),
    ],
    ids=["stale: the last session missing", "a hole in the middle", "no bars at all"],
)
def test_a_line_missing_a_session_is_parked(
    tmp_path: Path, kept: tuple[Bar, ...], named: str
) -> None:
    reasons = _parked(tmp_path, kept)
    assert len(reasons) == 1 and "missing" in reasons[0] and named in reasons[0]


def test_a_parked_line_comes_back_when_its_bars_are_clean(tmp_path: Path) -> None:
    assert _parked(tmp_path, _bars(US)[:-1])
    assert _parked(tmp_path, _bars(US)) == []
    assert store.read(tmp_path, US.symbol) == _bars(US)
