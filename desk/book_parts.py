"""book_parts - THE LEDGER'S LOWER PARTS: the desk's one keeper of dated records, the kill switch's
record (what is on it, when and why) and the day's pounds per currency. desk.book builds on them
and gives them to its callers under the same names."""

from __future__ import annotations

import csv
from collections.abc import Callable, Iterable, Mapping, Sequence
from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import TypeVar, cast
from uuid import uuid4

from desk.broker import Broker, Report
from desk.carry import carried
from desk.halt import Blocker, Stopped

RATES, SWITCH, CANCELS = "rates.csv", "switch.csv", "cancels.csv"
TURNS = ("at", "turn", "why")
T = TypeVar("T")

#: each file's reading, kept under the file's (inode, mtime ns, size) when it was read: a SimCity
#: day asks for the fills some forty times, the rates seventeen, the records five, and reading
#: them whole each time made a day's work grow with the days behind it (the deep run's 7200 s,
#: 22 and 27 Nov). One reading of each kind is kept, the newest, so a night of a hundred worlds
#: never holds a hundred ledgers; the one writer (keep) drops a file's own, so the next read is
#: of what it wrote.
_READ: dict[tuple[str, Callable[[Path], object]], tuple[Path, tuple[int, int, int], object]] = {}


class Switch(Enum):
    """A word on the kill switch's record: pulled, released, or drilled on a rehearsal desk."""

    ON = "on"
    OFF = "off"
    DRILLED = "drilled"


def keep(path: Path, rows: Iterable[Sequence[object]]) -> None:
    """The desk's one keeper of dated records: written whole, then swapped in."""
    path.parent.mkdir(parents=True, exist_ok=True)
    written = path.with_name(f"{path.name}.{uuid4().hex}.tmp")  #: one per writer, never shared
    try:
        with written.open("w", newline="", encoding="utf-8") as out:
            csv.writer(out).writerows(rows)
        written.replace(path)
    finally:
        written.unlink(missing_ok=True)
        for kind in [kind for kind, (read, _, _) in _READ.items() if read == path]:
            del _READ[kind]


def read_once(path: Path, parse: Callable[[Path], T]) -> T:
    """A file's reading by parse, read again only once the file has changed (_READ)."""
    seen = path.stat()
    stamp, kind = (seen.st_ino, seen.st_mtime_ns, seen.st_size), (path.name, parse)
    kept = _READ.get(kind)
    if kept is None or kept[:2] != (path, stamp):
        _READ[kind] = kept = (path, stamp, parse(path))
    return cast(T, kept[2])


def switch(root: Path) -> tuple[tuple[datetime, Switch, str], ...]:
    """The kill switch's record, oldest first; one not readable whole is an error."""
    if not (path := root / SWITCH).exists():
        return ()
    with path.open(newline="", encoding="utf-8") as record:
        rows = list(csv.reader(record))
    if rows[:1] != [list(TURNS)]:
        raise ValueError(f"{path}: not the kill switch's record, so nothing is sent")
    return tuple(entry(datetime.fromisoformat(at), Switch(to), why) for at, to, why in rows[1:])


def entry(at: datetime, to: Switch, why: str) -> tuple[datetime, Switch, str]:
    """An entry of the kill switch's record: a moment in UTC and a reason, or an error."""
    if at.utcoffset() != timedelta(0) or not why.strip():
        raise ValueError(f"the kill switch, {to.value} at {at} for {why!r}: no UTC time or reason")
    return at, to, why


def unless_killed(root: Path, order_id: str) -> None:
    """Refuse the order while the kill switch is on, in the switch's own words."""
    if on := killed(root):
        raise Stopped(Blocker.KILL, f"{order_id}: not sent, {on}")


def killed(root: Path) -> str | None:
    """The kill switch's word while it is on, when and why; None while off. A drill is neither."""
    turns = [(at, to, why) for at, to, why in switch(root) if to is not Switch.DRILLED]
    if not turns or turns[-1][1] is Switch.OFF:
        return None
    at, _, why = turns[-1]
    return f"the kill switch is on, pulled at {at:%Y-%m-%d %H:%M} UTC: {why}"


def record_rates(root: Path, day: date, rates: Mapping[str, Decimal]) -> None:
    """Keep the day's pounds per unit of each currency: fills are priced from this record."""
    kept = rates_kept(root)
    for currency, rate in rates.items():
        if not (rate.is_finite() and rate > 0) or (currency == "GBP" and rate != 1):
            raise ValueError(f"{day}: a rate of {rate} pounds per {currency}")
        if kept.setdefault((day, currency), rate) != rate:
            raise ValueError(f"{day}: {currency} was kept at {kept[day, currency]}, not {rate}")
    keep(root / RATES, [("day", "currency", "rate"), *((*key, r) for key, r in kept.items())])


def rates_kept(root: Path) -> dict[tuple[date, str], Decimal]:
    """Every rate kept, by day and currency: a copy of the file's one reading (read_once)."""
    path = root / RATES
    return dict(read_once(path, _rates)) if path.exists() else {}


def _rates(path: Path) -> dict[tuple[date, str], Decimal]:
    with path.open(newline="", encoding="utf-8") as saved:
        return {
            (date.fromisoformat(r["day"]), r["currency"]): Decimal(r["rate"])
            for r in csv.DictReader(saved)
        }


def _by_currency(path: Path) -> dict[str, dict[date, Decimal]]:
    by: dict[str, dict[date, Decimal]] = {}
    for (day, currency), pounds in read_once(path, _rates).items():
        by.setdefault(currency, {})[day] = pounds
    return by


def pounds_per(root: Path) -> Callable[[str, date], Decimal]:
    """Pounds per unit of a currency kept for a day, carried over a UK-only holiday (desk.carry),
    the rates read once until they change (read_once; 22 Nov: once a trip hung SimCity)."""
    path = root / RATES
    by = read_once(path, _by_currency) if path.exists() else {}

    def rate(currency: str, day: date) -> Decimal:
        kept = carried(by.get(currency, {}), day)
        if kept is None:
            raise ValueError(f"no {currency} rate kept for {day}")
        return kept

    return rate


def rate(root: Path, currency: str, day: date) -> Decimal:
    """Pounds per unit of a currency kept for a day, carried over a UK-only holiday (desk.carry)."""
    return pounds_per(root)(currency, day)


def cancel_all(root: Path, broker: Broker, day: date) -> tuple[str, ...]:
    """The desk's one way to cancel: the broker cancels what is working, and each order id the
    desk itself cancelled is kept by day, so a send can tell it from a broker-side cancel."""
    ids = tuple(broker.cancel())
    path = root / CANCELS
    kept: list[list[str]] = []
    if path.exists():
        with path.open(newline="", encoding="utf-8") as rows:
            kept = list(csv.reader(rows))
    keep(path, [*kept, *((i, day.isoformat()) for i in ids if not i.endswith("-stop"))])
    return ids


def retry_id(root: Path, order_id: str, report: Report | None, day: date) -> str | None:
    """The id an order is sent again under (<id>-r1), only when the broker shows it cancelled
    with nothing filled and the desk itself cancelled that id today; never an -r2."""
    if report is None or report.fills or order_id.endswith("-r1") or not (root / CANCELS).exists():
        return None
    with (root / CANCELS).open(newline="", encoding="utf-8") as kept:
        mine = (order_id, day.isoformat()) in {tuple(row) for row in csv.reader(kept)}
    return f"{order_id}-r1" if mine else None
