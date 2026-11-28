"""running_notes - WHAT THE DESK UNATTENDED IS GIVEN, AND ITS RECORD. The `Desk` a step is
given beside the moment (its records, its doors out), and the record of each thing it did
(`notes`, kept by `_note`): read by the step, its rounds and his messages alike."""

from __future__ import annotations

import csv
from collections.abc import Callable, Collection, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import NamedTuple

from desk import book, intraday, messenger, paper
from desk.lines import Line
from desk.messenger_parts import Mail
from desk.orders import Settings
from desk.store import Bar

NOTES, HEAD = "running.csv", ("at", "what", "words")
VENUES = {"LSE": "London", "US": "New York"}  #: each venue of the desk's lines, as he is told it
DAY, HOUR = timedelta(days=1), timedelta(hours=1)
ORDERS, RECOVERED, UNCLEAN, TROUBLE = "orders {}", "recovered", "unclean", "trouble"
ONCE = (UNCLEAN, TROUBLE)  #: told once a day, the first: of a failure, the first of its kind
ZOO_NOTE = "zoo"  #: the name the zoo's notes are kept under: told in the hourly message alone
MACHINERY = "MACHINERY TEST, NOT EVIDENCE OF AN EDGE"  #: said of every zoo order, never a verdict
Rules = Mapping[str, Callable[[], intraday.IntradayRule]]
Saved = tuple[Mapping[Line, Sequence[Bar]], Collection[str]]  #: bars by line; who is parked


@dataclass(frozen=True)
class Desk:
    """All a step is given beside the moment: the desk's records, and its doors out."""

    root: Path  #: where the ledger, the checks, the switch, the records and the messages are
    room: Settings
    post: messenger.Post  #: the door to his phone
    #: A day's pounds per unit of each currency: the same answer at every asking.
    rates: Callable[[date], Mapping[str, Decimal]]
    #: The fast store of five-minute bars for the crash watch, and the one door to the daily
    #: bars, as last kept by the store's keeper (no archive is asked at a step).
    hot: Path
    held: Callable[[date], Saved]
    door: paper.Door  #: who the desk is at the paper Gateway
    mail: Mail | None = None  #: the email door, if his SMTP_ settings are set
    #: The intraday rules the desk may trade, as `intraday.RULES`: none until one passes the ladder.
    rules: Rules = field(default_factory=lambda: intraday.RULES)
    zoo: bool = False  #: whether the zoo's rules trade on paper too (ZOO_ON): OFF unless set

    def __post_init__(self) -> None:
        """A day's rates are fixed at their first record: later steps price at the kept ones."""
        fetch, root = self.rates, self.root

        def first(day: date) -> Mapping[str, Decimal]:
            kept = {c: r for (d, c), r in book.rates_kept(root).items() if d == day}
            return kept or fetch(day)

        object.__setattr__(self, "rates", first)


class Note(NamedTuple):
    """One thing the desk did unattended, as its record keeps it and as he is told it."""

    at: datetime
    what: str
    words: str


def notes(root: Path) -> tuple[Note, ...]:
    """What the desk did unattended, oldest first. A file there that is not this record is
    an error, never a day on which nothing was done."""
    path = root / NOTES
    if not path.exists():
        return ()
    with path.open(newline="", encoding="utf-8") as kept:
        rows = list(csv.reader(kept))
    if rows[:1] != [list(HEAD)]:
        raise ValueError(f"{path}: not the record of what the desk did, so nothing is done")
    return tuple(Note(datetime.fromisoformat(at), what, words) for at, what, words in rows[1:])


def _note(root: Path, now: datetime, what: str, words: str) -> None:
    """Keep one thing done; of those told once a day (ONCE), the first alone."""
    kept = notes(root)
    if what.split()[0] in ONCE and any((n.what, n.at.date()) == (what, now.date()) for n in kept):
        return
    rows = ((n.at.isoformat(), n.what, n.words) for n in (*kept, Note(now, what, words)))
    book._write(root / NOTES, [HEAD, *rows])
