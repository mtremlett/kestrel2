"""goflat - GO FLAT (R-RUNNER-162), a second kill level: a flag file in the desk's folder
halts all buying and cancels the buys working (halt.stop, by "go flat", the operator's alone
to lift), and each step then
sells every line held, on a venue that is open, through the one send path and its gate. Taking
the flag away resumes nothing: only the operator's lift of that halt does. Paper only."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path

from desk import book, halt, venues
from desk.broker import Broker
from desk.halt import Halt, Stopped
from desk.lines import LINES
from desk.orders import Refused, Sale, Settings

FLAG, BY = "GO_FLAT", "go flat"  #: the flag file, under the desk's folder; who calls the halt
DAYS = timedelta(days=9)  #: how far back the venue's calendar is asked for its session before


def called(root: Path) -> Halt | None:
    """The go-flat halt in force, or None."""
    return next((h for h in halt.in_force(root) if h.by == BY), None)


def state(root: Path) -> str | None:
    """'go flat since HH:MM' (UTC) while it is in force, else None."""
    return f"go flat since {h.at:%H:%M}" if (h := called(root)) else None


def _before(venue: str, today: date) -> date:
    """The venue's session before today, the date a sale's id carries."""
    return venues.sessions(venue, today - DAYS, today)[-2:][0]


def step(root: Path, broker: Broker, room: Settings, now: datetime) -> list[str]:
    """One step: a flag with no go-flat halt calls one; while one is in force a sale of all
    that is held goes for every line whose venue is open. Each answer is a line of words."""
    if (root / FLAG).exists() and called(root) is None:
        halt.stop(root, broker, now, f"the {FLAG} flag appeared", BY)
    if called(root) is None:
        return []
    lines, said = {line.symbol: line for line in LINES}, []
    for symbol, shares in sorted(book.positions(root).items()):
        line = lines[symbol]
        if shares > 0 and venues.open_at(line.venue, now):
            sale = Sale(f"{_before(line.venue, now.date()):%Y%m%d}-goflat-{symbol}", line, shares)
            try:
                sent = book.send(root, broker, sale, room)
                said.append(f"{sale.order_id}: {sent.filled} of {shares} shares sold")
            except (Stopped, Refused) as refused:
                said.append(str(refused))
    return said
