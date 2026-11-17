"""history_write - THE BROKER'S PULLED BARS LET INTO THE DATABASE: what desk.history.pull gives
for one line in one timeframe is written, under the source IBKR, through the one writer
(desk.bars) in a round of its own, so a pull stopped anywhere has kept every answer it was
given. A refused line adds nothing. A bar off its timeframe's marks is refused loudly (the
bars are not yet re-aligned to the venue's session: left to a later step)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, time
from pathlib import Path

from desk import bars
from desk.history import Got
from desk.lines import Line
from desk.rollup import Candle
from desk.spans import Five, Timed
from desk.store import Bar

Keep = Callable[[Line, str, Got], int]


def _timed(frame: str, one: Bar | Candle) -> Timed:
    """A pulled bar as the store's bar of the timeframe: a day's bar starts at its midnight UTC."""
    if isinstance(one, Bar):
        start = datetime.combine(one.day, time(), UTC)
        return Timed(frame, start, one.open, one.high, one.low, one.close, one.volume)
    return Timed(frame, one.start, one.open, one.high, one.low, one.close, one.volume)


def keeper(path: Path) -> Keep:
    """The `keep` a pull takes: each answer written to the store at path as it comes, saying how
    many bars landed (none for a refusal)."""

    def keep(line: Line, frame: str, got: Got) -> int:
        if not isinstance(got, tuple):
            return 0
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
