"""The fast store: what is written is read back exactly, in whole rounds, by one writer and
many readers, and it is held to the three benchmarks the operator's need set (DAT-04). Each
evening's five-minute bars enter through the daily store's checks, for good (DAT-11)."""

from __future__ import annotations

import itertools
import sqlite3
import timeit
from collections.abc import Callable, Iterator
from contextlib import closing
from dataclasses import replace
from datetime import UTC, date, datetime, time, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from desk import bars
from desk.bars import Five, Source
from desk.lines import LINES, Line
from desk.store import Bar, Refused

US, UK = Line("BA", "US", "USD", 1), Line("BA", "LSE", "GBP", 1)  #: one symbol, two companies
NOON = datetime(2026, 11, 13, 12, 0, tzinfo=UTC)
NEXT, ELSEWHERE = NOON + timedelta(minutes=5), timezone(timedelta(hours=1))
TICK = timedelta(microseconds=1)
ODD = (Decimal("1E+3"), Decimal("123456.789012345678901"), Decimal("0.0001"), Decimal("0.10"))
#: A daily bar and a five-minute bar that the store keeps under one number, each in its span.
TWINS = (Bar(date.fromordinal(600), *ODD, 1), Five(bars.EPOCH + timedelta(seconds=600), *ODD, 2))
#: The benchmarks, in seconds, set on 13 November 2026 before the store was written.
ROUND, WEEK, HISTORY = 1.0, 0.050, 0.200


def _days(count: int) -> tuple[Bar, ...]:
    return tuple(Bar(date(2000, 1, 3) + timedelta(n), *ODD, 900 + n) for n in range(count))


def _fives(count: int) -> tuple[Five, ...]:
    """A line's newest five-minute bars up to NOON, a Friday, oldest first: 102 each weekday,
    from 08:00 to 16:30 UTC, as London trades."""
    marks = (NOON - timedelta(minutes=5 * n) for n in itertools.count())
    traded = (m for m in marks if m.weekday() < 5 and time(8) <= m.time() < time(16, 30))
    starts = reversed(list(itertools.islice(traded, count)))
    return tuple(Five(start, *ODD, 7 + n) for n, start in enumerate(starts))


def test_what_is_written_is_read_back_exactly_and_each_line_apart(tmp_path: Path) -> None:
    store, days, fives = tmp_path / "bars.db", _days(30), _fives(30)
    with bars.writing(store, Source.ARCHIVE) as round_:
        round_.daily(US, days[::-1])
        round_.five(US, fives[::-1])
        round_.daily(UK, (*days[:3], TWINS[0], Bar(date.max, *ODD, 3)))
        round_.five(UK, TWINS[1:])
    assert bars.daily(store, US) == days
    assert bars.daily(store, UK) == (TWINS[0], *days[:3], Bar(date.max, *ODD, 3))
    assert bars.five(store, US, fives[0].start, NEXT) == fives
    assert bars.five(store, US, fives[10].start, fives[20].start) == fives[10:20]
    assert bars.five(store, US, fives[9].start + TICK, fives[19].start + TICK) == fives[10:20]
    assert bars.five(store, UK, bars.EPOCH, NEXT) == TWINS[1:]
    read = bars.five(store, US, NOON, NEXT)[0]
    assert read.start.utcoffset() == timedelta(0)
    assert [str(p) for p in (read.open, read.high, read.low, read.close)] == [str(p) for p in ODD]
    with closing(sqlite3.connect(store)) as held:
        assert held.execute("PRAGMA journal_mode").fetchone() == ("wal",)


def test_a_history_is_replaced_whole_and_five_minute_bars_gather(tmp_path: Path) -> None:
    store, days, fives = tmp_path / "bars.db", _days(30), _fives(30)
    with bars.writing(store, Source.ARCHIVE) as round_:
        round_.daily(US, days)
        round_.daily(UK, days)
        round_.five(US, fives[:20])
        round_.five(UK, fives[:20])
    corrected = replace(fives[19], close=Decimal("9.5"))
    with bars.writing(store, Source.ARCHIVE) as round_:
        round_.daily(US, days[5:])
        round_.five(US, (corrected, *fives[20:]))
    assert bars.daily(store, US) == days[5:]
    assert bars.five(store, US, fives[0].start, NEXT) == (*fives[:19], corrected, *fives[20:])
    assert (bars.daily(store, UK), bars.five(store, UK, fives[0].start, NEXT)) == (days, fives[:20])
    with bars.writing(store, Source.ARCHIVE) as round_:
        with pytest.raises(ValueError, match="BA on US: its history gives a day twice"):
            round_.daily(US, (*days[:9], replace(days[0], volume=1)))
        round_.daily(UK, days[:9])
    assert (bars.daily(store, US), bars.daily(store, UK)) == (days[5:], days[:9])


