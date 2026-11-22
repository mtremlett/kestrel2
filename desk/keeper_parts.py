"""keeper_parts - the keeper's lower parts: who gave a line's newest daily bar, the days a judge
withdrew, and the five-minute side's reading of a line's ended bars (parked, delayed). desk.keeper
gives them to its callers."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime, timedelta
from pathlib import Path

from desk import bars, live, store, venues
from desk.bars import Five
from desk.lines import Line
from desk.store import Bar, Refused

LATE = timedelta(minutes=15)  #: a line's five-minute bars are late, and it is parked, after this


def source(kept: Sequence[Bar], answer: store.Answer, broker: store.Answer | None) -> str:
    """Who gave a line's newest kept bar: the broker, else the archive (and why not the broker)."""
    gave = [{b.day for b in a} if isinstance(a, list | tuple) else None for a in (broker, answer)]
    day = kept[-1].day if kept else None
    if day in (gave[0] or ()):
        return "IBKR"
    why = "not asked" if gave[0] is None else "gave none"
    return f"archive (IBKR {why})" if day in (gave[1] or ()) else "the shelf, or none"


def dropped(kept: Sequence[Bar], *answers: store.Answer | None) -> set[date]:
    """The days the answers gave that the judge did not keep: withdrawn, never deleted."""
    given = {b.day for a in answers if not isinstance(a, Refused | None) for b in a}
    return given - {b.day for b in kept}


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
