"""day_parts - the day's published record: its fields, its verdict and the file that keeps
it, read and written as the desk's records. desk.day gives them to its callers."""

from __future__ import annotations

import csv
from dataclasses import astuple, dataclass, field
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from desk.orders import Charges

RECORDS = "records.csv"
MONEY = ("day", "profit", *Charges.__dataclass_fields__, "market", "worth", "counted", "heat")
HEADER = (*MONEY, "halted", "stopped", "differ")
BEFORE_HEAT = [name for name in HEADER if name != "heat"]  #: the records' names until the heat


@dataclass(frozen=True)
class Record:
    """One day, as published: pounds, each amount rounded once, to the penny, where the record
    is made. A day whose book is not the broker's names the lines and has no profit; no other
    day lacks one. With it, kept exact, what the next day's record carries on from. A day with
    a halt in force names it, and keeps its number. THE DAY'S VERDICT (NS-06): it counts only
    if its book was the broker's, no halt was in force, and its orders were sent, none of
    them stopped for a halt or the kill switch."""

    day: date
    #: The book's gain after every cost, since the last record that carried one: the day's
    #: own, unless days before it were withheld. None when the book is not the broker's.
    profit: Decimal | None
    costs: Charges  #: every cost behind that gain, line by line: none can be left out
    market: Decimal  #: what the capital would have earned simply holding the market those days
    mismatches: tuple[str, ...]  #: lines where the desk's book and the broker's differ
    worth: Decimal  #: what the book held at the day's end was worth: the next record opens here
    counted: int  #: the ledger's fills dated by the day, each counted by a record up to this one
    #: the halts in force that day, each by the moment it was called, as halt.kept stood. A
    #: record made without these two says nothing was sent, and does not count
    halted: tuple[datetime, ...] = ()
    stopped: int | None = None  #: signals the kill switch or a halt refused; None, none sent
    #: THE BOOK'S HEAT, reported only: the pounds lost if every stop held at the day's end were
    #: hit, each line at its stop or, if worse, its worst recorded overnight gap (_heat). None:
    #: not recorded (a record made before the heat, or a held line whose stop level was not kept)
    heat: Decimal | None = None
    counts: bool = field(init=False)  #: the verdict

    def __post_init__(self) -> None:
        clear = self.profit is not None and not self.halted and self.stopped == 0
        object.__setattr__(self, "counts", clear)
        if (self.profit is None) != bool(self.mismatches):
            raise ValueError(
                f"{self.day}: a profit of {self.profit} with the book and the broker's "
                f"differing on {list(self.mismatches)}"
            )


def _row(r: Record) -> tuple[object, ...]:
    """A record as it is kept: the lines that differ last, as many as there are."""
    money = (r.day, r.profit, *astuple(r.costs), r.market, r.worth, r.counted, r.heat)
    return (*money, " ".join(h.isoformat() for h in r.halted), r.stopped, *r.mismatches)


def records(root: Path) -> tuple[Record, ...]:
    """Every day's record the desk has published, oldest first, as it was published. A file
    there whose first line is not the records' own names is an error, never a day short. A
    row that ends at its money is a record made without its halts: it does not count."""
    path = root / RECORDS
    if not path.exists():
        return ()
    with path.open(newline="", encoding="utf-8") as kept:
        rows = list(csv.reader(kept))
    if rows[:1] == [BEFORE_HEAT]:  #: records made before the heat have none
        rows = [rows[0], *(row[:10] + [""] + row[10:] for row in rows[1:])]
        rows[0] = list(HEADER)
    if rows[:1] != [list(HEADER)]:
        raise ValueError(f"{path}: not the desk's records")
    return tuple(
        Record(
            date.fromisoformat(row[0]),
            Decimal(row[1]) if row[1] else None,
            Charges(*map(Decimal, row[2:7])),
            Decimal(row[7]),
            tuple(row[13:]),
            Decimal(row[8]),
            int(row[9]),
            tuple(map(datetime.fromisoformat, row[11].split())),
            int(row[12]) if row[12] else None,
            Decimal(row[10]) if row[10] else None,
        )
        for row in (kept if kept[10:] else [*kept, "", "", ""] for kept in rows[1:])
    )
