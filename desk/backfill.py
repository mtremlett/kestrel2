"""backfill - A MISSING DAILY BAR, FILLED FOR ANY NAMED LINE AND DAY (R-RUNNER-224, 16 November
2026). The broker's bar first (source IBKR), the archive's (Yahoo) only for what the broker does
not give (source BACKFILL), each judged by the one store beside the bars the long database holds
and written through its one writer, only on a day it holds none. A second run writes nothing; a
day neither source gives is named, never filled. The quality monitor calls `fill` for every hole.
`python -m desk.backfill SYMBOL DAY...` asks the paper gateway (client 225) and the archive."""

from __future__ import annotations

import os
import sys
from collections.abc import Callable, Iterable, Sequence
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from desk import archive, bars, history, keeper, paper, store, venues
from desk.bars import Source
from desk.lines import LINES, POUND, Line
from desk.store import Bar, Refused

in_currency = history.in_currency  #: the one unit rule lives in desk/history.py
Ask = Callable[[Line, date], store.Answer]  #: a source's answer for one line's one day
Asks = Sequence[tuple[Source, Ask]]  #: the sources in the order they are tried


def _held(path: Path, line: Line) -> tuple[Bar, ...]:
    try:
        return bars.daily(path, line)
    except (LookupError, FileNotFoundError):  # a line never written holds nothing
        return ()


def _accepted(path: Path, line: Line, day: date, answer: store.Answer, today: date) -> Bar | str:
    """The day's bar if the one store lets it in beside the bars held on both sides of it, judged
    as of today (the keeper's clock), else why not."""
    if isinstance(answer, Refused):
        return answer.reason
    given = [bar for bar in answer if bar.day == day]
    if not given:
        return "it gave no bar for the day"
    rates = keeper.pound_closes(path)
    kept, faults, _ = store.judge(line, [*_held(path, line), *given], today, rates)
    return next((bar for bar in kept if bar.day == day), "; ".join(f.what for f in faults))


def ordered(broker: Ask, archived: Ask, local: Ask | None = None) -> Asks:
    """The sources in their order: the broker, local Stooq (when a folder is given), the archive."""
    near = ((Source.STOOQ_DAILY, local),) if local else ()
    return ((Source.IBKR, broker), *near, (Source.BACKFILL, archived))


def fill(
    path: Path, wanted: Iterable[tuple[Line, date]], asks: Asks, today: date
) -> tuple[list[str], list[str]]:
    """Each wanted day the database at path holds no bar for, filled from the first of the
    ordered (source, ask) pairs the one store accepts; the lines saying what was written, and
    what no source gave (with why)."""
    wrote, named = [], []
    for line, day in wanted:
        if any(bar.day == day for bar in _held(path, line)):
            continue
        why = []
        for source, ask in asks:
            got = _accepted(path, line, day, ask(line, day), today)
            if isinstance(got, Bar):
                with bars.writing(path, source) as opened:
                    opened.days(line, [got])
                wrote.append(f"{line.symbol} {day}: {source.value}")
                break
            why.append(f"{source.value}: {got}")
        else:
            named.append(f"{line.symbol} {day}: no source gives it ({'; '.join(why)})")
    return wrote, named


def fill_pound(path: Path, table: str, today: date) -> tuple[list[str], list[str]]:
    """The pound's sessions (from its first bar to before today) the database holds no rate for,
    filled from FRED's noon table (`date,dollars` a line, a blank where the Fed gave none) under
    Source.FED_NOON; the days written, and the days the Fed gave none, named, never invented."""
    held = {bar.day for bar in _held(path, POUND)}
    if not held:
        return [], []
    rows = (row.split(",") for row in table.splitlines()[1:])
    given = {date.fromisoformat(day): Decimal(rate) for day, rate in rows if rate}
    lost = [
        d for d in venues.sessions(POUND.venue, min(held), today - timedelta(1)) if d not in held
    ]
    found = [Bar(d, given[d], given[d], given[d], given[d], 0) for d in lost if d in given]
    if found:
        with bars.writing(path, Source.FED_NOON) as opened:
            opened.days(POUND, found)
    return [f"{b.day}: {b.close}" for b in found], [str(d) for d in lost if d not in given]


def _broker(home: Path, now: datetime) -> Ask:
    """The broker's bar of one day, in the line's currency: its own dial, in the history
    reader's pace and quiet, and the unit it prices the line in, as it lists the line today."""

    door = paper.Door(history.CLIENT)  #: the history reader's own door, passed down

    def ask(line: Line, day: date) -> store.Answer:
        got = history.gather((line,), day + timedelta(1), day, now)
        return history.priced(home, now, got, door)[line]

    return ask


def _archive(line: Line, day: date) -> store.Answer:
    return archive.gather(
        [line], day, lambda one, at: archive.fetch(one, at + timedelta(1), since=at)
    )[line]


def main(home: Path, now: datetime, wanted: Iterable[str]) -> int:
    """THE COMMAND: `SYMBOL DAY...` filled; what was written, then what no source gave (exit 1)."""
    lines = {line.symbol: line for line in LINES}
    names = list(wanted)
    if len(names) % 2:
        raise ValueError(f"SYMBOL DAY pairs are asked for, not {names}")
    pairs = zip(names[::2], names[1::2], strict=True)
    asked = [(lines[symbol], date.fromisoformat(day)) for symbol, day in pairs]
    wrote, named = fill(home / keeper.HOT, asked, ordered(_broker(home, now), _archive), now.date())
    sys.stdout.write("".join(f"{line}\n" for line in wrote))
    sys.stderr.write("".join(f"NOT FILLED: {line}\n" for line in named))
    return int(bool(named))


if __name__ == "__main__":
    sys.exit(main(Path(os.environ["KESTREL2_DATA"]), datetime.now(UTC), sys.argv[1:]))
