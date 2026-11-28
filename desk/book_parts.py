"""book_parts - THE LEDGER'S LOWER PARTS: the desk's one keeper of dated records, the kill switch's
record (what is on it, when and why) and the day's pounds per currency. desk.book builds on them
and gives them to its callers under the same names."""

from __future__ import annotations

import csv
import io
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from os import SEEK_END
from pathlib import Path
from shutil import copyfile
from typing import Generic, TypeVar, cast
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
NEWLINE = bytes([10])  #: the byte every row the desk keeps ends with
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


@dataclass(frozen=True)
class Rows(Generic[T]):
    """A FILE THE DESK ADDS ROWS TO, read: made, its reading from all its rows (the header first);
    grown, a reading with rows added after it (add) taken in, which must equal made of them all.
    It is a parse (read_once), so a day's reading grows by the day's rows (27 Nov: the records,
    rates and ledger parsed whole after each day's write made SimCity's day grow with its age)."""

    made: Callable[[list[list[str]]], T]
    grown: Callable[[T, list[list[str]]], T]

    def __call__(self, path: Path) -> T:
        with path.open(newline="", encoding="utf-8") as kept:
            rows = list(csv.reader(kept))
        try:
            return self.made(rows)
        except ValueError as wrong:  #: said again with the file it was read from
            raise ValueError(f"{path}: {wrong}") from wrong


def add(path: Path, header: Sequence[str], rows: Iterable[Sequence[object]]) -> bool:
    """THE DESK'S ONE WAY TO ADD ROWS to a record it keeps: the file as it was and the rows after
    it, written whole and swapped in as keep does. A reading of it kept by a Rows (read_once) is
    grown by the rows alone; any other is dropped. A file that does not begin with header is not
    added to (False), nor one whose last row is unended, for the caller to write whole (keep);
    none yet is written with header."""
    text = io.StringIO(newline="")
    csv.writer(text).writerows(rows)
    if not path.exists():
        keep(path, [header, *csv.reader(io.StringIO(text.getvalue(), newline=""))])
        return True
    line = io.StringIO(newline="")
    csv.writer(line).writerow(header)
    head, stamp = line.getvalue().encode(), _stamp(path)
    written = path.with_name(f"{path.name}.{uuid4().hex}.tmp")  #: one per writer, never shared
    try:
        copyfile(path, written)
        with written.open("r+b") as out:
            if out.read(len(head)) != head or out.seek(-1, SEEK_END) < 0 or out.read(1) != NEWLINE:
                return False  #: another header, or a last row unended: added to, it would break
            out.seek(0, SEEK_END)
            out.write(text.getvalue().encode())
        written.replace(path)
    finally:
        written.unlink(missing_ok=True)
    more = list(csv.reader(io.StringIO(text.getvalue(), newline="")))
    for kind, (read, seen, reading) in list(_READ.items()):
        if read == path:
            del _READ[kind]
            if seen == stamp and isinstance(kind[1], Rows):
                _READ[kind] = (path, _stamp(path), kind[1].grown(reading, more))
    return True


def _stamp(path: Path) -> tuple[int, int, int]:
    seen = path.stat()
    return seen.st_ino, seen.st_mtime_ns, seen.st_size


def read_once(path: Path, parse: Callable[[Path], T]) -> T:
    """A file's reading by parse, read again only once the file has changed (_READ). Its
    writers go through keep: a rewrite in place of the same size, inside the clock's tick,
    keeps the stamp and would be read stale."""
    stamp, kind = _stamp(path), (path.name, parse)
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
    known, kept, new = _rates_read(root), rates_kept(root), list[tuple[date, str, Decimal]]()
    for currency, rate in rates.items():
        if not (rate.is_finite() and rate > 0) or (currency == "GBP" and rate != 1):
            raise ValueError(f"{day}: a rate of {rate} pounds per {currency}")
        if kept.setdefault((day, currency), rate) != rate:
            raise ValueError(f"{day}: {currency} was kept at {kept[day, currency]}, not {rate}")
        new += [] if (day, currency) in known else [(day, currency, rate)]
    if new and not add(root / RATES, RATED, new):  #: a file of another hand's: written whole
        keep(root / RATES, [RATED, *((*key, r) for key, r in kept.items())])


def rates_kept(root: Path) -> dict[tuple[date, str], Decimal]:
    """Every rate kept, by day and currency: a copy of the file's one reading (read_once)."""
    return dict(_rates_read(root))


def _rates_read(root: Path) -> Mapping[tuple[date, str], Decimal]:
    path = root / RATES
    return read_once(path, _RATES) if path.exists() else {}


def _rate_rows(rows: list[list[str]]) -> dict[tuple[date, str], Decimal]:
    return {(date.fromisoformat(r[0]), r[1]): Decimal(r[2]) for r in rows if r}  #: none blank


def _body(rows: list[list[str]]) -> list[list[str]]:
    """The rates' rows after their header; a file that does not begin with it is not the desk's."""
    if rows[:1] != [list(RATED)]:
        raise ValueError("not the desk's rates")
    return rows[1:]


def _by_grown(
    kept: dict[str, dict[date, Decimal]], rows: list[list[str]]
) -> dict[str, dict[date, Decimal]]:
    by = {currency: dict(days) for currency, days in kept.items()}
    for (day, currency), pounds in _rate_rows(rows).items():
        by.setdefault(currency, {})[day] = pounds
    return by


RATED = ("day", "currency", "rate")
_RATES = Rows(lambda rows: _rate_rows(_body(rows)), lambda kept, rows: {**kept, **_rate_rows(rows)})
_BY_CURRENCY = Rows(lambda rows: _by_grown({}, _body(rows)), _by_grown)


def pounds_per(root: Path) -> Callable[[str, date], Decimal]:
    """Pounds per unit of a currency kept for a day, carried over a UK-only holiday (desk.carry),
    the rates read once until they change (read_once; 22 Nov: once a trip hung SimCity)."""
    path = root / RATES
    by = read_once(path, _BY_CURRENCY) if path.exists() else {}

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
