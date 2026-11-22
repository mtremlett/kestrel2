"""The research bars in the history database: what grid/store and the pound's table hold is
read back from it bar for bar, each under its source, and a second import adds nothing."""

from __future__ import annotations

import json
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from desk import bars, store, venues
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


def test_the_stores_bars_and_the_pound_enter_with_their_sources_and_a_second_import_adds_nothing(
    tmp_path: Path,
) -> None:
    root, path, table = tmp_path / "store", tmp_path / bars.LIVE, tmp_path / "pound.jsonl"
    stooq = _bars(LSE)[3:5]
    store.shelve(root / "LSE", LSE, stooq)  # the second source's fill of two days the archive lacks
    kept = {US: _bars(US), LSE: tuple(b for b in _bars(LSE) if b not in stooq)}
    for line, answer in kept.items():
        assert not store.prepare(root / line.venue, {line: answer}, END)
    table.write_text(
        "".join(json.dumps([d.isoformat(), "1.30"]) + "\n" for d in DAYS[US]), encoding="utf-8"
    )

    first = universe_history.run(root, path, table, [US, LSE], [LSE], END)
    assert "bars added" in first and "has no bar" not in first
    for line in (US, LSE):
        assert bars.daily(path, line) == _bars(line)
    assert bars.sources(path, LSE, bars.DAILY) == {
        Source.ARCHIVE: len(DAYS[LSE]) - 2,
        Source.MATRIX_DAILY: 2,
    }
    assert bars.sources(path, US, bars.DAILY) == {Source.ARCHIVE: len(DAYS[US])}
    assert [b.close for b in bars.daily(path, POUND)] == [Decimal("1.30")] * len(DAYS[US])
    assert universe_history.run(root, path, table, [US, LSE], [LSE], END).startswith(
        "research history: 0 bars added, 0 pound days added"
    )


def test_a_session_with_no_bar_is_named_never_invented(tmp_path: Path) -> None:
    root, path, table = tmp_path / "store", tmp_path / bars.LIVE, tmp_path / "pound.jsonl"
    kept = [b for b in _bars(LSE) if b.day != DAYS[LSE][4]]
    store.prepare(root / "LSE", {LSE: kept}, END)  # parks the line; its bars are kept
    table.write_text(json.dumps(["2026-10-30", "1.30"]) + "\n", encoding="utf-8")
    said = universe_history.run(root, path, table, [LSE], universe.YARDSTICKS, END)
    assert f"ISF has no bar on {DAYS[LSE][4]}" in said
    assert universe_history.missing(path, LSE, DAYS[LSE][-1] + timedelta(1)) == (DAYS[LSE][4],)


def test_the_pounds_noon_rates_fill_only_the_days_before_the_archives_first(tmp_path: Path) -> None:
    path, table = tmp_path / bars.LIVE, tmp_path / "pound.jsonl"
    table.write_text(json.dumps([DAYS[US][2].isoformat(), "1.30"]) + "\n", encoding="utf-8")
    universe_history.enter_pound(table, path)
    given = f"observation_date,DEXUSUK\n{DAYS[US][0]},1.50\n{DAYS[US][1]},\n{DAYS[US][2]},1.99\n"
    assert universe_history.enter_noon(path, given) == 1  # the blank day and the held day: none
    assert universe_history.enter_noon(path, given) == 0
    assert [(b.day, b.close) for b in bars.daily(path, POUND)] == [
        (DAYS[US][0], Decimal("1.50")),
        (DAYS[US][2], Decimal("1.30")),
    ]
    assert bars.sources(path, POUND, bars.DAILY) == {Source.FED_NOON: 1, Source.ARCHIVE: 1}


def test_research_reads_the_database_and_never_a_bar_held_only_in_a_csv(tmp_path: Path) -> None:
    root, path = tmp_path / "store", tmp_path / bars.LIVE
    held = _bars(US)
    store.prepare(
        root / "US", {US: held}, END
    )  # the CSV holds every day, the database all but the last
    with bars.writing(path, Source.ARCHIVE) as opened:
        opened.days(US, held[:-1])
    assert universe_parts.read(root, US).bars == held
    assert universe_parts.read_db(path, US).bars == held[:-1]
