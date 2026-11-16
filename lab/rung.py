"""rung - THE LADDER'S FIRST RUNG: does a strategy earn on a line after the broker's costs, by
more than chance would give?

A cell's trades (`lab/cell.py`) are priced as the desk trades: decided after a close, filled at the
next open, sized by the desk's sizer from the one capital number, the line alone in the book.
A trade is judged only once both fills fall on bars the rule was shown.

ITS COSTS WHOLE, by the desk's one cost model (`orders.charges`), none worked out here: commission,
a sale's fees, half the spread and slippage on both legs (a stop's sale slips further), the
conversion on a line not in pounds and the UK tax on a purchase. Each fill is in pounds at its own
day's rate, the order sized at the morning's, so a dollar line carries the currency's gain or
loss; a pound line reads no rate. A day whose rate is needed and is missing or not above nothing
is refused loudly. A sale whose morning opens at or under the resting stop is the stop's sale.

The rung passes a strategy when it made at least MIN_TRADES judged trades and the mean of
their returns after costs is at least T_PASS standard errors above nothing. Every verdict
names the broker whose schedule priced it.

FAILING FAIRLY (LAD-06, STR-12). A strategy is failed only by a test that could have passed
it. Under MIN_TRADES judged trades the answer is THIN, never a fail. No judged trade at all is a
FAULT in the test: it says nothing of the rule. `judge` gives no verdict on code that is not the
published rule (`lab/published.py`); gains with no spread at all are refused loudly.
THE AUTHOR'S RESULT FIRST. A rule with an author's figure on file (`lab/reproduce.py`) is given
no verdict until each figure's reproduction is handed over, made by the code as it now is; the
verdict carries them. The trades counted are the effective ones: each judged whole, each its own
bet, since a rule holds one position on a line at a time.
"""

from __future__ import annotations

import enum
import hashlib
import importlib
import inspect
import json
import pkgutil
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, localcontext
from pathlib import Path
from types import ModuleType

from desk import orders
from desk.broker import Pretend
from desk.lines import Line
from desk.orders import Charges, Leg, Settings
from desk.orders import Refused as Declined
from desk.store import Bar
from desk.strategy import ARITHMETIC, Action, Decision
from lab import cell, published, reproduce
from lab.cell import Cell, Key, Record, Trade
from lab.reproduce import Reproduction

#: A-GATE (AG-01): thirty trades is the fewest a t-statistic can fairly judge; two errors the bar.
MIN_TRADES = 30
T_PASS = Decimal(2)
#: Pounds per unit of a line's currency, for each day it trades.
Rates = Mapping[date, Decimal]


class Answer(enum.IntEnum):
    """A rung's answer. Read together (folds, rungs), the least is given: fault, fail, thin."""

    FAULT = 0  #: no trades at all: the test is at fault, and says nothing of the rule
    FAIL = 1  #: enough trades, and it did not earn
    THIN = 2  #: not enough evidence: too few trades to pass it, or to fail it
    DOUBT = 3  #: neither a win nor a loss: not promoted, and not thrown away
    PASS = 4


@dataclass(frozen=True)
class Priced:
    trade: Trade
    shares: int
    paid: Decimal  #: pounds the shares' value took at the buy's fill, at that day's rate
    received: Decimal  #: pounds their value brought at the sale's fill, at its own day's rate
    costs: Charges  #: every cost of both legs, line by line, from the desk's one cost model
    held: tuple[date, date]  #: the day its buy filled, and the day its sale did
    #: the return had its stop sold it, with a stop's costs (G2); none for a hand-built trade
    stopped: Decimal | None = None

    @property
    def gross(self) -> Decimal:
        """Pounds the two prices and the two rates made, before any cost."""
        return self.received - self.paid

    @property
    def gain(self) -> Decimal:
        """The return after every cost, on the pounds the shares' value took."""
        return (self.gross - self.costs.total) / self.paid


@dataclass(frozen=True)
class Verdict:
    key: Key
    broker: str  #: whose schedule priced it
    trades: tuple[Priced, ...]
    t: Decimal | None  #: the mean gain in standard errors; None under two trades
    answer: Answer  #: PASS, FAIL, THIN or FAULT: the first rung never answers DOUBT
    reproduced: tuple[Reproduction, ...]  #: the published results behind it, if on file
    #: REFUSED: the desk's sizing declined a trade of the record (one share costs more than the
    #: room); the words of its refusal. A judged outcome with no trades, never an error or a pass.
    refusal: str | None = None

    @property
    def refused(self) -> bool:
        """The desk's sizing declined the line at this capital: nothing was priced."""
        return self.refusal is not None

    @property
    def gains(self) -> tuple[Decimal, ...]:
        """For the standard errors: each judged gain and ONE MORE planted at a stop (G2)."""
        return planted(self.trades)

    @property
    def passed(self) -> bool:
        return self.answer is Answer.PASS


