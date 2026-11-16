"""THE LIVE KEEPER, `--live` (R-RUNNER-12): the runner calls it every minute of a weekday. One
round takes the last two hours of 1-minute bars of every line whose venue is open, the twenty
and a watchlist (`watchlist.txt`, one `VENUE SYMBOL` a line), cut to his hundred market-data
lines, into `market_live.db`. It ends 1 on a refused line, or one whose newest bar is more
than STALE old in its venue's hours, naming it; its last line is `pacing N`, the refusals
for pacing. `--roll`, at 21:30, copies every live bar into `market_history.db`.
"""

from __future__ import annotations

import sqlite3
import sys
import time
from collections.abc import Callable, Mapping, Sequence
from contextlib import closing
from datetime import datetime, timedelta
from pathlib import Path

from desk import archive, bars, venues
from desk.bars import EPOCH
from desk.keeper import Ask, _within
from desk.lines import LINES, Line
from desk.store import Refused

LIVE, HISTORY, MINUTE = "market_live.db", "market_history.db", "1-minute"
WATCHLIST, HOLDS = "watchlist.txt", 100  #: in the data folder; his IBKR market-data lines
CURRENCY = {"LSE": "GBP", "US": "USD"}
BAR = timedelta(minutes=1)
STALE = timedelta(minutes=2)  #: a line in hours whose newest bar ended longer ago is a miss
BACK = timedelta(hours=2)  #: how far back a live round asks, so a missed round heals at the next
LIVE_SPENT = 50.0  #: seconds of one live round in which the archive is still asked
ROLL = (
    "INSERT OR REPLACE INTO main.bar (venue, symbol, span, at, open, high, low, close, volume,"
    " source) SELECT venue, symbol, span, at, open, high, low, close, volume, source FROM live.bar"
)


def watch(home: Path, lines: Sequence[Line] = LINES) -> list[Line]:
    """The watchlist beside the lines, cut so both fit his HOLDS market-data lines."""
    path = home / WATCHLIST
    rows = [row.split() for row in path.read_text("utf-8").splitlines() if row.strip()[:1] > "#"]
    mine = {(line.venue, line.symbol) for line in lines}
    extra = [Line(symbol, venue, CURRENCY[venue], 1) for venue, symbol in rows]
    return [line for line in extra if (line.venue, line.symbol) not in mine][: HOLDS - len(lines)]


