"""halt - WHAT STOPS THE DESK BUYING. A HALT (FIL-08, NS-06) is a typed record: called at a
moment for a reason, and in force until it is lifted. Nothing lifts one because time has
passed. While one is in force the send path refuses every buy, and the rules and the stops
sell as ever; every day's record names it, that day does not count, and the desk says so each
day, counting the days. THE BLOCKERS (FIL-04, TRD-01) are everything that can stand between a
rule's signal and its whole trade, each named once here; every morning's orders leave one list
of every blocker with the signals it blocked. Sending what is said to him is the messenger's."""

from __future__ import annotations

import csv
from collections.abc import Iterable
from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta
from enum import Enum
from pathlib import Path

from desk.orders import Refused
from desk.store import _write

HALTS, BLOCKED = "halts.csv", "blocked"  #: the one record of halts; a folder, a list a morning
COLUMNS = ("called", "why", "lifted", "lifted_why")
LISTED = ("order_id", "blocker", "filled", "reason")


class Blocker(Enum):
    """EVERY BLOCKER, in the order the day meets them: a signal that did not become its whole
    trade was stopped by exactly one of these, and its answer names which."""

    KILL = "The kill switch is on"
    HALT = "A halt is in force"
    BOOK = "The book is not the broker's"
    HELD = "The line is held already, or was sold this morning"
    GATE = "The pre-trade gate refused it"
    BROKER = "The broker did not take it whole"


class Stopped(Refused):
    """An order the send path refused before it went, and the blocker that stood in its way."""

    def __init__(self, blocker: Blocker, words: str) -> None:
        super().__init__(words)
        self.blocker = blocker


@dataclass(frozen=True)
class Halt:
    """One halt. Its moments are in UTC and each has its reason, or it cannot be made."""

    at: datetime  #: when it was called
    why: str  #: with the moment, what the halt is known by
    lifted: tuple[datetime, str] | None = None  #: when and why; None while it is in force

    def __post_init__(self) -> None:
        for moment, why in ((self.at, self.why), *((self.lifted,) if self.lifted else ())):
            if moment.utcoffset() != timedelta(0) or not why.strip() or moment < self.at:
                raise ValueError(
                    f"a halt called at {self.at} for {self.why!r}, lifted {self.lifted}: each "
                    "needs a time in UTC and a reason, and is lifted no sooner than called"
                )

    @property
    def since(self) -> str:
        return f"called {self.at:%Y-%m-%d %H:%M} UTC: {self.why}"

    def on(self, day: date) -> bool:
        """In force at some moment of the day, by UTC's date: the day it was called on, the
        day it was lifted on, whatever the hour, and every day between."""
        return self.at.date() <= day and (self.lifted is None or day <= self.lifted[0].date())

    def words(self, day: date) -> str:
        """What the desk says of it on a day it was in force: on its last, that it is lifted."""
        if self.lifted is not None and self.lifted[0].date() <= day:
            at, why = self.lifted
            return f"HALT LIFTED at {at:%Y-%m-%d %H:%M} UTC ({why}); it was {self.since}."
        return (
            f"HALT IN FORCE, day {(day - self.at.date()).days + 1}, {self.since}. The desk buys "
            "nothing until it is lifted; the rules and the stops sell as ever."
        )


@dataclass(frozen=True)
class Blocked:
    """A signal that did not become its whole trade one morning."""

    order_id: str  #: the signal, by the order it asked for: its day, its rule and its line
    blocker: Blocker
    filled: int  #: the shares that did trade: all but a part fill has none
    reason: str  #: the refusal, or the broker's answer, in its own words


def call(root: Path, at: datetime, why: str) -> Halt:
    """A HALT IS CALLED: from now the send path sends no buy. Whoever calls it gives the
    moment and the reason, and no well-made halt is refused, whatever the record holds; one
    already in force for that moment and reason is the same halt, and is not kept twice."""
    record, halt = kept(root), Halt(at, why)
    if halt not in record:
        _keep(root / HALTS, COLUMNS, map(_row, (*record, halt)))
    return halt


