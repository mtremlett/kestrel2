"""The fast store: what is written is read back exactly, in whole rounds, by one writer and
many readers, and it is held to the three benchmarks the operator's need set (DAT-04)."""

from __future__ import annotations

import itertools
import sqlite3
import timeit
from collections.abc import Callable
from contextlib import closing
from dataclasses import replace
from datetime import UTC, date, datetime, time, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from desk import bars
from desk.bars import Five
from desk.lines import LINES, Line
from desk.store import Bar

US, UK = Line("BA", "US", "USD", 1), Line("BA", "LSE", "GBP", 1)  #: one symbol, two companies
NOON = datetime(2026, 11, 13, 12, 0, tzinfo=UTC)
NEXT, ELSEWHERE = NOON + timedelta(minutes=5), timezone(timedelta(hours=1))
ODD = (Decimal("0.1"), Decimal("1E+3"), Decimal("0.0001"), Decimal("123456.789012345"))
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
    with bars.writing(store) as round_:
        round_.daily(US, days[::-1])
        round_.five(US, fives[::-1])
        round_.daily(UK, days[:3])
        round_.five(UK, ())
    assert bars.daily(store, US) == days
    assert bars.daily(store, UK) == days[:3]
    assert bars.five(store, US, fives[0].start, NEXT) == fives
    assert bars.five(store, US, fives[10].start, fives[20].start) == fives[10:20]
    assert bars.five(store, UK, fives[0].start, NEXT) == ()
    read = bars.five(store, US, NOON, NEXT)[0]
    assert read.start.utcoffset() == timedelta(0)
    assert [str(p) for p in (read.open, read.high, read.low, read.close)] == [str(p) for p in ODD]
    with closing(sqlite3.connect(store)) as held:
        assert held.execute("PRAGMA journal_mode").fetchone() == ("wal",)


def test_a_history_is_replaced_whole_and_five_minute_bars_gather(tmp_path: Path) -> None:
    store, days, fives = tmp_path / "bars.db", _days(30), _fives(30)
    with bars.writing(store) as round_:
        round_.daily(US, days)
        round_.daily(UK, days)
        round_.five(US, fives[:20])
        round_.five(UK, fives[:20])
    corrected = replace(fives[19], close=Decimal("9.5"))
    with bars.writing(store) as round_:
        round_.daily(US, days[5:])
        round_.five(US, (corrected, *fives[20:]))
    assert bars.daily(store, US) == days[5:]
    assert bars.five(store, US, fives[0].start, NEXT) == (*fives[:19], corrected, *fives[20:])
    assert bars.daily(store, UK) == days
    assert bars.five(store, UK, fives[0].start, NEXT) == fives[:20]
    with pytest.raises(sqlite3.IntegrityError), bars.writing(store) as round_:
        round_.daily(US, (days[0], replace(days[0], volume=1)))
    assert bars.daily(store, US) == days[5:]


def test_a_reader_sees_only_whole_rounds_and_a_second_writer_is_refused(tmp_path: Path) -> None:
    store, days, fives = tmp_path / "bars.db", _days(30), _fives(30)
    with bars.writing(store) as round_:
        round_.daily(US, days[:5])
    with pytest.raises(RuntimeError, match="the round fails"), bars.writing(store) as round_:
        round_.daily(US, days)
        round_.five(US, fives)
        assert bars.daily(store, US) == days[:5]
        with pytest.raises(bars.Busy, match="another writer"), bars.writing(store):
            pass
        raise RuntimeError("the round fails")
    assert bars.daily(store, US) == days[:5]
    with pytest.raises(LookupError, match="five-minute bars for BA on US"):
        bars.five(store, US, fives[0].start, NEXT)


def test_a_store_or_a_line_never_written_is_refused_not_read_as_empty(tmp_path: Path) -> None:
    store = tmp_path / "bars.db"
    with pytest.raises(FileNotFoundError, match="bars.db"):
        bars.daily(store, US)
    assert not store.exists()
    with bars.writing(store) as round_:
        round_.daily(US, ())
    assert bars.daily(store, US) == ()
    with pytest.raises(LookupError, match="daily bars for BA on LSE"):
        bars.daily(store, UK)
    with pytest.raises(ValueError, match="UTC"):
        bars.five(store, US, NOON.replace(tzinfo=None), NEXT)
    with pytest.raises(ValueError, match="UTC"):
        bars.five(store, US, NOON, NEXT.astimezone(ELSEWHERE))


def test_a_five_minute_bar_starts_on_a_five_minute_mark_in_utc() -> None:
    zones = (NOON.replace(tzinfo=None), NOON.astimezone(ELSEWHERE))
    late = (timedelta(minutes=1), timedelta(seconds=1), timedelta(microseconds=1))
    for start in (*zones, *(NOON + by for by in late)):
        with pytest.raises(ValueError, match="UTC"):
            Five(start, *ODD, 1)


def _fastest(job: Callable[[], object]) -> float:
    """The seconds the fastest of three runs took: the store's speed, not a busy machine's."""
    return min(timeit.repeat(job, number=1, repeat=3))


def test_the_deep_store_meets_its_three_benchmarks(tmp_path: Path) -> None:
    """Each of the twenty lines holds 7,000 daily bars, the sessions of 27 years, and 6,120
    five-minute bars, London's sixty sessions that the archive keeps."""
    store, days, fives = tmp_path / "bars.db", _days(7_000), _fives(6_120)
    with bars.writing(store) as round_:
        for line in LINES:
            round_.daily(line, days)
            round_.five(line, fives)
    newest = [Five(NOON + timedelta(minutes=5 * n), *ODD, 1) for n in range(1, 4)]
    rounds = iter(newest)

    def a_round() -> None:
        bar = next(rounds)
        with bars.writing(store) as round_:
            for line in LINES:
                round_.five(line, (bar,))

    def a_week() -> tuple[Five, ...]:
        return bars.five(store, LINES[7], NOON - timedelta(7), NEXT)

    assert (seconds := _fastest(a_round)) < ROUND, f"a round of {len(LINES)} took {seconds:.3f}s"
    assert bars.five(store, LINES[19], NEXT, NEXT + timedelta(hours=1)) == tuple(newest)
    assert a_week() == fives[-511:]
    assert (seconds := _fastest(a_week)) < WEEK, f"a week took {seconds:.3f}s"
    assert bars.daily(store, LINES[7]) == days
    seconds = _fastest(lambda: bars.daily(store, LINES[7]))
    assert seconds < HISTORY, f"a history took {seconds:.3f}s"
