"""The one calendar: each venue's shut weekdays, half-days and hours, against the exchanges'
published lists."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta, timezone

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
    ("US", 1997): "01-01 02-17 03-28 05-26 07-04 09-01 11-27 12-25",
    ("LSE", 2027): "01-01 03-26 03-29 05-03 05-31 08-30 12-27 12-28",
    ("LSE", 2028): "01-03 04-14 04-17 05-01 05-29 08-28 12-25 12-26",
    ("LSE", 2029): "01-01 03-30 04-02 05-07 05-28 08-27 12-25 12-26",
    ("US", 2027): "01-01 01-18 02-15 03-26 05-31 06-18 07-05 09-06 11-25 12-24",
    ("US", 2028): "01-17 02-21 04-14 05-29 06-19 07-04 09-04 11-23 12-25",
    ("US", 2029): "01-01 01-15 02-19 03-30 05-28 06-19 07-04 09-03 11-22 12-25",
    ("US", 2001): "01-01 01-15 02-19 04-13 05-28 07-04 09-03 09-11 09-12 09-13 09-14 11-22 12-25",
    ("LSE", 1995): "01-02 04-14 04-17 05-08 05-29 08-28 12-25 12-26",
    ("LSE", 1999): "01-01 04-02 04-05 05-03 05-31 08-30 12-27 12-28 12-31",
    ("LSE", 2002): "01-01 03-29 04-01 05-06 06-03 06-04 08-26 12-25 12-26",
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
    [("LSE", date(1992, 12, 30), date(1993, 1, 5)), ("US", date(2029, 12, 30), date(2030, 1, 4))],
)
def test_a_year_the_calendar_does_not_know_is_refused(venue: str, first: date, last: date) -> None:
    with pytest.raises(ValueError, match="no calendar"):
        venues.sessions(venue, first, last)


def test_hours_before_2010_are_refused_though_the_days_are_known() -> None:
    assert venues.sessions("US", date(2004, 6, 10), date(2004, 6, 14)) == (
        date(2004, 6, 10),
        date(2004, 6, 14),
    )
    with pytest.raises(ValueError, match="no hours"):
        venues.hours("US", date(2004, 6, 10))
    # the archive's SPY holds exactly 2,515 daily bars in 2000-2009 (read 17 Nov 2026)
    assert len(venues.sessions("US", date(2000, 1, 1), date(2009, 12, 31))) == 2515


def test_a_venue_the_calendar_does_not_know_is_refused() -> None:
    with pytest.raises(ValueError, match="no calendar"):
        venues.sessions("XETRA", date(2025, 1, 1), date(2025, 1, 31))


#: The exchanges' own notices. London's half-days are Christmas Eve and New Year's Eve, or the
#: last working day before each; New York's the day after Thanksgiving, and 3 July and
#: Christmas Eve when they trade at all (2 July 2020 and 2026 are full days).
EARLY = {
    ("LSE", 2022): "12-23 12-30",
    ("LSE", 2023): "12-22 12-29",
    ("LSE", 2025): "12-24 12-31",
    ("LSE", 2026): "12-24 12-31",
    ("US", 2020): "11-27 12-24",
    ("US", 2023): "07-03 11-24",
    ("US", 2025): "07-03 11-28 12-24",
    ("US", 2026): "11-27 12-24",
    ("US", 2027): "11-26",
    ("US", 2028): "07-03 11-24",
    ("US", 2029): "07-03 11-23 12-24",
    ("LSE", 2027): "12-24 12-31",
    ("LSE", 2028): "12-22 12-29",
}
#: venue, day, then in UTC: the open, the end of continuous trading, the closing auction. Each
#: side of every clock change of 2025, and of 2021's, when the two countries are weeks apart;
#: the last two rows are the earliest day each clock rule can fall on.
HOURS = """
LSE 2025-01-15 08:00 16:30 16:35    LSE 2025-07-15 07:00 15:30 15:35
LSE 2025-03-28 08:00 16:30 16:35    LSE 2025-03-31 07:00 15:30 15:35
LSE 2025-10-24 07:00 15:30 15:35    LSE 2025-10-27 08:00 16:30 16:35
LSE 2021-03-26 08:00 16:30 16:35    LSE 2021-11-01 08:00 16:30 16:35
LSE 2025-12-24 08:00 12:30 12:35    LSE 2023-12-29 08:00 12:30 12:35
US 2025-03-07 14:30 21:00 21:00     US 2025-03-10 13:30 20:00 20:00
US 2025-10-31 13:30 20:00 20:00     US 2025-11-03 14:30 21:00 21:00
US 2021-03-12 14:30 21:00 21:00     US 2021-11-05 13:30 20:00 20:00
US 2025-07-03 13:30 17:00 17:00     US 2025-11-28 14:30 18:00 18:00
LSE 2018-03-26 07:00 15:30 15:35    LSE 2026-10-26 08:00 16:30 16:35
US 2026-03-09 13:30 20:00 20:00     US 2026-11-02 14:30 21:00 21:00
"""


@pytest.mark.parametrize(("venue", "year"), sorted(EARLY))
def test_a_venue_closes_early_exactly_on_its_published_half_days(venue: str, year: int) -> None:
    expected = {date(year, int(d[:2]), int(d[3:])) for d in EARLY[venue, year].split()}
    days = venues.sessions(venue, date(year, 1, 1), date(year, 12, 31))
    assert {day for day in days if venues.hours(venue, day).early} == expected


@pytest.mark.parametrize(
    "row", [" ".join(HOURS.split()[n : n + 5]) for n in range(0, len(HOURS.split()), 5)]
)
def test_a_session_opens_closes_and_holds_its_auction_at_the_published_times(row: str) -> None:
    venue, day, *times = row.split()
    opens, close, auction = (datetime.fromisoformat(f"{day}T{t}+00:00") for t in times)
    hours = venues.hours(venue, date.fromisoformat(day))
    assert (hours.open, hours.close, hours.auction) == (opens, close, auction)
    assert hours.open.tzinfo is UTC and hours.early == (close.hour in (12, 17, 18))


def test_a_day_the_venue_is_shut_has_no_hours() -> None:
    shut = [("LSE", date(2025, 12, 25)), ("US", date(2025, 7, 4)), ("US", date(2025, 7, 5))]
    for venue, day in shut:
        with pytest.raises(ValueError, match="does not trade"):
            venues.hours(venue, day)


def test_a_venue_is_open_from_its_open_to_its_closing_auction_both_included() -> None:
    hours = venues.hours("LSE", date(2025, 7, 15))
    second = timedelta(seconds=1)
    assert venues.open_at("LSE", hours.open) == venues.open_at("LSE", hours.auction) == hours
    assert venues.open_at("LSE", hours.open - second) is None
    assert venues.open_at("LSE", hours.auction + second) is None
    assert venues.open_at("US", hours.open) is None  # London's morning: New York is asleep
    tokyo = hours.auction.astimezone(timezone(timedelta(hours=9)))
    assert venues.open_at("LSE", tokyo) == hours  # the same moment, on a clock a day ahead
    assert venues.open_at("LSE", datetime(2025, 12, 25, 10, tzinfo=UTC)) is None
    assert venues.open_at("LSE", datetime(2025, 12, 24, 14, tzinfo=UTC)) is None  # a half-day
    assert venues.open_at("US", datetime(2025, 7, 5, 15, tzinfo=UTC)) is None  # a Saturday
    with pytest.raises(ValueError, match="no time zone"):
        venues.open_at("LSE", datetime(2025, 7, 15, 10))


def test_the_uk_clock_time_of_a_moment_either_side_of_both_2026_clock_changes() -> None:
    # (UTC moment, UK wall clock): the change falls at 01:00 UTC, on the moment, not the day
    known = [((2026, 3, 29, 0, 59), (0, 59, 0)), ((2026, 3, 29, 1, 0), (2, 0, 1)),
             ((2026, 10, 25, 0, 59), (1, 59, 1)), ((2026, 10, 25, 1, 0), (1, 0, 0)),
             ((2026, 7, 1, 12, 0), (13, 0, 1)), ((2026, 12, 1, 12, 0), (12, 0, 0))]  # fmt: skip
    for utc, (hour, minute, offset) in known:
        moment = datetime(*utc, tzinfo=UTC)
        got = venues.uk_time(moment)
        assert (got.hour, got.minute, got.utcoffset()) == (hour, minute, timedelta(hours=offset))
        assert got == moment
    with pytest.raises(ValueError, match="no time zone"):
        venues.uk_time(datetime(2026, 3, 29, 1, 0))


def test_the_calendar_names_an_event_day_and_a_plain_day_apart() -> None:
    assert venues.events("US", date(2026, 9, 16)) == ("FOMC",)
    assert venues.events("LSE", date(2026, 9, 17)) == ("BoE",)
    assert venues.events("US", date(2026, 12, 18)) == ("rebalance",)
    assert venues.events("LSE", date(2026, 9, 16)) == ()
    assert venues.events("US", date(2026, 9, 15)) == venues.events("US", date(2026, 11, 20)) == ()
    with pytest.raises(ValueError, match="no events"):
        venues.events("US", date(2027, 3, 17))
