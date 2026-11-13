"""The lists' past members: who was on a list on a past day, the ones still on it told from
the ones that have left, so a study of the past is not the survivors' alone."""

from __future__ import annotations

import hashlib
from datetime import date, timedelta

import pytest

from desk.lines import Line
from lab import members, universe
from lab.members import Change

TODAY = {"SP500": universe.SP500, "NASDAQ100": universe.NASDAQ100}


def _symbols(lines: tuple[Line, ...]) -> set[str]:
    return {line.symbol for line in lines}


def test_each_new_year_a_list_is_its_whole_membership_and_the_survivors_are_the_smaller_part() -> (
    None
):
    """The golden count: every member of each 1 January, and how many of them a study of
    today's list alone would have seen."""
    counted = {
        name: [
            (len(then.listed) + len(then.left), len(then.listed))
            for then in (members.on(name, date(year, 1, 1)) for year in range(2010, 2027))
        ]
        for name in TODAY
    }
    assert counted["SP500"] == [
        *((500, 279), (500, 287), (500, 296), (500, 307), (500, 315), (502, 322), (504, 337)),
        *((505, 356), (505, 377), (505, 389), (505, 406), (505, 416), (505, 426), (503, 440)),
        *((503, 453), (503, 467), (503, 484)),
    ]
    assert counted["NASDAQ100"] == [
        *((100, 32), (100, 33), (100, 35), (100, 38), (100, 41), (106, 43), (105, 45), (104, 48)),
        *((103, 54), (103, 57), (103, 59), (102, 63), (101, 69), (101, 73), (101, 78), (101, 83)),
        (101, 90),
    ]
    #: every change and its day, so that none is altered without this line saying so
    prints = {
        n: hashlib.sha256(repr(r.changes).encode()).hexdigest()[:12]
        for n, r in members.RECORDS.items()
    }
    assert prints == {"SP500": "9f8eb21b8207", "NASDAQ100": "a3760de517c5"}


@pytest.mark.parametrize("name", TODAY)
def test_a_member_still_listed_is_todays_line_and_one_that_left_is_only_a_name(name: str) -> None:
    for day in (members.FIRST, date(2015, 6, 30), date(2021, 12, 20), members.LAST):
        then = members.on(name, day)
        assert then.day == day
        assert set(then.listed) <= set(TODAY[name])
        assert not _symbols(then.listed) & set(then.left) and list(then.left) == sorted(then.left)
    assert (then.listed, then.left) == (TODAY[name], ())  #: the last day is the list itself


def test_a_change_takes_effect_on_its_day_and_not_the_day_before() -> None:
    meta, kenvue = date(2013, 12, 23), date(2026, 10, 30)
    before, after = (members.on("SP500", meta - timedelta(1)), members.on("SP500", meta))
    assert "META" not in _symbols(before.listed) and "META" in _symbols(after.listed)
    assert "TER" in _symbols(before.listed) and "TER" not in _symbols(after.listed)  #: it came back
    assert "KVUE" in members.on("SP500", kenvue - timedelta(1)).left
    assert "KVUE" not in members.on("SP500", kenvue).left
    assert "OKTA" not in _symbols(members.on("NASDAQ100", date(2020, 12, 20)).listed)
    assert "OKTA" in members.on("NASDAQ100", date(2020, 12, 21)).left  #: joined, and left since


def test_a_ticker_another_company_carries_today_is_not_taken_for_the_one_that_left() -> None:
    """Q was Qwest until 2011 and is another company today; Berkshire joined in February 2010."""
    first = members.on("SP500", members.FIRST)
    assert {"Q.2011", "JAVA", "BNI", "AGN", "AGN.2015", "CB.2016"} <= set(first.left)
    assert not {"Q", "BRK-B", "TSLA", "DELL", "CB"} & _symbols(first.listed)
    assert {"AAPL", "HWM", "MDLZ"} <= _symbols(first.listed) and "DD.2017" in first.left


def test_a_list_or_a_day_with_no_record_is_refused_never_guessed() -> None:
    for owed in ("FTSE350", "ETFS"):
        with pytest.raises(NotImplementedError, match=owed):
            members.on(owed, date(2020, 1, 1))
    with pytest.raises(KeyError):
        members.on("SP600", date(2020, 1, 1))
    for day in (members.FIRST - timedelta(1), members.LAST + timedelta(1)):
        with pytest.raises(ValueError, match="no record"):
            members.on("SP500", day)


def test_a_record_that_contradicts_the_list_or_itself_is_refused() -> None:
    day = date(2020, 1, 2)
    pair = universe.SP500[:1] + (universe.UNIVERSE[-1],)
    for wrong in (Change(day, "ZZZZ", joined=True), Change(day, pair[0].symbol, joined=False)):
        with pytest.raises(ValueError, match=wrong.symbol):
            members.Record(pair, (wrong,))
    for text in ("2020-01-02 -GONE 2020-01-03 -OLD", f"{members.LAST + timedelta(1)} -OLD"):
        with pytest.raises(ValueError, match="out of order"):
            members.Record(pair, members.changes(text))
    with pytest.raises(ValueError, match="before any day"):
        members.changes("+A 2020-01-02 -B")
    record = members.Record(
        pair, members.changes(f"2020-01-03 +{pair[1].symbol} -OLD 2020-01-02 -GONE")
    )
    assert record.symbols(day) == {pair[0].symbol, "OLD"}
    assert record.symbols(day - timedelta(1)) == {pair[0].symbol, "OLD", "GONE"}
