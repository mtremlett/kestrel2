"""keeper_live - THE LIVE DAY'S PART OF THE KEEPER: a venue's five-minute round taken from IBKR's
paper gateway into the short database, and the archive's bars of the days before it, backfilled.
desk.keeper calls it in each venue's hours; the words it returns are the keeper's."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import datetime, timedelta
from pathlib import Path

from desk import archive, bars, live
from desk.bars import Five
from desk.lines import YARDSTICK, Line
from desk.store import Refused

RECENT = timedelta(days=7)  #: how far back a five-minute round asks: the week kept hot
Ask = Callable[[Line, datetime], tuple[Five, ...]]


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
