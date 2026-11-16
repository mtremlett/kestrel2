"""The old desk's stores as a head start: its five-minute bars are read, never written, and
enter the fast store only where a fresh daily bar vouches for them and the store's own checks
pass; a fresh bar wins, and each bar that differs from one held is counted."""

from __future__ import annotations

import sqlite3
import zipfile
from collections.abc import Iterable, Mapping
from contextlib import closing
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import numpy as np
import pyarrow as pa  # type: ignore[import-untyped]  # ships no stubs
import pyarrow.parquet as pq  # type: ignore[import-untyped]  # ships no stubs
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
        UK: Adopted(0, 3, 3, (f"{wrong} instrument (on 2026-11-13); none kept",))
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


def _parquet(folder: Path, line: Line, walls: list[datetime], fetched: bool = False) -> None:
    """A parquet store of the old desk's form: a line's bars of 10 11 9 10 and 5 shares at the
    walls, and a last one with a hole in its open; ibkr_store alone keeps a fetch record."""
    made = folder / f"freq=5/market=uk/ticker={line.symbol}.UK"
    made.mkdir(parents=True)
    walls = [*walls, walls[-1] + timedelta(minutes=5)]
    rows = len(walls)
    table = pa.table(
        {
            "ts": [wall.replace(tzinfo=None) for wall in walls],
            "open": [10.0] * (rows - 1) + [None],
            "high": [11.0] * rows,
            "low": [9.0] * rows,
            "close": [10.0] * rows,
            "volume": [5.0] * rows,
        }
    )
    pq.write_table(table, made / "part.parquet")
    if fetched:
        (made / "fetch.json").write_text("{}")


def _stooq(trend: Path, raw: Path, line: Line, walls: list[datetime]) -> None:
    """mark_the_trend's Stooq file and a raw Stooq zip of a line's bars of 10 11 9 10 and 5."""
    trend.mkdir()
    cells = {
        name: [x] * len(walls)
        for name, x in zip(headstart.TREND[1:], (10.0, 11.0, 9.0, 10.0, 5.0), strict=True)
    }
    pq.write_table(pa.table({"DATE": walls} | cells), trend / f"{line.symbol}.L.5.parquet")
    later = [walls[0], walls[1] + timedelta(minutes=5)]  # the zip's second moment is its own
    rows = [f"{line.symbol}.UK,5,{w:%Y%m%d},{w:%H%M%S},10,11,9,10,5,0" for w in later]
    (raw / "2026-10-24").mkdir(parents=True)
    with zipfile.ZipFile(raw / "2026-10-24/5_uk_txt__24oct26.zip", "w") as made:
        made.writestr(
            f"data/5 min/uk/lse etfs/{line.symbol.lower()}.uk.txt", "\n".join(["<T>", *rows])
        )


def test_the_parquet_and_stooq_stores_are_read_on_their_own_clocks_and_adopted_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    line, store, ibkr, stooq = LINES[2], tmp_path / "market.db", tmp_path / "i", tmp_path / "s"
    trend, raw = tmp_path / "t", tmp_path / "r"
    with bars.writing(store) as round_:
        round_.five(line, [_at(0)])
    monkeypatch.setattr(archive, "fetch", lambda _line, _day: (DAY,))
    monkeypatch.setattr(archive, "fetch_five", lambda _line, _now: (_at(0),))
    hour = timedelta(hours=1)  # Stooq's clock in winter
    _parquet(ibkr, line, [_at(0).start, _at(5).start], fetched=True)
    _parquet(stooq, line, [_at(0).start + hour, _at(10).start + hour])
    _stooq(trend, raw, line, [_at(0).start + hour, _at(15).start + hour])
    wheres = (ibkr, stooq, trend, raw)
    sources = [headstart.reader(where) for where in wheres]
    made = [Source.IBKR_STORE, Source.STOOQ_STORE, Source.TREND_STOOQ, Source.STOOQ_RAW]
    assert [how[0] for how in sources if how] == made
    with pytest.raises(ValueError, match="no zip of us"):
        headstart.raw(US, raw)
    register = tmp_path / "register.md"
    register.write_text("".join(f"| IMPORT | `{where}` | 1 GB | |\n" for where in wheres))
    day = NOON.date() + timedelta(1)
    read = "4 old stores read, 0 already in, 0 with no reader yet (none)"
    assert headstart.main(register, store, day) == (
        f"headstart: {read}; bars filled 4, met 4, differ 0"
    )
    assert bars.five(store, line, NOON, NOON + timedelta(1)) == tuple(map(_at, (0, 5, 10, 15, 20)))
    assert bars.sources(store, line, bars.FIVE) == dict.fromkeys((Source.ARCHIVE, *made), 1)
    again = "headstart: 0 old stores read, 4 already in, 0 with no reader yet (none)"
    assert headstart.main(register, store, day) == f"{again}; bars filled 0, met 0, differ 0"


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


def test_an_old_store_in_adjusted_prices_never_writes_over_the_raw_and_a_real_difference_is_refused(
    tmp_path: Path,
) -> None:
    store, then = tmp_path / "bars.db", NOON - timedelta(1)

    def raw(start: datetime) -> Five:  # as traded: 10 11 9 10
        return _five(start)

    def adjusted(start: datetime) -> Five:  # a dividend's 1%
        return _five(start, "9.9 10.89 8.91 9.9")

    with bars.writing(store) as round_:
        round_.five(UK, [raw(then), raw(NOON), raw(NOON + timedelta(minutes=5))])
    old = [adjusted(then), adjusted(then + timedelta(minutes=5)), raw(NOON)]
    old += [_at(5, "10 11 9 10.5"), raw(NOON + timedelta(minutes=10))]
    days = {UK: [DAY, replace(DAY, day=then.date())]}
    said = "2 bars on days that are the adjusted form of the store's as-traded bars: not taken"
    got = headstart.adopt(store, Source.MATRICES, {UK: old}, days)
    assert got == {UK: Adopted(1, 3, 1, (said,))}  # the 12:10 raw bar alone fills
    expected = (raw(then), raw(NOON), _at(5), _at(10))  # nothing of the raw is written over
    assert bars.five(store, UK, bars.EPOCH, NOON + timedelta(1)) == expected
    with bars.writing(store, Source.MATRICES) as round_:
        seen = round_.compare(UK, [adjusted(then)])
    assert dict(seen.factors) == {then.date(): Decimal("0.99")}
    assert [p * Decimal("0.99") for p in (raw(then).open, raw(then).low)] == [
        adjusted(then).open,
        adjusted(then).low,
    ]  # read adjusted, the raw is the old series
    other = [_five(then, "10 11 9 10.5"), _at(0, "10 11 9 10.5")]
    refused = headstart.adopt(store, Source.DATABASE, {UK: other}, days)[UK]
    assert refused.filled == 0
    assert "2 of the 2 bars already held for the same moments differ" in refused.faults[-1]
    assert "(on 2026-11-12, 2026-11-13)" in refused.faults[-1]