def test_a_bar_is_kept_with_its_source_and_only_a_fresh_source_restates(tmp_path: Path) -> None:
    store, fives, one = tmp_path / "bars.db", _fives(2), ("1",) * 4
    with closing(sqlite3.connect(store)) as before:  # a store made before sources were kept
        before.execute(bars.SCHEMA[0].replace(" source TEXT NOT NULL,", ""))
        first = ("LSE", "BA", bars.FIVE, bars._seconds(fives[0].start), *one, 1)
        before.execute(bars.ADD.replace(", ?)", ")"), first)
        before.commit()
    held = Five(fives[0].start, Decimal(1), Decimal(1), Decimal(1), Decimal(1), 1)
    near, far = replace(held, close=Decimal("1.0001")), replace(fives[1], close=Decimal("0.2"))
    with bars.writing(store, Source.MATRICES) as round_:
        assert round_.apart(UK, [near, fives[1]]) == (1, 0)  # within a vendor's rounding
        assert round_.five(UK, [near, fives[1]]) == 1  # the moment held stays as it is
        over = replace(held, close=Decimal("1.00011"))
        assert round_.apart(UK, [over]) == (1, 1)
        with pytest.raises(ValueError, match="Stooq matrices is no fresh source"):
            round_.daily(UK, _days(1))
    assert bars.sources(store, UK, bars.FIVE) == {Source.ARCHIVE: 1, Source.MATRICES: 1}
    with bars.writing(store, Source.ARCHIVE) as round_:
        assert round_.apart(UK, [far, held]) == (1, 1)
        assert round_.five(UK, [far]) == 1
    assert bars.five(store, UK, bars.EPOCH, NEXT) == (held, far)
    assert bars.sources(store, UK, bars.FIVE) == {Source.ARCHIVE: 2}


def test_a_reader_sees_only_whole_rounds_and_a_second_writer_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store, days, fives = tmp_path / "bars.db", _days(30), _fives(30)
    monkeypatch.setattr(bars, "WAIT", 0.05)
    for _ in range(2):  # in the first round, and after it failed
        with (
            pytest.raises(RuntimeError, match="the first fails"),
            bars.writing(store, Source.ARCHIVE),
        ):
            with pytest.raises(FileNotFoundError, match="no round"):
                bars.daily(store, US)
            raise RuntimeError("the first fails")
    with bars.writing(store, Source.ARCHIVE) as round_:
        round_.daily(US, days[:5])
    with (
        pytest.raises(RuntimeError, match="the round fails"),
        bars.writing(store, Source.ARCHIVE) as round_,
    ):
        round_.daily(US, days)
        round_.five(US, fives)
        assert bars.daily(store, US) == days[:5]
        with pytest.raises(bars.NoRound, match="bars.db: no round begun: database is locked"):
            bars.writing(store, Source.ARCHIVE).__enter__()
        raise RuntimeError("the round fails")
    assert bars.daily(store, US) == days[:5]

    def dropped(_bar: Bar) -> Bar:
        round_._held.rollback()  # as SQLite itself does to a round when the disk fills
        raise OSError("the disk is full")

    with bars.writing(store, Source.ARCHIVE) as round_:
        round_.five(US, fives)
        with pytest.raises(OSError, match="the disk is full"):
            round_.daily(US, map(dropped, days))
        with pytest.raises(bars.NoRound, match="dropped this round"):
            round_.five(US, fives)
    with pytest.raises(LookupError, match="five-minute bars for BA on US"):
        bars.five(store, US, fives[0].start, NEXT)