def judge(
    record: Record,
    bars: Sequence[Bar],
    settings: Settings,
    rates: Rates,
    reproduced: Sequence[Reproduction] = (),
) -> Verdict:
    """The record's trades priced on the bars that made it; none before its reproductions."""
    published.proven(record.key.cell.strategy)
    behind = reproduce.settled(record.key.cell.strategy, reproduced)  #: before anything is priced
    if cell.key(record.key.cell, bars) != record.key:
        raise ValueError(f"{record.key.cell}: these bars or this code did not make the record")
    read = cell.shown(record.key.cell, bars)
    at = {bar.day: n for n, bar in enumerate(read)}
    done = [t for t in record.trades if t.sold is not None and at[t.sold] + 1 < len(read)]
    with localcontext(ARITHMETIC):
        try:
            priced = tuple(_price(record.key.cell, t, read, at, settings, rates) for t in done)
        except Declined as error:  #: the one place the sizing's refusal is judged: as REFUSED
            return Verdict(record.key, orders.BROKER, (), None, Answer.FAULT, behind, str(error))
        return verdict(record.key, priced, reproduced)


def planted(priced: Sequence[Priced]) -> tuple[Decimal, ...]:
    """The gains of the judged trades and the one more that is planted among them (G2)."""
    gains = tuple(p.gain for p in priced)
    stops = [p.stopped for p in priced if p.stopped is not None]
    return (*gains, min(stops)) if stops else gains


def verdict(
    key: Key, priced: tuple[Priced, ...], reproduced: Sequence[Reproduction] = ()
) -> Verdict:
    """The first rung's one rule, on trades already priced, once the rule's author's own
    result is reproduced."""
    behind = reproduce.settled(key.cell.strategy, reproduced)
    with localcontext(ARITHMETIC):
        t = standard_errors(planted(priced)) if len(priced) > 1 else None
    return Verdict(key, orders.BROKER, priced, t, decide(len(priced), t), behind)


def decide(trades: int, t: Decimal | None) -> Answer:
    """The first rung's one rule, wherever gains are judged: FAULT for none, THIN, PASS, FAIL."""
    if not trades:
        return Answer.FAULT
    if t is None or trades < MIN_TRADES:
        return Answer.THIN
    return Answer.PASS if t >= T_PASS else Answer.FAIL


def standing(answer: Answer, t: Decimal | None) -> tuple[Answer, bool, Decimal | int]:
    """The sort key of "worst fold", wherever folds are judged: the worst answer, then the lowest
    t, a missing t lowest of all; `min` over it gives the fold judged on, the older of equals."""
    return answer, t is not None, t or 0


def _price(
    c: Cell,
    trade: Trade,
    read: Sequence[Bar],
    at: Mapping[date, int],
    settings: Settings,
    rates: Rates,
) -> Priced:
    """Sized at the close it was decided on, bought at the next open through the desk's own
    pretend broker, where its stop rests; sold by the stop, or at the open after the sell.
    Each leg's value and its every cost in pounds at its own day's rate."""
    if trade.sold is None:
        raise ValueError(f"{c.line.symbol}, bought {trade.bought}: still held, so it has no price")
    line, decided, out = c.line, at[trade.bought], at[trade.sold] + 1
    decision = Decision(c.strategy, c.line.symbol, trade.bought, Action.BUY)
    held = read[decided + 1 : out]
    sized_at = rate(line, rates, held[0].day)
    order = orders.size(decision, line, read[decided].close, sized_at, settings, {})
    broker = Pretend({line: held}, {})
    broker.open(held[0].day)
    broker.place(order)
    for bar in held[1:]:
        broker.open(bar.day)
    (bought, *stopped) = broker.fills()
    if stopped:
        sale = (Leg.STOP, stopped[0].price, stopped[0].day)
    else:  #: an open at or under the stop is the stop's sale: it rests there before the sale
        gapped = read[out].open <= order.stop
        sale = (Leg.STOP if gapped else Leg.SALE, read[out].open, read[out].day)
    paid, buying = _leg(line, rates, order.quantity, Leg.BUY, bought.price, bought.day)
    received, selling = _leg(line, rates, order.quantity, *sale)
    at_stop, stopping = _leg(line, rates, order.quantity, Leg.STOP, order.stop, sale[2])
    ifstopped = (at_stop - paid - (buying + stopping).total) / paid
    return Priced(
        trade, order.quantity, paid, received, buying + selling, (bought.day, sale[2]), ifstopped
    )


