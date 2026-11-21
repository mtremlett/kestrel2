"""history_write - THE BROKER'S PULLED BARS LET INTO THE DATABASE: what desk.history.pull gives
for one line in one timeframe is written, under the source IBKR, through the one writer
(desk.bars) in a round of its own, so a pull stopped anywhere has kept every answer it was
given. A refused line adds nothing. A bar off its timeframe's marks is refused loudly (the
bars are not yet re-aligned to the venue's session: left to a later step)."""

from __future__ import annotations

import os
import sys
from collections.abc import Callable, Iterable, Mapping, Sequence
from datetime import UTC, datetime, time, timedelta
from pathlib import Path

from desk import bars, history, listing, paper, rollup, venues
from desk.history import Ask, Got
from desk.lines import LINES, Line
from desk.rollup import Candle
from desk.spans import EPOCH, SPANS, Five, Timed
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


HOURLY = ("1h", "4h")  #: the timeframes built from held 30-minute bars, not asked of the broker
HALF = timedelta(minutes=30)
FROM_ONE = ("2m", "10m")  #: the timeframes built from held one-minute bars
FROM_FIVE = ("15m", "30m")  #: the timeframes built from held five-minute bars


def built(venue: str, candles: Iterable[Candle], frame: str) -> list[Candle]:
    """The venue's 30-minute candles as bars of frame (1h or 4h) on the store's UTC marks: a bar
    only where every half hour the session holds in its interval is there; none otherwise."""
    length = timedelta(seconds=SPANS[frame].seconds)
    groups: dict[datetime, list[Candle]] = {}
    for one in sorted(candles, key=lambda c: c.start):
        if venues.sessions(venue, one.start.date(), one.start.date()):
            groups.setdefault(EPOCH + (one.start - EPOCH) // length * length, []).append(one)
    made = []
    for start, group in groups.items():
        session = venues.hours(venue, start.date())
        due = [start + HALF * n for n in range(length // HALF)]
        if [c.start for c in group] == [t for t in due if session.open <= t < session.close]:
            made.append(Candle(start, group[0].open, max(c.high for c in group),
                min(c.low for c in group), group[-1].close, sum(c.volume for c in group),
                bars.Source.ROLLUP_30M.value))  # fmt: skip
    return made


def _held(path: Path, line: Line, span: str, now: datetime) -> list[Candle]:
    """The line's bars of one span as held (a day's at its midnight UTC), none if the store
    never held the span."""
    try:
        if span == "1d":
            return [Candle(datetime.combine(b.day, time(), UTC), b.open, b.high, b.low, b.close,
                           b.volume, "ibkr") for b in bars.daily(path, line)]  # fmt: skip
        got = bars.five(path, line, EPOCH, now) if span == "5m" else bars.timed(
            path, line, span, EPOCH, now)  # fmt: skip
    except LookupError:  # the store never held this span for the line: none to build from
        return []
    return [Candle(b.start, b.open, b.high, b.low, b.close, b.volume, "ibkr") for b in got]


def _made(path: Path, line: Line, now: datetime) -> dict[str, list[Candle]]:
    """The line's 2m, 10m, 15m, 30m, 1h, 4h and weekly bars as built from the finer bars held."""
    halves, fives, days, ones = (_held(path, line, s, now) for s in ("30m", "5m", "1d", "1m"))
    made = {f: built(line.venue, halves, f) for f in HOURLY}
    made |= {f: rollup.rollup(line.venue, ones, f, "1m") for f in FROM_ONE}
    made |= {f: rollup.rollup(line.venue, fives, f, "5m") for f in FROM_FIVE}
    return {**made, "1wk": rollup.weekly(line.venue, days)}


def roll(path: Path, line: Line, now: datetime) -> int:
    """Build the line's 1h, 4h and weekly bars from the 30-minute and daily bars the database
    holds and add them: a bar already held, pulled or not, stays. Says how many landed."""
    made = _made(path, line, now)
    landed = 0
    for source, frames in (
        (bars.Source.ROLLUP_1M, FROM_ONE),
        (bars.Source.ROLLUP_5M, FROM_FIVE),
        (bars.Source.ROLLUP_30M, HOURLY),
        (bars.Source.ROLLUP_1D, ("1wk",)),
    ):
        with bars.writing(path, source) as round_:
            landed += sum(round_.timed(line, f, (_timed(f, c) for c in made[f])) for f in frames)
    return landed


def clashes(path: Path, line: Line, now: datetime) -> list[str]:
    """A fault for each bar built that a bar already held for its moment does not match in
    open, high, low or close (a pulled bar stays; the disagreement is recorded)."""
    faults = []
    for frame, candles in _made(path, line, now).items():
        have = {b.start: b for b in bars.timed(path, line, frame, EPOCH, now)}
        for c in candles:
            one = have.get(c.start)
            if one and (one.open, one.high, one.low, one.close) != (c.open, c.high, c.low, c.close):
                faults.append(
                    f"{line.symbol} {frame} {c.start:%Y-%m-%d %H:%M}: rolled and held differ"
                )
    return faults


def held(path: Path, lines: Iterable[Line]) -> set[Ask]:
    """The asks the database already holds bars of from the broker: what a pull has done."""
    done: set[Ask] = set()
    for line in lines:
        for frame in history.PULLED:
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
        faults = [f for line in lines for f in clashes(path, line, now)]
        rolled = sum(roll(path, line, now) for line in lines)
    except history.Busy as busy:
        sys.stderr.write(f"{busy}\n")
        return 1
    sys.stderr.writelines(f"FAULT {f}\n" for f in faults)
    sys.stdout.write(f"{made} asks made, {len(asks) - made} to go, {rolled} rolled\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(os.environ["KESTREL2_DATA"]), datetime.now(UTC), sys.argv[1:]))
