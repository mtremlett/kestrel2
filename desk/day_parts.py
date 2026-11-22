"""day_parts - the day's published record: its fields, its verdict and the file that keeps
it, read and written as the desk's records; and the day's smaller steps (signals left
unreached, the loss-limit alert, the stop to put back, lines no rule read, where the book
stands, the lines due, what the gate reads before a buy). desk.day gives them to its callers."""

from __future__ import annotations

import csv
from collections.abc import Mapping, Sequence
from dataclasses import astuple, dataclass, field
from datetime import UTC, date, datetime, time
from decimal import Decimal
from pathlib import Path

from desk import book, day_money, halt, venues
from desk.halt import Blocker
from desk.lines import LINES, Line
from desk.orders import Charges, Settings, is_zoo, moves, order_id_of
from desk.risk import Standing
from desk.store import Bar
from desk.strategy import Action, Decision

RECORDS = "records.csv"
FX = ("currency", "interest")
MONEY = ("day", "profit", *Charges.__dataclass_fields__, "market", "worth", "counted", "heat", *FX)
HEADER = (*MONEY, "halted", "stopped", "differ")
BEFORE_FX = [name for name in HEADER if name not in FX]  #: the records' names until currency
BEFORE_HEAT = [name for name in BEFORE_FX if name != "heat"]  #: and until the heat


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
    #: KEPT BESIDE THE PROFIT, NOT IN IT (BIC-03, BIC-04): the pounds the currency's move gave the
    #: closed trades and the open holdings, and the interest idle cash earned since the first fill,
    #: as the day ended. None: not recorded (a record before them, or a fill's day's rate unkept)
    currency: Decimal | None = None
    interest: Decimal | None = None
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
    money = (
        r.day,
        r.profit,
        *astuple(r.costs),
        r.market,
        r.worth,
        r.counted,
        r.heat,
        r.currency,
        r.interest,
    )
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
        rows = [BEFORE_FX, *(row[:10] + [""] + row[10:] for row in rows[1:])]
    if rows[:1] == [BEFORE_FX]:  #: records made before currency and interest have none
        rows = [list(HEADER), *(row[:11] + ["", ""] + row[11:] for row in rows[1:])]
    if rows[:1] != [list(HEADER)]:
        raise ValueError(f"{path}: not the desk's records")
    return tuple(
        Record(
            date.fromisoformat(row[0]),
            Decimal(row[1]) if row[1] else None,
            Charges(*map(Decimal, row[2:7])),
            Decimal(row[7]),
            tuple(row[15:]),
            Decimal(row[8]),
            int(row[9]),
            tuple(map(datetime.fromisoformat, row[13].split())),
            int(row[14]) if row[14] else None,
            *(Decimal(row[i]) if row[i] else None for i in (10, 11, 12)),
        )
        for row in (kept + [""] * (15 - len(kept)) for kept in rows[1:])
    )


def _unreached(
    root: Path, day: date, decided: Sequence[Decision], sent: Sequence[book.Sent], dead: Exception
) -> None:
    """NO SIGNAL HALF-PROCESSED (TST-08): each signal still without an answer when the desk died
    goes on the morning's list, saying so; it is decided again when the desk starts."""
    answered = {s.order_id for s in sent}
    why = f"not reached, the desk stopped on {type(dead).__name__}: {dead}"
    names = (order_id_of(d) for d in decided if d.action is not Action.HOLD)
    halt.note(
        root,
        day,
        [halt.Blocked(n, Blocker.BROKER, 0, f"{n}: {why}") for n in names if n not in answered],
    )


def _alert(root: Path, day: date, settings: Settings, tell: book.Tell | None) -> None:
    """ON PAPER A LOSS LIMIT REACHED IS TOLD TO HIM (halt.drawdown): the buys still go, the gate
    having refused them if the limit is past; recorded once for the day."""
    at = datetime.combine(day, time(), UTC)
    words = halt.drawdown(root, at, standing(root, day), settings)
    if words and tell is not None:
        tell(f"drawdown {day}", words)


def _barred(d: Decision) -> book.Sent:
    """The answer for a buy by a strategy that met its kill condition: not sent, and why."""
    name = order_id_of(d)
    why = f"{name}: not sent, {d.strategy} met its kill condition and buys nothing"
    return book.Sent(name, 0, why, Blocker.GATE)


