"""The one calendar: each venue's shut weekdays, against the exchanges' published lists."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from desk import venues

PUBLISHED = {
    ("LSE", 2024): "01-01 03-29 04-01 05-06 05-27 08-26 12-25 12-26",
    ("LSE", 2025): "01-01 04-18 04-21 05-05 05-26 08-25 12-25 12-26",
    ("LSE", 2026): "01-01 04-03 04-06 05-04 05-25 08-31 12-25 12-28",
    ("LSE", 2022): "01-03 04-15 04-18 05-02 06-02 06-03 08-29 09-19 12-26 12-27",
    ("LSE", 2020): "01-01 04-10 04-13 05-08 05-25 08-31 12-25 12-28",
    ("US", 2024): "01-01 01-15 02-19 03-29 05-27 06-19 07-04 09-02 11-28 12-25",
    ("US", 2025): "01-01 01-09 01-20 02-17 04-18 05-26 06-19 07-04 09-01 11-27 12-25",
    ("US", 2026): "01-01 01-19 02-16 04-03 05-25 06-19 07-03 09-07 11-26 12-25",
    ("LSE", 2011): "01-03 04-22 04-25 04-29 05-02 05-30 08-29 12-26 12-27",
    ("LSE", 2023): "01-02 04-07 04-10 05-01 05-08 05-29 08-28 12-25 12-26",
    ("US", 2018): "01-01 01-15 02-19 03-30 05-28 07-04 09-03 11-22 12-05 12-25",
    ("US", 2021): "01-01 01-18 02-15 04-02 05-31 07-05 09-06 11-25 12-24",
    ("US", 2022): "01-17 02-21 04-15 05-30 06-20 07-04 09-05 11-24 12-26",
    ("US", 2012): "01-02 01-16 02-20 04-06 05-28 07-04 09-03 10-29 10-30 11-22 12-25",
}


def _shut(venue: str, year: int) -> set[date]:
    first, last = date(year, 1, 1), date(year, 12, 31)
    weekdays = {
        first + timedelta(n)
        for n in range((last - first).days + 1)
        if (first + timedelta(n)).weekday() < 5
    }
    return weekdays - set(venues.sessions(venue, first, last))


@pytest.mark.parametrize(("venue", "year"), sorted(PUBLISHED))
def test_a_venue_is_shut_exactly_on_its_published_holidays(venue: str, year: int) -> None:
    expected = {date(year, int(d[:2]), int(d[3:])) for d in PUBLISHED[venue, year].split()}
    assert _shut(venue, year) == expected


def test_sessions_are_weekdays_in_order_and_inclusive() -> None:
    days = venues.sessions("US", date(2025, 11, 7), date(2025, 11, 17))
    assert days == (date(2025, 11, 7), *(date(2025, 11, d) for d in (10, 11, 12, 13, 14, 17)))


@pytest.mark.parametrize(
    ("venue", "first", "last"),
    [("LSE", date(2009, 12, 30), date(2010, 1, 5)), ("US", date(2027, 12, 30), date(2028, 1, 4))],
)
def test_a_year_the_calendar_does_not_know_is_refused(venue: str, first: date, last: date) -> None:
    with pytest.raises(ValueError, match="no calendar"):
        venues.sessions(venue, first, last)


def test_a_venue_the_calendar_does_not_know_is_refused() -> None:
    with pytest.raises(ValueError, match="no calendar"):
        venues.sessions("XETRA", date(2025, 1, 1), date(2025, 1, 31))
