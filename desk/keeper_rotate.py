"""keeper_rotate - THE KEEPER'S RECORD AND THE ORDER IT ASKS THE BROKER IN: a venue's last refresh
(`Kept`, read and written whole), and which lines IBKR is asked for first: the yardstick before
all, then the lines not asked on the last call, so a line IBKR refuses goes to the back and
never starves the others (R-RUNNER-313)."""

from __future__ import annotations

import json
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from desk.lines import YARDSTICK, Line

RECORD = "kept.json"  #: in each venue's folder of the daily store: its last refresh


@dataclass(frozen=True)
class Kept:
    """A venue's last refresh of its daily bars, as its record keeps it."""

    day: date  #: the day it readied: every session of the venue before it was asked for
    at: datetime  #: when the archive was last asked
    tries: int  #: how many calls have asked for this day on this date
    parked: Mapping[str, str]  #: each parked line's symbol, and why
    refused: frozenset[str]  #: those of them the archive would not answer for
    rules: str = ""  #: the store rules' version it was cleaned under; none in an old record
    unasked: frozenset[str] = frozenset()  #: lines the broker was not asked or refused: asked again
    tried: frozenset[str] = frozenset()  #: the lines the broker was asked on this call
    notes: tuple[str, ...] = ()  #: each source of a newest bar, and each disagreement of sources


def load(folder: Path) -> Kept | None:
    """A venue's record; none before its first refresh."""
    if not (folder / RECORD).is_file():
        return None
    said = json.loads((folder / RECORD).read_text(encoding="utf-8"))
    day, at = date.fromisoformat(said.pop("day")), datetime.fromisoformat(said.pop("at"))
    for names in ("refused", "unasked", "tried"):  # an old record has no unasked or tried
        said[names] = frozenset(said.get(names, ()))
    return Kept(day, at, **said)


def record(folder: Path, kept: Kept) -> None:
    """The record written whole, then swapped in, after the bars."""
    said = {"day": kept.day.isoformat(), "at": kept.at.isoformat(), "tries": kept.tries}
    said |= {"parked": dict(kept.parked), "refused": sorted(kept.refused), "rules": kept.rules}
    said |= {"unasked": sorted(kept.unasked), "tried": sorted(kept.tried)}
    folder.mkdir(parents=True, exist_ok=True)
    part = folder / f"{RECORD}.part"
    part.write_text(json.dumps(said, indent=1), encoding="utf-8")
    part.replace(folder / RECORD)


def order(lines: Sequence[Line], tried: Collection[str]) -> list[Line]:
    """The lines in the order the broker is asked: those not asked on the last call first, the
    yardstick ahead of the rest of them; the lines list order is kept otherwise."""
    return sorted(lines, key=lambda line: (line.symbol in tried, line != YARDSTICK))