def lift(root: Path, halt: Halt, at: datetime, why: str) -> Halt:
    """A HALT IS LIFTED: that one, as it stands in force (in_force), and no other; by whoever
    may, the operator, or the part that called it once what it was called for has ended,
    with the reason. One that is not in force is an error."""
    record, lifted = list(kept(root)), replace(halt, lifted=(at, why))
    if halt.lifted is not None or halt not in record:
        raise ValueError(f"no halt {halt.since} is in force: none lifted at {at}, {why!r}")
    record[record.index(halt)] = lifted
    _keep(root / HALTS, COLUMNS, map(_row, record))
    return lifted


def kept(root: Path) -> tuple[Halt, ...]:
    """Every halt ever called, oldest first, lifted or not. No record is a desk never halted;
    one that is there and is not exactly as the desk writes it is an error, never no halt."""
    path = root / HALTS
    return tuple(_halt(path, row) for row in _rows(path, COLUMNS)) if path.exists() else ()


def _halt(path: Path, row: list[str]) -> Halt:
    try:
        called, why, at, lifted_why = row
        lifted = (datetime.fromisoformat(at), lifted_why) if at else None
        halt = Halt(datetime.fromisoformat(called), why, lifted)
    except ValueError as fault:
        raise ValueError(f"{path}: {row} is no halt of the desk's: {fault}") from fault
    if _row(halt) != tuple(row):
        raise ValueError(f"{path}: {row} is no halt as the desk writes one, so nothing is bought")
    return halt


def _row(halt: Halt) -> tuple[str, ...]:
    at, why = halt.lifted or (None, "")
    return (halt.at.isoformat(), halt.why, at.isoformat() if at else "", why)


def in_force(root: Path) -> tuple[Halt, ...]:
    """The halts in force now, called and not lifted: the send path asks before every buy."""
    return tuple(halt for halt in kept(root) if halt.lifted is None)


def on(root: Path, day: date) -> tuple[Halt, ...]:
    """The halts in force at some moment of a day (Halt.on): the day's record names them."""
    return tuple(halt for halt in kept(root) if halt.on(day))


def said(root: Path, day: date) -> str | None:
    """WHAT THE DESK SAYS EVERY DAY a halt is in force, in plain English, each halt with its
    reason and the days it has run; None on a day with none."""
    return " ".join(halt.words(day) for halt in on(root, day)) or None


def keep_morning(root: Path, day: date, blocked: Iterable[Blocked]) -> None:
    """Keep a morning's list, in place of any kept for that day: as its last run left it."""
    rows = ((b.order_id, b.blocker.name, b.filled, b.reason) for b in blocked)
    _keep(root / BLOCKED / f"{day}.csv", LISTED, rows)


def morning(root: Path, day: date) -> dict[Blocker, tuple[Blocked, ...]]:
    """THE MORNING'S ONE LIST: every blocker, each with the signals it blocked that morning,
    none left off for having blocked nothing. A day whose orders were never sent has no list,
    which is an error, never a morning on which nothing was blocked."""
    path = root / BLOCKED / f"{day}.csv"
    if not path.exists():
        raise ValueError(f"{day}: no list of blockers, its orders were never sent")
    try:
        found = [Blocked(o, Blocker[b], int(n), why) for o, b, n, why in _rows(path, LISTED)]
    except (KeyError, ValueError) as fault:
        raise ValueError(f"{path}: not a list of the desk's blockers: {fault!r}") from fault
    return {blocker: tuple(b for b in found if b.blocker is blocker) for blocker in Blocker}


def listed(root: Path, day: date) -> str:
    """The morning's list in plain English, for whoever must be told."""
    found = morning(root, day)
    said = (f"{b.value}: {', '.join(s.order_id for s in found[b]) or 'none'}." for b in Blocker)
    return f"BLOCKERS, {day}: {sum(map(len, found.values()))} signals blocked. {' '.join(said)}"


def _rows(path: Path, names: tuple[str, ...]) -> list[list[str]]:
    """A kept file's rows under its own names, or an error: never a file read as empty."""
    with path.open(newline="", encoding="utf-8") as kept_file:
        rows = list(csv.reader(kept_file))
    if rows[:1] != [list(names)]:
        raise ValueError(f"{path}: not the desk's record of halts and blockers")
    return rows[1:]


def _keep(path: Path, names: tuple[str, ...], rows: Iterable[tuple[object, ...]]) -> None:
    """Written whole, then swapped in, by the store's one writer."""
    path.parent.mkdir(parents=True, exist_ok=True)
    _write(path, names, list(rows))
