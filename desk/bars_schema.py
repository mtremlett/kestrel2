"""bars_schema - what the fast store is made of, split from desk/bars.py: where a bar came from
(Source), the tables of its one SQLite file and the statements that write and find rows in them."""

from __future__ import annotations

from enum import Enum


class Source(Enum):
    """Where a bar came from: a bar from anywhere else cannot be written."""

    ARCHIVE = "archive"  #: the free price archive; until 14 November 2026 the one source
    IBKR = "IBKR paper"  #: the live session's only source: the paper gateway's own bars
    BACKFILL = "archive, backfilled"  #: the archive's bars of a past day, only where none is held
    MATRICES = "old desk: Stooq matrices"  #: the old desk's stores (lab/headstart.py)
    DATABASE = "old desk: mark_the_trend.db"
    STOOQ_RAW = "old desk: raw Stooq downloads"
    IBKR_STORE = "old desk: ibkr_store"
    STOOQ_STORE = "old desk: stooq_store"
    TREND_STOOQ = "old desk: mark_the_trend Stooq downloads"
    MTT_DB = "old desk: mark_the_trend.db daily rows"  #: its daily bars alone
    STOOQ_DAILY = "old desk: stooq_store daily rows"  #: its daily bars alone
    MATRIX_DAILY = "old desk: Stooq matrices daily rows"  #: its 1d arrays alone
    IBKR_DAILY = "old desk: ibkr_store daily rows"  #: its daily bars alone, the broker's own
    TREND_DAILY = "old desk: mark_the_trend Stooq daily files"  #: its daily files alone
    STOOQ_HOURLY = "old desk: stooq_store hourly rows"  #: its hourly bars alone
    FED_NOON = (
        "Federal Reserve noon buying rate, DEXUSUK via FRED"  #: the pound before the archive's
    )
    MATRIX_INTRADAY = "old desk: Stooq matrices 15m, 30m, 1h rows"  #: its arrays of those spans
    ROLLUP_30M = "rollup:30m"  #: 1h and 4h bars built here from held 30-minute bars
    ROLLUP_1D = "rollup:1d"  #: weekly bars built here from held daily bars

    @property
    def fresh(self) -> bool:
        """It is still asked, and so may restate a bar; an old store only fills."""
        return self in (Source.ARCHIVE, Source.IBKR)


#: Each bar under its line, its span and its start: a daily bar's day as its ordinal, a
#: five-minute bar's start as seconds since EPOCH. `held` names every line and span ever
#: written, so that a line never written is not read as a line with no bars.
SCHEMA = (
    "CREATE TABLE IF NOT EXISTS bar (venue TEXT NOT NULL, symbol TEXT NOT NULL,"
    " span TEXT NOT NULL, at INTEGER NOT NULL, open TEXT NOT NULL, high TEXT NOT NULL,"
    " low TEXT NOT NULL, close TEXT NOT NULL, volume INTEGER NOT NULL,"
    " source TEXT NOT NULL, PRIMARY KEY (venue, symbol, span, at)) WITHOUT ROWID",
    "CREATE TABLE IF NOT EXISTS held (venue TEXT NOT NULL, symbol TEXT NOT NULL,"
    " span TEXT NOT NULL, PRIMARY KEY (venue, symbol, span)) WITHOUT ROWID",
    "CREATE TABLE IF NOT EXISTS correction (venue TEXT NOT NULL, symbol TEXT NOT NULL,"
    " span TEXT NOT NULL, at INTEGER NOT NULL, open TEXT NOT NULL, high TEXT NOT NULL,"
    " low TEXT NOT NULL, close TEXT NOT NULL, volume INTEGER NOT NULL, source TEXT NOT NULL,"
    " replaced_by TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS withdrawn (venue TEXT NOT NULL, symbol TEXT NOT NULL, span TEXT"
    " NOT NULL, at INTEGER NOT NULL, PRIMARY KEY (venue, symbol, span, at)) WITHOUT ROWID",
)
#: A store made before sources were kept: every bar in it came from the archive.
SOURCED = f"ALTER TABLE bar ADD COLUMN source TEXT NOT NULL DEFAULT '{Source.ARCHIVE.value}'"
MADE = "SELECT 1 FROM sqlite_master WHERE name = 'held'"
HOLD = "INSERT OR IGNORE INTO held VALUES (?, ?, ?)"
HELD = "SELECT 1 FROM held WHERE venue = ? AND symbol = ? AND span = ?"
ADD = "INSERT INTO bar VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
PUT, FILL = (ADD.replace("INSERT", f"INSERT OR {then}") for then in ("REPLACE", "IGNORE"))