def _minutes(line: Line, now: datetime) -> tuple[archive.Row, ...]:
    """A line's 1-minute bars of the last BACK, as far as they had ended by now (the archive
    closes its answer with the price of the moment, which is no bar)."""
    first, end = ((moment - EPOCH) // timedelta(seconds=1) for moment in (now - BACK, now))
    answer = archive._ask(archive._address(line, first, end, "1m"))  # noqa: SLF001
    meta, rows = archive._read(line, "1m", answer)  # noqa: SLF001
    ended = min(meta["regularMarketTime"], end - 59)
    return tuple(row for row in rows if row[0] < ended)


def _land(
    path: Path, answers: Mapping[Line, tuple[archive.Row, ...] | Refused]
) -> tuple[int, int, dict[Line, int]]:
    """The sound bars into the live store in one round: how many landed, how many were
    dropped as impossible, and each line's newest bar held (its start, seconds since EPOCH)."""
    rows, dropped = [], 0
    for line, got in answers.items():
        for at, *prices, volume in [] if isinstance(got, Refused) else got:
            o, h, lo, c = prices
            if 0 < lo <= min(o, c) <= max(o, c) <= h and volume >= 0:
                rows.append((line.venue, line.symbol, MINUTE, at, *map(str, prices), volume))
            else:
                dropped += 1
    keyed = [(*row, bars.Source.ARCHIVE.value) for row in rows]
    newest: dict[Line, int] = {}
    with closing(sqlite3.connect(path, timeout=bars.WAIT)) as held, held:
        held.execute("PRAGMA journal_mode = WAL")
        for table in bars.SCHEMA:
            held.execute(table)
        for line in answers:
            held.execute(bars.HOLD, (line.venue, line.symbol, MINUTE))
        held.executemany(bars.PUT, keyed)
        top = "SELECT max(at) FROM bar WHERE venue = ? AND symbol = ? AND span = ?"
        for line in answers:
            (last,) = held.execute(top, (line.venue, line.symbol, MINUTE)).fetchone()
            if last is not None:
                newest[line] = last
    return len(keyed), dropped, newest


def live(
    home: Path,
    now: datetime,
    lines: Sequence[Line] = LINES,
    ask: Ask[datetime, tuple[archive.Row, ...]] = _minutes,
    clock: Callable[[], float] = time.monotonic,
) -> tuple[list[str], list[str], int]:
    """ONE LIVE ROUND: what was done, the misses, and the refusals for pacing (HTTP 429)."""
    if now.utcoffset() != timedelta(0):
        raise ValueError(f"{now!r} is not a moment in UTC")
    open_ = [line for line in lines if venues.open_at(line.venue, now)]
    if not open_:
        return [], [], 0
    answers = archive.gather(open_, now, _within(ask, clock, clock() + LIVE_SPENT))
    refused = {line: a.reason for line, a in answers.items() if isinstance(a, Refused)}
    kept, dropped, newest = _land(home / LIVE, answers)
    missed = [f"{line.symbol} on {line.venue}: refused: {why}" for line, why in refused.items()]
    for line in open_:
        hours = venues.open_at(line.venue, now)
        if line in refused or hours is None or not hours.open + STALE <= now <= hours.close:
            continue
        age = now - EPOCH - timedelta(seconds=newest[line]) - BAR if line in newest else None
        if age is None or age > STALE:
            missed.append(f"{line.symbol} on {line.venue}: stale: newest bar ended {age} ago")
    words = (
        f"live round: {kept} bars kept for {len(open_) - len(refused)} of {len(open_)} lines, "
        f"{dropped} dropped as impossible, {len(refused)} refused"
    )
    return [words], missed, sum("429" in why for why in refused.values())


def roll(home: Path) -> int:
    """THE DAY ROLLED: every bar in the live store copied into the history store, one round,
    a bar already there replaced by the live one; how many were copied. The live store keeps
    its bars, so nothing is lost."""
    if not (home / LIVE).is_file():
        raise FileNotFoundError(f"{home / LIVE}: no live bars have been kept to roll")
    with closing(sqlite3.connect(home / HISTORY, timeout=bars.WAIT, isolation_level=None)) as db:
        db.execute("PRAGMA journal_mode = WAL")
        db.execute("ATTACH DATABASE ? AS live", ((home / LIVE).as_posix(),))
        db.execute("BEGIN IMMEDIATE")
        for table in bars.SCHEMA:
            db.execute(table)
        db.execute("INSERT OR IGNORE INTO main.held SELECT * FROM live.held")
        copied = db.execute(ROLL).rowcount
        db.execute("COMMIT")
    return copied


def command(
    home: Path,
    now: datetime,
    argv: Sequence[str],
    ask: Ask[datetime, tuple[archive.Row, ...]] | None,
) -> int:
    """`--live`: one live round, ending in `pacing N`; `--roll`: the day rolled."""
    if list(argv) == ["--roll"]:
        sys.stdout.write(f"rolled {roll(home)} bars into {HISTORY}\n")
        return 0
    if list(argv) != ["--live"]:
        raise SystemExit(f"usage: python -m desk.keeper [--live | --roll]; not {list(argv)}")
    lines = [*LINES, *watch(home)] if (home / WATCHLIST).is_file() else LINES
    done, missed, pacing = live(home, now, lines, ask or _minutes)
    sys.stdout.write("".join(f"{line}\n" for line in done) + f"pacing {pacing}\n")
    sys.stderr.write("".join(f"MISSED: {line}\n" for line in missed))
    return int(bool(missed))
