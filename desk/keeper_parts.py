"""keeper_parts - the keeper's lower part: which lines are late in their five-minute round now,
parked for it, and how long since each line's newest ended bar. desk.keeper gives them out."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta
from pathlib import Path

from desk import bars, live, venues
from desk.bars import Five
from desk.lines import Line

LATE = timedelta(minutes=15)  #: a line's five-minute bars are late, and it is parked, after this


def _ended(hot: Path, line: Line, now: datetime) -> list[Five] | None:
    """A line's ended bars of the last LATE; none until its venue has been open for LATE."""
    session = venues.open_at(line.venue, now)
    if session is None or now - session.open < LATE:
        return None
    try:
        held = bars.five(hot, line, now - LATE, now)
    except LookupError:  # the store never held a bar of the line: it is missing
        return []
    return [bar for bar in held if bar.start + live.BAR <= now]


def parked_live(hot: Path, lines: Sequence[Line], now: datetime) -> dict[str, str]:
    """EACH LINE NOT TO BE TRADED NOW, and why: in session for LATE with no ended bar in the last
    LATE, or whose bars there are out of line."""
    parked = {}
    for line in lines:
        ended = _ended(hot, line, now)
        if ended is not None and (
            faults := bars.checked(line, ended)[1] if ended else ["no ended bar"]
        ):
            parked[line.symbol] = f"{faults[0]} in the last {LATE.seconds // 60} minutes"
    return parked


def delays(hot: Path, lines: Sequence[Line], now: datetime) -> dict[str, int]:
    """THE SOURCE'S DELAY: minutes since each line's newest ended bar ended; parked lines absent."""
    found = {line.symbol: _ended(hot, line, now) for line in lines}
    return {s: (now - (e[-1].start + live.BAR)).seconds // 60 for s, e in found.items() if e}