def test_a_store_or_a_line_never_written_is_refused_not_read_as_empty(tmp_path: Path) -> None:
    store = tmp_path / "bars.db"
    with pytest.raises(FileNotFoundError, match="bars.db"):
        bars.daily(store, US)
    assert not store.exists()
    with bars.writing(store, Source.ARCHIVE) as round_:
        round_.daily(US, ())
        round_.five(UK, ())
    assert (bars.daily(store, US), bars.five(store, UK, NOON, NEXT)) == ((), ())
    for other in (UK, Line("BB", "US", "USD", 1)):
        with pytest.raises(LookupError, match=f"daily bars for {other.symbol} on {other.venue}"):
            bars.daily(store, other)
    for since, until in ((NOON.replace(tzinfo=None), NEXT), (NOON, NEXT.astimezone(ELSEWHERE))):
        with pytest.raises(ValueError, match="UTC"):
            bars.five(store, US, since, until)


def test_a_five_minute_bar_starts_on_a_five_minute_mark_in_utc() -> None:
    late = (NOON + timedelta(minutes=1), NOON + timedelta(seconds=1), NOON + TICK)
    for start in (NOON.replace(tzinfo=None), NOON.astimezone(ELSEWHERE), *late):
        with pytest.raises(ValueError, match="UTC"):
            Five(start, *ODD, 1)


def _fastest(job: Callable[[], object]) -> float:
    """The seconds the fastest of five runs took: the store's speed, not a busy machine's."""
    return min(timeit.repeat(job, number=1, repeat=5))


def test_the_deep_store_meets_its_three_benchmarks(tmp_path: Path) -> None:
    """Each of the twenty lines holds 7,000 daily bars, the sessions of 27 years, and 26,010
    five-minute bars, a year of London's sessions: the week is read hot from on top of every
    older bar, archived beneath it in the one file."""
    store, days, fives = tmp_path / "bars.db", _days(7_000), _fives(26_010)
    with bars.writing(store, Source.ARCHIVE) as round_:
        for line in LINES:
            round_.daily(line, days)
            round_.five(line, fives)
    newest = [Five(NOON + timedelta(minutes=5 * n), *ODD, 1) for n in range(1, 6)]
    rounds = iter(newest)

    def a_round() -> None:
        bar = next(rounds)
        with bars.writing(store, Source.ARCHIVE) as round_:
            for line in LINES:
                round_.five(line, (bar,))

    def a_week() -> tuple[Five, ...]:
        return bars.five(store, LINES[7], NOON - timedelta(7), NEXT)

    round_took = _fastest(a_round)
    assert round_took < ROUND, f"a round of {len(LINES)} lines took {round_took:.3f}s"
    assert bars.five(store, LINES[19], NEXT, NEXT + timedelta(hours=1)) == tuple(newest)
    assert a_week() == fives[-511:]
    week_took = _fastest(a_week)
    assert week_took < WEEK, f"a week took {week_took:.3f}s"
    assert bars.daily(store, LINES[7]) == days
    history_took = _fastest(lambda: bars.daily(store, LINES[7]))
    assert history_took < HISTORY, f"a history took {history_took:.3f}s"


def _at(minutes: int, *prices: str, volume: int = 5, noon: datetime = NOON) -> Five:
    """A bar so many minutes after noon: its open, high, low and close, or 10, 11, 9 and 10."""
    open_, high, low, close = (*prices, *("10", "11", "9", "10")[len(prices) :])
    start = noon + timedelta(minutes=minutes)
    return Five(start, Decimal(open_), Decimal(high), Decimal(low), Decimal(close), volume)


def test_a_five_minute_bar_enters_through_the_checks_the_daily_store_makes() -> None:
    eve = datetime(2026, 12, 24, 12, 0, tzinfo=UTC)  #: a half-day: London shuts at 12:30
    line = replace(UK, suspended=frozenset({date(2026, 11, 12)}))
    stretched = replace(_at(5), open=Decimal("11.2"), high=Decimal("11.2"), low=Decimal("8.8"))
    stretched = replace(stretched, close=Decimal("8.8"))
    good = [_at(-240), _at(0), stretched, _at(40), _at(265), _at(25, noon=eve)]
    hours, price = "is outside the trading hours of the LSE calendar", "has a price or volume that"
    odd = {
        _at(-245): f"2026-11-13 07:55 {hours}",
        _at(270): f"2026-11-13 16:30 {hours}",
        _at(0, noon=NOON + timedelta(1)): f"2026-11-14 12:00 {hours}",
        _at(30, noon=eve): f"2026-12-24 12:30 {hours}",
        _at(0, noon=NOON - timedelta(1)): "2026-11-12 12:00 has a bar, yet BA records the day"
        " as suspended",
        _at(0, noon=NOON.replace(year=2030)): f"2030-11-13 12:00 {hours}",  # no calendar yet
        _at(10, "Infinity"): f"2026-11-13 12:10 {price} cannot be",
        _at(15, "10", "11", "0"): f"2026-11-13 12:15 {price} cannot be",
        _at(20, volume=-1): f"2026-11-13 12:20 {price} cannot be",
        _at(25, "11.4"): "2026-11-13 12:25 has an open or close outside its high and low",
        _at(30, "10", "8"): "2026-11-13 12:30 has an open or close outside its high and low",
        _at(45, "10.05", "10", "10.1", "10.05"): "2026-11-13 12:45 has an open or close outside"
        " its high and low",
    }
    given = [*odd, _at(35), _at(35, volume=6), _at(40), *good]
    given[given.index(stretched)] = _at(5, "11.2", "11", "9", "8.8")
    kept, faults = bars.checked(line, given[::-1])
    assert kept == good
    assert faults == sorted([*odd.values(), "2026-11-13 12:35 given 2 ways; none kept"])


