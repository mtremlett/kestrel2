"""The old desk's stores as a head start: its five-minute bars are read, never written, and
enter the fast store only where a fresh daily bar vouches for them and the store's own checks
pass; a fresh bar wins, and each bar that differs from one held is counted."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable, Mapping
from contextlib import closing
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import numpy as np
import pytest

from desk import archive, bars, store, venues
from desk.bars import Five, Source
from desk.lines import LINES, Line
from desk.store import Bar, Refused
from lab import headstart
from lab.headstart import Adopted

US, UK = Line("BA", "US", "USD", 1), Line("BA", "LSE", "GBP", 1)  #: one symbol, two companies
NOON = datetime(2026, 11, 13, 12, 0, tzinfo=UTC)  #: a Friday; the Thursday has no daily bar
DAY = Bar(NOON.date(), Decimal(10), Decimal(11), Decimal(9), Decimal(10), 500)
PENCE = "1000 1100 900 1000"
TABLE = "CREATE TABLE ohlcv (ticker, timeframe, ts, open, high, low, close, volume)"


def _five(start: datetime, prices: str = "10 11 9 10", volume: int = 5) -> Five:
    open_, high, low, close = map(Decimal, prices.split())
    return Five(start, open_, high, low, close, volume)


def _at(minutes: int, prices: str = "10 11 9 10") -> Five:
    """A bar so many minutes after noon: its open, high, low and close, or 10, 11, 9 and 10."""
    return _five(NOON + timedelta(minutes=minutes), prices)


def _matrix(folder: Path, name: str, walls: list[datetime], rows: list[list[float]]) -> None:
    stamps = [(wall - bars.EPOCH) // timedelta(milliseconds=1) for wall in walls]
    np.save(folder / f"{name}_5m_ts.npy", np.array(stamps, dtype=np.int64))
    np.save(folder / f"{name}_5m_ohlcv.npy", np.array(rows, dtype=np.float32).T)


def _database(path: Path, rows: Iterable[tuple[object, ...]]) -> None:
    with closing(sqlite3.connect(path)) as made:
        made.execute(TABLE)
        made.executemany("INSERT INTO ohlcv VALUES (?, ?, ?, ?, ?, ?, ?, ?)", rows)
        made.commit()


def test_the_matrices_are_read_off_warsaws_clock_and_a_missing_line_is_refused_alone(
    tmp_path: Path,
) -> None:
    summer = datetime(2026, 7, 15, 9, 0, tzinfo=UTC)
    rows = [
        [96.6, 96.7, 96.5, 96.65, 1200],
        [1, float("nan"), 1, 1, 1],
        [110.6, 110.7, 110.5, 110.6, 7],
    ]
    walls = [summer, summer + timedelta(minutes=5), NOON + timedelta(hours=1)]
    _matrix(tmp_path, "BA.UK", walls, rows)
    read = archive.gather([UK, US], tmp_path, headstart.matrices)
    assert read[UK] == (
        _five(summer - timedelta(hours=2), "96.6 96.7 96.5 96.65", 1200),
        _five(NOON, "110.6 110.7 110.5 110.6", 7),
    )
    missing = read[US]
    assert isinstance(missing, Refused) and "FileNotFoundError" in missing.reason


def test_the_old_database_is_read_and_nothing_is_written_to_it_or_beside_it(
    tmp_path: Path,
) -> None:
    old, stamp = tmp_path / "old.db", "2026-07-29T15:25:00+00:00"
    rows: list[tuple[object, ...]] = [
        ("BA.L", "5m", stamp, 1.0818000030517578, 1.25, 1.0, 1.125, 5475.0),
        ("BA.L", "5m", "2026-07-29T15:20:00+00:00", 1.0, 1.0, 1.0, None, 1.0),
        ("BA.L", "1d", stamp, 2.0, 2.0, 2.0, 2.0, 1.0),
        ("BA", "5m", stamp, 3, 3, 3, 3, 1),
    ]
    _database(old, rows)
    with closing(sqlite3.connect(old)) as logged:  # as the old desk left it: kept with a log
        logged.execute("PRAGMA journal_mode = WAL")
    before = sorted(tmp_path.iterdir())
    held = _five(datetime.fromisoformat(stamp), "1.0818000030517578 1.25 1.0 1.125", 5475)
    assert headstart.database(UK, old) == (held,)
    assert headstart.database(US, old) == (_five(datetime.fromisoformat(stamp), "3 3 3 3", 1),)
    with pytest.raises(ValueError, match="old.db holds no five-minute bar of 3LGO.L"):
        headstart.database(LINES[0], old)
    with pytest.raises(sqlite3.OperationalError, match="unable to open"):
        headstart.database(UK, tmp_path / "absent.db")
    assert sorted(tmp_path.iterdir()) == before
    (tmp_path / "old.db-wal").write_bytes(b"a change not yet folded in")
    with pytest.raises(ValueError, match="old.db is still being written"):
        headstart.database(UK, old)


def test_an_old_bar_enters_only_vouched_for_and_checked_and_a_fresh_bar_wins(
    tmp_path: Path,
) -> None:
    store, fresh = tmp_path / "bars.db", [_at(0), _at(20, "10 11 9 9.5")]
    with bars.writing(store) as round_:
        round_.five(UK, fresh)
    yesterday = _five(NOON - timedelta(1))
    given = [_at(0), _at(5, PENCE), _at(10, "10 12 9 10"), yesterday, _at(20), _at(-300)]
    faults = (
        "1 bars on a day with no fresh daily bar to vouch for them",
        "1 bars outside their day's fresh high and low",
        "2026-11-13 07:00 is outside the trading hours of the LSE calendar",
    )
    unproven = "no bar is held for any of their moments to prove their clock; none kept"
    daily = {UK: [DAY], US: [DAY]}
    for filled in (1, 0):  # the same store read again fills nothing more
        answers: Mapping[Line, Iterable[Five] | Refused] = {
            UK: iter(given),
            US: [_at(180, PENCE), _at(185)],
            LINES[0]: Refused("FileNotFoundError: x"),
        }
        nothing = "old desk: Stooq matrices gave nothing: FileNotFoundError: x"
        assert headstart.adopt(store, Source.MATRICES, answers, daily) == {
            UK: Adopted(filled, 2, 1, faults),
            US: Adopted(0, 0, 0, (faults[1], unproven)),  # dollars are never read as cents
            LINES[0]: Adopted(0, 0, 0, (nothing,)),
        }
    held = (fresh[0], _at(5), fresh[1])
    assert bars.five(store, UK, bars.EPOCH, NOON + timedelta(1)) == held
    assert bars.sources(store, UK, bars.FIVE) == {Source.ARCHIVE: 2, Source.MATRICES: 1}
    astray = [_at(n, "10 11 9 10.5") for n in (0, 5, 20, 25)]
    wrong = "3 of the 3 bars already held for the same moments differ: another clock or another"
    assert headstart.adopt(store, Source.DATABASE, {UK: astray}, {}) == {
        UK: Adopted(0, 0, 0, ("4 bars on a day with no fresh daily bar to vouch for them",))
    }
    assert headstart.adopt(store, Source.DATABASE, {UK: astray}, {UK: [DAY]}) == {
        UK: Adopted(0, 3, 3, (f"{wrong} instrument; none kept",))
    }
    assert bars.five(store, UK, bars.EPOCH, NOON + timedelta(1)) == held
    late = _at(5, "10 11 9 9.9")
    gave = "1 bars held from another source differ, and gave way"
    assert bars.keep(store, {UK: [late]}) == {UK: (gave,)}
    assert bars.five(store, UK, bars.EPOCH, NOON + timedelta(1)) == (fresh[0], late, fresh[1])
    assert bars.sources(store, UK, bars.FIVE) == {Source.ARCHIVE: 3}


def test_every_store_the_register_tags_import_is_adopted_once_and_counted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    line, store, old = LINES[2], tmp_path / "market.db", tmp_path / "old.db"
    with bars.writing(store) as round_:
        round_.five(line, [_at(0)])
    asked: list[date] = []

    def fetch(_line: Line, day: date) -> tuple[Bar, ...]:
        asked.append(day)
        return (DAY,)

    monkeypatch.setattr(archive, "fetch", fetch)
    monkeypatch.setattr(archive, "fetch_five", lambda _line, _now: (_at(0),))
    walls = [NOON + timedelta(minutes=minutes) for minutes in (60, 70)]
    for folder in "matrix", "parquet":
        (tmp_path / folder).mkdir()
    _matrix(tmp_path / "matrix", f"{line.symbol}.UK", walls, [[1000, 1100, 900, 1000, 5]] * 2)
    rows = [(f"{line.symbol}.L", "5m", _at(n).start.isoformat(), 10, 11, 9, 10, 5) for n in (5, 10)]
    _database(old, rows)
    register = tmp_path / "register.md"
    named = [("IMPORT", old), ("IMPORT", tmp_path / "matrix"), ("IMPORT", tmp_path / "parquet")]
    tagged = "\n".join(f"| {tag} | `{where}` | 1 GB | |" for tag, where in named)
    register.write_text(f"| tag | folder |\n{tagged}\n| CROSS-CHECK | `{tmp_path}` | |\n")
    day = NOON.date() + timedelta(1)
    counts = "1 with no reader yet (parquet); bars filled 2, met 2, differ 0"
    assert (
        headstart.main(register, store, day)
        == f"headstart: 2 old stores read, 0 already in, {counts}"
    )
    assert bars.five(store, line, NOON, NOON + timedelta(1)) == (_at(0), _at(5), _at(10))
    assert bars.sources(store, line, bars.FIVE) == dict.fromkeys(
        (Source.ARCHIVE, Source.MATRICES, Source.DATABASE), 1
    )
    said = capsys.readouterr().out.splitlines()
    for source in Source.MATRICES, Source.DATABASE:  # the matrices, named second, read first
        assert f"{source.value}: {line.symbol}: filled 1, met 1, differ 0; " in said
    assert len(said) == 2 * len(LINES) + 1 and len(asked) == len(LINES)
    again = "headstart: 0 old stores read, 2 already in, 1 with no reader yet (parquet); bars"
    assert headstart.main(register, store, day) == f"{again} filled 0, met 0, differ 0"
    assert len(asked) == len(LINES)  # nothing left to read in asks the archive for nothing
    sound = register.read_text()
    for row, why in ("", "by its path"), (f"`{old}`", "a second store"), ("`x`", "not there"):
        register.write_text(f"{sound}| IMPORT | {row} |\n")
        with pytest.raises((ValueError, FileNotFoundError), match=why):
            headstart.main(register, store, day)


def _history(tmp_path: Path, closes: list[float]) -> tuple[Path, Path]:
    """The old stores of BA: pence matrices from 2 June to 13 November 2025, and a database
    giving the closes of the last days as pounds, later days first."""
    days = venues.sessions("LSE", date(2025, 6, 2), date(2025, 11, 13))
    stamps = [
        (datetime(d.year, d.month, d.day, tzinfo=UTC) - bars.EPOCH) // timedelta(milliseconds=1)
        for d in days
    ]
    rows = [[5000 + n % 3, 5200, 4900, 5100, 900] for n in range(len(days))]
    np.save(tmp_path / "BA.UK_1d_ts.npy", np.array(stamps, dtype=np.int64))
    np.save(tmp_path / "BA.UK_1d_ohlcv.npy", np.array(rows, dtype=np.float64).T)
    old = tmp_path / "old.db"
    _database(
        old,
        [
            ("BA.L", "1d", f"{d}T00:00:00+00:00", 50, 52, 49, c, 9)
            for d, c in zip(days[::-1], closes, strict=False)
        ],
    )
    return tmp_path, old


def test_a_daily_history_joins_the_archives_day_with_its_gap_bridged_by_five_minute_bars(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    mon = Bar(date(2025, 11, 17), Decimal(51), Decimal(52), Decimal(50), Decimal(51), 70)
    friday = datetime(2025, 11, 14, 10, tzinfo=UTC)
    fives = [
        _five(friday, "51 52 50 51", 3),
        _five(friday + timedelta(minutes=5), "51 53 51 52", 4),
    ]
    monkeypatch.setattr(archive, "fetch", lambda *_: (mon,))
    monkeypatch.setattr(archive, "fetch_five", lambda *_: tuple(fives))
    stores = _history(tmp_path, [51.0, 51.0, 49.0])
    said = headstart.daily(UK, tmp_path / "data", stores, date(2025, 11, 18))
    assert "agree on 2 of 3 days" in said
    kept = store.read(tmp_path / "data" / "daily" / "LSE", "BA")
    assert (kept[0].day, kept[-3:-1], kept[-1]) == (date(2025, 6, 2), kept[-3:-1], mon)
    assert kept[-2] == Bar(
        date(2025, 11, 14), Decimal(51), Decimal(53), Decimal(50), Decimal(52), 7
    )
    (tmp_path / "two").mkdir()
    stores = _history(tmp_path / "two", [49.0, 49.0, 51.0])
    with pytest.raises(ValueError, match="2 of the 3 bars already held"):
        headstart.daily(UK, tmp_path / "other", stores, date(2025, 11, 18))
    assert not (tmp_path / "other").exists()
