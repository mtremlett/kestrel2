"""rung - THE LADDER'S FIRST RUNG: does a strategy earn on a line after the broker's costs, by
more than chance would give?

A cell's trades (`lab/cell.py`) are priced as the desk trades: the rule decides after a day's
close and the order fills at the next day's open, sized by the desk's own sizer from the one
capital number, the line alone in the book. A buy costs what the desk's one cost model says
(`orders.cost`); a sale is charged what a buy of the same shares at the same price is charged
beyond its value. A trade is judged only once both its fills fall on bars the rule was shown:
one still held, or sold on the window's last day, is not.

The rung passes a strategy when it made at least MIN_TRADES judged trades and the mean of
their returns after costs is at least T_PASS standard errors above nothing. Every verdict
names the broker whose schedule priced it.

FAILING FAIRLY (LAD-06, STR-12). A strategy is failed only by a test that could have passed
it. Under MIN_TRADES judged trades there is not enough evidence: the answer is THIN, whatever
the trades made or lost, and never a fail. No judged trade at all is a FAULT in the test (a
window too short, the wrong bars, a rule that cannot fire there): it says nothing of the
rule. And no verdict is given by code that is not the published rule (`lab/published.py`).
The trades counted are the effective ones: each judged whole, and each a bet of its own,
since a rule holds one position on a line at a time. Trades pooled across lines, where two
held together are one bet, are counted here when pooling is built.
"""

from __future__ import annotations

import enum
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal, localcontext

from desk import orders
from desk.broker import Pretend
from desk.lines import LINES
from desk.orders import Order, Settings
from desk.store import Bar
from desk.strategy import ARITHMETIC, Action, Decision
from lab import cell, published
from lab.cell import Cell, Key, Record, Trade

#: His A-GATE (AG-01) asks for years of history; thirty trades is the fewest whose mean
#: return a t-statistic can fairly judge, and two standard errors is the textbook bar.
MIN_TRADES = 30
T_PASS = Decimal(2)


class Answer(enum.IntEnum):
    """A rung's answer on a trial, and the ladder's. Where several are read together (the
    folds of a history, the named rungs on one trial) the least is the one given: a fault
    in the test before anything it seemed to show, and a fail on enough trades before what
    too few could not settle."""

    FAULT = 0  #: no trades at all: the test is at fault, and says nothing of the rule
    FAIL = 1  #: enough trades, and it did not earn
    THIN = 2  #: not enough evidence: too few trades to pass it, or to fail it
    DOUBT = 3  #: neither a win nor a loss: not promoted, and not thrown away
    PASS = 4


@dataclass(frozen=True)
class Priced:
    trade: Trade
    shares: int
    paid: Decimal  #: pounds out at the buy, its commission and conversion in
    received: Decimal  #: pounds back at the sale, after its commission and conversion
    gross: Decimal  #: pounds the two prices alone made, before any cost

    @property
    def costs(self) -> Decimal:
        return self.gross - (self.received - self.paid)

    @property
    def gain(self) -> Decimal:
        """The return after every cost, on the pounds paid."""
        return (self.received - self.paid) / self.paid


@dataclass(frozen=True)
class Verdict:
    key: Key
    broker: str  #: whose schedule priced it
    trades: tuple[Priced, ...]
    t: Decimal | None  #: the mean gain in standard errors; None under two trades
    answer: Answer  #: PASS, FAIL, THIN or FAULT: the first rung never answers DOUBT

    @property
    def passed(self) -> bool:
        return self.answer is Answer.PASS


def judge(record: Record, bars: Sequence[Bar], settings: Settings, fx: Decimal) -> Verdict:
    """The verdict on the record's trades, priced on the bars that made it; fx is pounds per
    unit of the line's currency, one rate for the window."""
    published.proven(record.key.cell.strategy)
    if cell.key(record.key.cell, bars) != record.key:
        raise ValueError(f"{record.key.cell}: these bars or this code did not make the record")
    read = cell.shown(record.key.cell, bars)
    at = {bar.day: n for n, bar in enumerate(read)}
    done = [t for t in record.trades if t.sold is not None and at[t.sold] + 1 < len(read)]
    with localcontext(ARITHMETIC):
        return verdict(
            record.key,
            tuple(_price(record.key.cell, trade, read, at, settings, fx) for trade in done),
        )


def verdict(key: Key, priced: tuple[Priced, ...]) -> Verdict:
    """The first rung's one rule, on trades already priced."""
    with localcontext(ARITHMETIC):
        t = standard_errors([p.gain for p in priced])
    if t is None or len(priced) < MIN_TRADES:
        answer = Answer.THIN if priced else Answer.FAULT
    else:
        answer = Answer.PASS if t >= T_PASS else Answer.FAIL
    return Verdict(key, orders.BROKER, priced, t, answer)


def _price(
    c: Cell,
    trade: Trade,
    read: Sequence[Bar],
    at: Mapping[date, int],
    settings: Settings,
    fx: Decimal,
) -> Priced:
    """Sized at the close it was decided on, bought at the next open through the desk's own
    pretend broker, where its stop rests; sold by the stop, or at the open after the sell."""
    if trade.sold is None:
        raise ValueError(f"{c.symbol}, bought {trade.bought}: still held, so it has no price")
    line = next(line for line in LINES if line.symbol == c.symbol)
    decided, out = at[trade.bought], at[trade.sold] + 1
    decision = Decision(c.strategy, c.symbol, trade.bought, Action.BUY)
    order = orders.size(decision, line, read[decided].close, fx, settings, {})
    held = read[decided + 1 : out]
    broker = Pretend({line: held}, {})
    broker.open(held[0].day)
    broker.place(order)
    for bar in held[1:]:
        broker.open(bar.day)
    (bought, *stopped) = broker.fills()
    sold = stopped[0].price if stopped else read[out].open
    value = order.quantity * sold * fx
    gross = order.quantity * (sold - bought.price) * fx
    paid, charged = _charged(order, bought.price), _charged(order, sold)
    return Priced(trade, order.quantity, paid, 2 * value - charged, gross)


def _charged(order: Order, price: Decimal) -> Decimal:
    """What the desk's one cost model charges for the order's shares at this price; a sale is
    charged what a buy of the same shares is charged beyond its value. An order cannot exist
    without its stop below its price, so the stop moves with the price; it sets no fee."""
    return orders.cost(replace(order, price=price, stop=price * order.stop / order.price))


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