def test_a_wrong_unit_is_not_kept_and_any_other_far_move_is_kept_as_a_fault() -> None:
    pence, tenth, double = ("1000", "1100", "900", "1000"), ("0.1",) * 4, ("20", "22", "18", "20")
    given = [_at(0, *pence), _at(5), _at(10), _at(15, *pence), _at(20), _at(25)]
    given += [_at(30, *double), _at(35, *pence), _at(40, *tenth), _at(45)]
    #: a spike, out of line with the bar before and the bar after; then a move of exactly JUMP
    given += [_at(50, "10", "30"), _at(55, "10", "11", "10"), _at(60, "16", "16", "10", "16")]
    kept, faults = bars.checked(UK, given)
    assert kept == [given[n] for n in (1, 2, 4, 5, 6, 9, 10, 11, 12)]
    unit = "is a hundredfold from the bars around it: a wrong unit"
    assert faults == [
        *(f"2026-11-13 12:{minute} {unit}" for minute in ("00", "15")),
        "2026-11-13 12:30 moved from 10 to 20",
        *(f"2026-11-13 12:{minute} {unit}" for minute in ("35", "40")),
        "2026-11-13 12:45 moved from 20 to 10",
        "2026-11-13 12:50 moved from 10 to 10",
        "2026-11-13 12:55 moved from 10 to 10",
    ]
    assert bars.checked(UK, [_at(0, *pence)]) == ([_at(0, *pence)], [])  # nothing to judge it by


def test_each_evenings_bars_are_kept_in_one_round_and_none_is_ever_thrown_away(
    tmp_path: Path,
) -> None:
    store, first, late = tmp_path / "bars.db", [_at(n) for n in range(0, 50, 5)], _at(180)
    gone = "the archive refused it: URLError: gone"
    assert bars.keep(store, {UK: first, US: Refused("URLError: gone")}) == {UK: (), US: (gone,)}
    restated, bad = replace(first[9], volume=99), replace(first[0], low=Decimal(0))
    evening = {UK: iter([restated, _at(50), bad, _at(270)]), US: [late, _at(0)]}
    assert bars.keep(store, evening) == {
        UK: (
            "2026-11-13 12:00 has a price or volume that cannot be",
            "2026-11-13 16:30 is outside the trading hours of the LSE calendar",
        ),
        US: ("2026-11-13 12:00 is outside the trading hours of the US calendar",),
    }
    held = (*first[:9], restated, _at(50))

    def cut() -> Iterator[Five]:
        yield _at(185)
        raise OSError("the answer was cut short")

    with pytest.raises(OSError, match="cut short"):
        bars.keep(store, {UK: [_at(55)], US: cut()})
    assert bars.keep(store, {UK: Refused("URLError: gone"), US: ()}) == {UK: (gone,), US: ()}
    pence = [_at(n, "1000", "1100", "900", "1000") for n in (0, 5, 55)]  # the whole answer
    unit = "is a hundredfold from the bars around it: a wrong unit"
    assert bars.keep(store, {UK: pence}) == {
        UK: tuple(f"2026-11-13 12:{minute} {unit}" for minute in ("00", "05", "55"))
    }
    assert bars.five(store, UK, bars.EPOCH, NEXT + timedelta(1)) == held
    assert bars.five(store, US, bars.EPOCH, NEXT + timedelta(1)) == (late,)