def _bare(
    root: Path,
    day: date,
    held: Mapping[str, int],
    unsure: set[str],
    stops: Sequence[book.Difference],
) -> None:
    """A HOLDING WITH NO STOP: each line whose shares the broker holds as the book does, with
    fewer of them under a stop resting there, goes on the day's list under the stop it is due
    (its newest buy's, at the level kept for it, book.levels), saying what to put back."""
    kept = book.levels(root)
    due = {f.symbol: f"{f.order_id}-stop" for f in book.fills(root) if f.quantity > 0}
    resting = {d.name: d.broker for d in stops}
    level = {s: kept.get(due[s], "a level never kept, so set one by hand") for s in held}
    bare = [
        halt.Blocked(
            due[s],
            Blocker.BOOK,
            0,
            f"{s}: {n} shares held, {resting[s]} under a stop at"
            f" the broker; put back {due[s]}, selling {n} at {level[s]}",
        )
        for s, n in held.items()
        if s in resting and s not in unsure and resting[s] < n
    ]
    halt.note(root, day, bare)


def _unread(root: Path, lines: Sequence[Line], due: Mapping[str, Line], day: date) -> None:
    """Open the morning's list with the lines no rule could decide: its venue trades today
    and its bars do not end at the session before. A line read now leaves the list."""
    late = [s.symbol for s in lines if s.symbol not in due and venues.sessions(s.venue, day, day)]
    why = f"no bar for the session before {day}, so no rule decided"
    unread = [halt.Blocked(symbol, Blocker.UNREAD, 0, f"{symbol}: {why}") for symbol in late]
    halt.note(root, day, unread, (line.symbol for line in lines))


def standing(root: Path, day: date, zoo: bool = False) -> Standing:
    """WHERE THE BOOK STANDS AGAINST ITS LOSS AND ORDER-RATE LIMITS when the day opens
    (canon B1, risk.loss_limit): the day's loss is the pounds the last published record lost
    (0 when it gained or was withheld), the week's the net pounds lost over the records of
    day's own ISO week, and the new lines the lines first bought today. THE ZOO STANDS APART
    (orders.is_zoo, his 22 Nov ruling): the desk's standing leaves out its round trips' pounds
    and its lines, and the zoo's own (zoo) counts them alone, so neither spends the other's."""
    fills = book.fills(root)
    made = _zoo_made(root) if any(is_zoo(f.order_id) for f in fills) else {}
    profits = list[tuple[date, Decimal]]()
    for r in records(root):
        theirs = made.get(r.day, Decimal(0))  #: a withheld record (no profit) counts 0 for both
        ours = Decimal(0) if r.profit is None else r.profit - theirs
        profits.append((r.day, theirs if zoo else ours))
    week = sum((p for d, p in profits if d.isocalendar()[:2] == day.isocalendar()[:2]), Decimal(0))
    lost = -profits[-1][1] if profits else Decimal(0)
    bought = {
        f.symbol for f in fills if f.day == day and f.quantity > 0 and is_zoo(f.order_id) == zoo
    }
    return Standing(max(lost, Decimal(0)), max(-week, Decimal(0)), len(bought))


def _zoo_made(root: Path) -> dict[date, Decimal]:
    """The zoo's pounds after every cost by the day each of its round trips closed."""
    made = dict[date, Decimal]()
    for trip in book.round_trips(root, LINES):
        if is_zoo(trip.buy.order_id):
            made[trip.sell.day] = made.get(trip.sell.day, Decimal(0)) + trip.profit
    return made


def _due(line: Line, bars: Sequence[Bar], day: date) -> bool:
    """The line's venue trades on day and its last bar is the session before: decisions
    dated any other day are not acted on."""
    return bool(bars) and venues.sessions(line.venue, bars[-1].day, day) == (bars[-1].day, day)


def _watch(
    root: Path, archive: Mapping[Line, Sequence[Bar]], rates: Mapping[str, Decimal], symbol: str
) -> tuple[dict[str, Decimal], dict[str, tuple[float, ...]]]:
    """What the gate reads of the book before a buy of the symbol: the pounds it controls per
    underlying, and the daily returns of the symbol and of the lines held."""
    return day_money.exposure(root, archive, rates), moves(
        set(book.positions(root)), archive, symbol
    )
