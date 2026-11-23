"""The research bars in the history database: what grid/store holds is
read back from it bar for bar, each under its source, and a second import adds nothing."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from desk import bars, venues
from desk.bars import Source
from desk.lines import POUND, Line
from desk.store import Bar
from lab import universe, universe_history, universe_parts

END = date(2026, 11, 2)
US, LSE = Line("AAPL", "US", "USD", 1), Line("ISF", "LSE", "GBP", 1)
DAYS = {
    line: venues.sessions(line.venue, date(2026, 10, 19), date(2026, 10, 30)) for line in (US, LSE)
}


def _bars(line: Line) -> tuple[Bar, ...]:
    return tuple(
        Bar(d, Decimal(10 + n), Decimal(12 + n), Decimal(9 + n), Decimal(11 + n), 100 + n)
        for n, d in enumerate(DAYS[line])
    )


def test_a_missing_session_is_named_and_a_complete_line_is_not(tmp_path: Path) -> None:
    path = tmp_path / bars.LIVE
    with bars.writing(path, Source.ARCHIVE) as opened:  # ISF lacks its fifth session
        opened.days(LSE, [b for b in _bars(LSE) if b.day != DAYS[LSE][4]])
        opened.days(US, _bars(US))
    first = universe_history.run(path, universe.YARDSTICKS, END)
    assert f"research history; ISF has no bar on {DAYS[LSE][4]}" in first
    assert universe_history.missing(path, LSE, DAYS[LSE][-1] + timedelta(1)) == (DAYS[LSE][4],)
    assert universe_history.run(path, [US], END) == "research history"


def test_the_pounds_noon_rates_fill_only_the_days_before_the_archives_first(tmp_path: Path) -> None:
    path, one = tmp_path / bars.LIVE, Decimal("1.30")
    with bars.writing(path, Source.ARCHIVE) as opened:
        opened.days(POUND, [Bar(DAYS[US][2], one, one, one, one, 0)])
    given = f"observation_date,DEXUSUK\n{DAYS[US][0]},1.50\n{DAYS[US][1]},\n{DAYS[US][2]},1.99\n"
    assert universe_history.enter_noon(path, given) == 1  # the blank day and the held day: none
    assert universe_history.enter_noon(path, given) == 0
    assert [(b.day, b.close) for b in bars.daily(path, POUND)] == [
        (DAYS[US][0], Decimal("1.50")),
        (DAYS[US][2], Decimal("1.30")),
    ]
    assert bars.sources(path, POUND, bars.DAILY) == {Source.FED_NOON: 1, Source.ARCHIVE: 1}


def test_research_reads_the_database_and_names_a_line_it_lacks(tmp_path: Path) -> None:
    path = tmp_path / bars.LIVE
    with bars.writing(path, Source.ARCHIVE) as opened:
        opened.days(US, _bars(US))
    assert universe_parts.read(path, US).bars == _bars(US)
    with pytest.raises(FileNotFoundError, match="ISF on LSE"):
        universe_parts.read(path, LSE)
