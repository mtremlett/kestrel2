"""history_write - THE BROKER'S PULLED BARS LET INTO THE DATABASE: what desk.history.pull gives
for one line in one timeframe is written, under the source IBKR, through the one writer
(desk.bars) in a round of its own, so a pull stopped anywhere has kept every answer it was
given. A refused line adds nothing. A bar off its timeframe's marks is refused loudly (the
bars are not yet re-aligned to the venue's session: left to a later step)."""

from __future__ import annotations

import os
import sys
from collections.abc import Callable, Iterable, Mapping, Sequence
from datetime import UTC, datetime, time
from pathlib import Path

from desk import bars, history, listing, paper
from desk.history import Ask, Got
from desk.lines import LINES, Line
from desk.rollup import Candle
from desk.spans import Five, Timed
from desk.store import Bar

Keep = Callable[[Line, str, Got], int]
LIMIT = 50  #: asks in one run: at the pacing, inside the broker's 60 in ten minutes


def _timed(frame: str, one: Bar | Candle) -> Timed:
    """A pulled bar as the store's bar of the timeframe: a day's bar starts at its midnight UTC."""
    if isinstance(one, Bar):
        start = datetime.combine(one.day, time(), UTC)
        return Timed(frame, start, one.open, one.high, one.low, one.close, one.volume)
    return Timed(frame, one.start, one.open, one.high, one.low, one.close, one.volume)


def keeper(path: Path, units: Mapping[str, int]) -> Keep:
    """The `keep` a pull takes: each answer written to the store at path as it comes, its prices
    turned into the line's currency by the unit the broker lists the line in (units, by symbol;
    history.scaled), saying how many bars landed (none for a refusal). A line with no unit
    is a KeyError: its prices are not guessed."""

    def keep(line: Line, frame: str, got: Got) -> int:
        if not isinstance(got, tuple):
            return 0
        got = tuple(history.scaled(b, units[line.symbol]) for b in got)
        with bars.writing(path, bars.Source.IBKR) as round_:
            if frame == "1d":
                return round_.days(line, (b for b in got if isinstance(b, Bar)))
            if frame == "5m":
                return round_.five(
                    line,
                    (
                        Five(c.start, c.open, c.high, c.low, c.close, c.volume)
                        for c in got
                        if isinstance(c, Candle)
                    ),
                )
            return round_.timed(line, frame, (_timed(frame, b) for b in got))

    return keep


def held(path: Path, lines: Iterable[Line]) -> set[Ask]:
    """The asks the database already holds bars of from the broker: what a pull has done."""
    done: set[Ask] = set()
    for line in lines:
        for frame in history.SIZES:
            try:
                have = bars.sources(path, line, bars.DAILY if frame == "1d" else frame)
            except (FileNotFoundError, LookupError):  # nothing written yet for it: not done
                continue
            if have.get(bars.Source.IBKR):
                done.add((line, frame))
    return done


def main(home: Path, now: datetime, wanted: Sequence[str]) -> int:
    """THE COMMAND: `[ASKS]` (LIMIT unless said) of the asks not yet held are made of the broker
    and written; says how many were made. Not in a desk round (exit 1, nothing sent)."""
    path, limit = home / bars.LIVE, int(wanted[0]) if wanted else LIMIT
    try:
        if not history.quiet(now):  # the gateway is not dialled, even for the units, in a round
            raise history.Busy("a desk round runs: history is not asked now")
        listed = listing.kept(home, now, LINES, paper.Door(history.CLIENT))
        units = {s: one.magnifier for s, one in listed.items() if isinstance(one, listing.Listing)}
        lines = [line for line in LINES if line.symbol in units]  # else its unit is unknown
        asks = history.plan(lines, held(path, lines))
        made = history.run(asks, keeper(path, units), now.date(), now, limit=limit)
    except history.Busy as busy:
        sys.stderr.write(f"{busy}\n")
        return 1
    sys.stdout.write(f"{made} asks made, {len(asks) - made} to go\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(os.environ["KESTREL2_DATA"]), datetime.now(UTC), sys.argv[1:]))
