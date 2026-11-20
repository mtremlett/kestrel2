"""book_parts - THE LEDGER'S LOWER PARTS: the desk's one keeper of dated records, the kill switch's
record (what is on it, when and why) and the day's pounds per currency. desk.book builds on them
and gives them to its callers under the same names."""

from __future__ import annotations

import csv
from collections.abc import Iterable, Mapping, Sequence
from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from pathlib import Path
from uuid import uuid4

from desk.carry import carried
from desk.halt import Blocker, Stopped

RATES, SWITCH = "rates.csv", "switch.csv"
TURNS = ("at", "turn", "why")


class Switch(Enum):
    """A word on the kill switch's record: pulled, released, or drilled on a rehearsal desk."""

    ON = "on"
    OFF = "off"
    DRILLED = "drilled"


def keep(path: Path, rows: Iterable[Sequence[object]]) -> None:
    """The desk's one keeper of dated records: written whole, then swapped in."""
    path.parent.mkdir(parents=True, exist_ok=True)
    written = path.with_name(f"{path.name}.{uuid4().hex}.tmp")  # its own, so two writers never meet
    with written.open("w", newline="", encoding="utf-8") as out:
        csv.writer(out).writerows(rows)
    written.replace(path)


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
    """Every rate kept, by day and currency."""
    path = root / RATES
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as saved:
        return {
            (date.fromisoformat(r["day"]), r["currency"]): Decimal(r["rate"])
            for r in csv.DictReader(saved)
        }


def rate(root: Path, currency: str, day: date) -> Decimal:
    """Pounds per unit of a currency kept for a day, carried over a UK-only holiday (desk.carry)."""
    kept = carried({d: r for (d, c), r in rates_kept(root).items() if c == currency}, day)
    if kept is None:
        raise ValueError(f"no {currency} rate kept for {day}")
    return kept
