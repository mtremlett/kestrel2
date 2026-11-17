"""keeper_live - THE LIVE DAY'S PART OF THE KEEPER: a venue's five-minute round taken from IBKR's
paper gateway into the short database, and the archive's bars of the days before it, backfilled.
desk.keeper calls it in each venue's hours; the words it returns are the keeper's."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable, Sequence
from contextlib import closing
from datetime import datetime, timedelta
from pathlib import Path

from desk import archive, bars, live, venues
from desk.bars import Five
from desk.lines import YARDSTICK, Line
from desk.spans import Timed
from desk.store import Refused

RECENT = timedelta(days=7)  #: how far back a five-minute round asks: the week kept hot
Ask = Callable[[Line, datetime], tuple[Five, ...]]
MINUTES = "1m"  #: the span of the live keeper's bars
PER_RUN = (
    2  #: lines asked each minute: twenty lines, each once in ten minutes, inside IBKR's pacing
)
LATE = timedelta(minutes=2)  #: how stale a due line's newest bar may be
Minutes = Callable[[Line, datetime], tuple[Timed, ...]]


def recent(line: Line, now: datetime) -> tuple[Five, ...]:
    """The archive's five-minute bars of the last week, asked of it for the backfill."""
    return archive.fetch_five(line, now, RECENT)


def round_(
    hot: Path,
    mine: Sequence[Line],
    now: datetime,
    ask: Ask,
    back: Ask,
) -> tuple[str, bool]:
    """A venue's five-minute round into the fast store, in words, and whether it was a miss."""
    answers = archive.gather(sorted(mine, key=lambda line: line != YARDSTICK), now, ask)
    refused = sum(isinstance(answer, Refused) for answer in answers.values())
    faulted = sum(bool(f) for f in bars.keep(hot, answers, bars.Source.IBKR).values()) - refused
    old = archive.gather(mine, now, back)
    gaps = sum(isinstance(answer, Refused) for answer in old.values())
    past = {
        line: answer
        if isinstance(answer, Refused)
        else [b for b in answer if b.start.date() < now.date()]
        for line, answer in old.items()
    }
    bars.keep(hot, past, bars.Source.BACKFILL)
    ends = [b.start + live.BAR for a in answers.values() if not isinstance(a, Refused) for b in a]
    late = "no bar landed"
    if ends:
        late = f"newest bar landed {(now - max(ends)).seconds // 60} minutes after it ended"
    words = (
        f"{mine[0].venue}: five-minute round: {len(mine) - refused} of {len(mine)} lines "
        f"kept, {faulted} of them with faults listed, {refused} refused by the broker "
        f"({next((a.reason for a in answers.values() if isinstance(a, Refused)), 'none')}); "
        f"past days backfilled from the archive for {len(mine) - gaps} of {len(mine)} lines; "
        f"{late}"
    )
    return words, refused == len(mine)


def due(lines: Sequence[Line], now: datetime) -> tuple[Line, ...]:
    """The lines asked this minute: the next PER_RUN of the rota, which turns once a minute."""
    slot = int(now.timestamp()) // 60
    return tuple(lines[(slot * PER_RUN + k) % len(lines)] for k in range(PER_RUN))


def minute_round(
    hot: Path, lines: Sequence[Line], now: datetime, ask: Minutes
) -> tuple[str, list[str]]:
    """One run of `--live`: the due lines in session asked for their one-minute bars, kept as
    IBKR's; the words, and each line whose newest bar is later than LATE or was refused."""
    mine = [line for line in due(lines, now) if venues.open_at(line.venue, now)]
    answers = archive.gather(mine, now, ask)
    with bars.writing(hot, bars.Source.IBKR) as kept:
        for line, answer in answers.items():
            if not isinstance(answer, Refused):
                kept.timed(line, MINUTES, answer)
    stale = []
    for line, answer in answers.items():
        if isinstance(answer, Refused):
            stale.append(f"{line.symbol}: {answer.reason}")
        elif not answer or now - max(b.start for b in answer) - live.MINUTE > LATE:
            stale.append(f"{line.symbol}: no bar within {LATE.seconds // 60} minutes")
    paced = sum("pacing" in words.lower() for words in stale)
    return (
        f"live: one-minute bars asked for {len(mine)} lines, {len(stale)} stale, pacing {paced}",
        stale,
    )


ROLLED = "SELECT * FROM bar WHERE span IN (?, ?)"
HELD = "SELECT * FROM held WHERE span IN (?, ?)"


def roll(hot: Path) -> str:
    """One run of `--roll`: the short database's one-minute and five-minute bars copied, source
    kept and nothing changed, into the long one, which keeps every timeframe; in words."""
    spans = (MINUTES, bars.FIVE)
    if not hot.is_file():
        raise FileNotFoundError(f"{hot}: no live day to roll")
    with (
        closing(sqlite3.connect(hot)) as src,
        closing(sqlite3.connect(bars.files(hot)[bars.DAILY], timeout=bars.WAIT)) as dst,
    ):
        rows = src.execute(ROLLED, spans).fetchall()
        held = src.execute(HELD, spans).fetchall()
        with dst:
            for table in bars.SCHEMA:
                dst.execute(table)
            dst.executemany(bars.PUT, rows)
            dst.executemany(bars.HOLD, held)
    return f"roll: {len(rows)} one-minute and five-minute bars copied to the long database"
