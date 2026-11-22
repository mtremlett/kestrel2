"""universe_parts - how research reads the list's bars, split from lab/universe.py: its rule for
the large moves nobody has confirmed (the store parks a ticker for one and that is not loosened;
the desk cannot import this module, so the rule can decide no trade), the longest run on one
scale of price, and the second source of London's daily bars."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from statistics import median

import numpy as np

from desk import bars as database
from desk import store
from desk.lines import Line
from desk.store import Bar

#: Research's rule for a move the store parks for (docs/DECISIONS.md, the data lane's). Read
#: on the list's 406 such moves of 13 November 2026: a fall made wholly between two sessions
#: on under this many times the usual value traded looks each time like a change of scale (a
#: split the archive did not adjust, a demerger, a special payment: fifteen, the heaviest on
#: 2.3 times, none confirmed from a second source); the lightest real fall came on 2.8. Two
#: that look like changes of scale, on 2.5 and 4.4 times, are read as losses. The usual is
#: the median of the USUAL sessions before. The number was chosen looking at that one list.
HEAVY, USUAL = Decimal("2.5"), 20


@dataclass(frozen=True)
class History:
    """A ticker's bars as research reads them: its longest run on one scale of price. It
    stops short of the store's last day when a day of `rescaled` is later than its last bar:
    it is then no guide to today. Which run is longest can change as sessions gather."""

    bars: tuple[Bar, ...]  #: oldest first, none either side of a change of scale
    #: The days among them of an unconfirmed move, read as the market's. One made within a
    #: day is named on that day and on the next, whose bar sits far from where the day began.
    moves: tuple[date, ...]
    rescaled: tuple[date, ...]  #: every change of scale in what the store keeps for it


def _rescaled(before: Sequence[Bar], bar: Bar) -> bool:
    """An unconfirmed move is a change of the price's scale, not a move a holder lived
    through, when it was made wholly between two sessions and it is a rise, or a fall on
    ordinary trading. A rise is never believed unconfirmed: the desk only buys, so counting
    a false windfall flatters a study and disbelieving a real one cannot. A fall is
    disbelieved only on trading under HEAVY times a usual that is known: forgetting a real
    loss flatters every strategy, so a fall with no usual volume to judge it by is believed.
    The price of disbelief is the bars on the shorter side of the move, which go unread."""
    last = before[-1].close
    usual = median(b.close * b.volume for b in before[-USUAL:])
    quiet = bar.close * bar.volume < HEAVY * usual
    return bar.low > last * store.JUMP or (bar.high * store.JUMP < last and quiet)


def read(path: Path, line: Line) -> History:
    """A ticker's bars from the history database beside the live file at path, the one door
    for prices: a bar held only in a CSV file is never read. Else as `_history`. A line the
    database holds no bar for raises LookupError naming it."""
    held = database.daily(path, line)
    if not held:
        raise LookupError(f"{line.symbol} on {line.venue}: the history database holds no bar")
    return _history(held, line)


def _history(bars: tuple[Bar, ...], line: Line) -> History:
    """The longest run of bars on one scale. No trade is priced
    across a change of scale: the bars are the longest run between two (the later of two as
    long), and the unconfirmed moves inside it are named, so that a verdict can say how many
    it was held through."""
    at = {bar.day: n for n, bar in enumerate(bars)}
    moved = [at[day] for day in store.moves(line, bars)]
    cuts = [n for n in moved if _rescaled(bars[:n], bars[n])]
    edges = [0, *cuts, len(bars)]
    start, end = max(zip(edges, edges[1:], strict=False), key=lambda run: (run[1] - run[0], run))
    listed = tuple(bars[n].day for n in moved if start < n < end)
    return History(bars[start:end], listed, tuple(bars[n].day for n in cuts))


def matrix(folder: Path) -> Callable[[Line, date], tuple[Bar, ...]]:
    """The second source: the old desk's Stooq daily matrices in folder, read only. It knows
    London lines only, in pence; a line it holds no file for has no bars from it."""

    def second(line: Line, day: date) -> tuple[Bar, ...]:
        stem = folder / f"{line.symbol}.UK_1d"
        if line.venue != "LSE" or not stem.with_name(stem.name + "_ts.npy").is_file():
            return ()
        rows = np.load(stem.with_name(stem.name + "_ohlcv.npy"))
        stamps = np.load(stem.with_name(stem.name + "_ts.npy"))
        bars = []
        for n, stamp in enumerate(stamps):
            when = datetime.fromtimestamp(int(stamp) / 1000, UTC).date()
            o, h, lo, c = (Decimal(str(round(float(rows[k, n]), 3))) / 100 for k in range(4))
            if when < day:
                bars.append(Bar(when, o, h, lo, c, int(rows[4, n])))
        return tuple(bars)

    return second


def breadth(path: Path, lines: Sequence[Line]) -> dict[date, tuple[int, int]]:
    """Each session's advances and declines among the lines (R-RUNNER-346): a line advances
    when its close is above its previous bar's, declines when below, and is left out when
    unchanged or first. Read through `read`, the history database at path, so no change of
    scale counts as a move; a line it holds no bar for is left out. Counts only: a day's ratio
    is the caller's."""
    tally: dict[date, list[int]] = {}
    for line in lines:
        try:
            held = read(path, line).bars
        except LookupError:
            continue
        for before, bar in zip(held, held[1:], strict=False):
            if bar.close != before.close:
                tally.setdefault(bar.day, [0, 0])[bar.close < before.close] += 1
    return {day: (up, down) for day, (up, down) in sorted(tally.items())}