def _leg(
    line: Line, rates: Rates, shares: int, leg: Leg, price: Decimal, day: date
) -> tuple[Decimal, Charges]:
    """A leg's value and its every cost, in pounds at its own day's rate."""
    at = rate(line, rates, day)
    return shares * price * at, orders.charges(line, leg, shares, price, at)


def rate(line: Line, rates: Rates, day: date) -> Decimal:
    """Pounds per unit of the line's currency on the day; a pound line reads no rate."""
    if line.currency == "GBP":
        return Decimal(1)
    given = rates.get(day)
    if given is None or not (given.is_finite() and given > 0):
        raise ValueError(
            f"{line.symbol}: no rate of pounds per {line.currency} to price {day} by: {given}"
        )
    return given


def standard_errors(gains: Sequence[Decimal]) -> Decimal | None:
    """The mean in standard errors, the sample's own deviation estimating the spread; None
    under two gains."""
    n = len(gains)
    if n < 2:
        return None
    mean = sum(gains, Decimal(0)) / n
    spread = sum(((g - mean) ** 2 for g in gains), Decimal(0)) / (n - 1)
    if not spread:
        raise ValueError(f"{n} gains all of {mean}: no spread to judge them by")
    return mean / (spread / n).sqrt()


def kept_closes(
    table: Path | None, last: date, fetch: Callable[[], Sequence[Bar]]
) -> dict[date, Decimal]:
    """A line's closes as one table kept at `table` (none: not kept): `fetch` is asked only
    while the table lacks the close of `last`, and what it brings is added to what is held."""
    held: dict[date, Decimal] = {}
    if table is not None and table.exists():
        rows = map(json.loads, table.read_text(encoding="utf-8").splitlines())
        held = {date.fromisoformat(day): Decimal(close) for day, close in rows}
    if table is None or last not in held:
        held = {bar.day: bar.close for bar in fetch()} | held
    if table is not None:
        table.parent.mkdir(parents=True, exist_ok=True)
        lines = (json.dumps([day.isoformat(), str(close)]) for day, close in sorted(held.items()))
        (fresh := table.with_suffix(".new")).write_text("\n".join(lines) + "\n", encoding="utf-8")
        fresh.replace(table)
    return held


@dataclass(frozen=True)
class Rung:
    """A rung as its module declares it, in `RUNG`: its name, its bar in words, and its one
    judging function, which reads the first rung's verdict (the priced trades) and answers."""

    name: str
    bar: str
    judge: Callable[[Verdict], tuple[Answer, str]]

    @property
    def code(self) -> str:
        """sha256 of the declaring module's text: part of a cell's key, so a changed rung is
        judged again."""
        text = inspect.getsource(sys.modules[self.judge.__module__])
        return hashlib.sha256(text.encode()).hexdigest()


def found(package: str = "lab") -> tuple[tuple[Rung, ...], tuple[str, ...]]:
    """The rungs the package's `rung_*` modules declare, by name order, and the names of those
    that declare none (still wired by hand). A new rung needs no edit of the ladder."""
    root = importlib.import_module(package)
    modules: list[ModuleType] = [
        importlib.import_module(f"{package}.{m.name}")
        for m in sorted(pkgutil.iter_modules(root.__path__), key=lambda m: m.name)
        if m.name.startswith("rung_")
    ]
    declared = [(m, getattr(m, "RUNG", None)) for m in modules]
    for m, one in declared:
        if one is not None and not isinstance(one, Rung):
            raise TypeError(f"{m.__name__}.RUNG is not a rung.Rung: {one!r}")
    rungs = tuple(one for _, one in declared if one is not None)
    names = [one.name for one in rungs]
    if len(set(names)) != len(names):
        raise ValueError(f"two rung modules declare the same rung name: {sorted(names)}")
    return rungs, tuple(m.__name__ for m, one in declared if one is None)
