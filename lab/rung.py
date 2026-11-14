"""rung - THE LADDER'S FIRST RUNG: does a strategy earn on a line after the broker's costs, by
more than chance would give?

A cell's trades (`lab/cell.py`) are priced as the desk trades: the rule decides after a day's
close and the order fills at the next day's open, sized by the desk's own sizer from the one
capital number, the line alone in the book. A trade is judged only once both its fills fall
on bars the rule was shown: one still held, or sold on the window's last day, is not.

ITS COSTS WHOLE. Each leg is charged by the desk's one cost model (`orders.charges`), as the
desk's own book charges a round trip: the broker's commission, a sale's own fees, half the
spread and the slippage on both legs (a stop's sale slips further), the conversion on a line
not in pounds and the UK tax on a purchase. No cost is worked out here. Each fill is turned
into pounds at its own day's rate of exchange, the order sized at the rate of the morning it
is sent on, as the desk's day sizes it, so a dollar line's verdict carries the currency's gain
or loss with the trade's own. A pound is a pound: a pound line reads no rate. A day whose
rate is needed and is not given, or is not a number above nothing, is refused loudly, never
filled in from another day. A sale whose morning opens at or under the resting stop is the
stop's sale, as it is at the broker, and slips as one.

The rung passes a strategy when it made at least MIN_TRADES judged trades and the mean of
their returns after costs is at least T_PASS standard errors above nothing. Every verdict
names the broker whose schedule priced it.

FAILING FAIRLY (LAD-06, STR-12). A strategy is failed only by a test that could have passed
it. Under MIN_TRADES judged trades there is not enough evidence: the answer is THIN, whatever
the trades made or lost, and never a fail. No judged trade at all is a FAULT in the test (a
window too short, the wrong bars, a rule that cannot fire there): it says nothing of the
rule. And `judge` gives no verdict on code that is not the published rule
(`lab/published.py`). Gains with no spread at all are still refused loudly, few or many.
THE AUTHOR'S RESULT FIRST. A rule with an author's figure on file (`lab/reproduce.py`) is given
no verdict until each figure's reproduction is handed over, made by the code as it now is and
the same as the author's; the verdict carries them. With none on file it carries none.
The trades counted are the effective ones: each judged whole, and each a bet of its own,
since a rule holds one position on a line at a time. Trades pooled across lines, where two
held together are one bet, are counted here when pooling is built.
"""

from __future__ import annotations

import enum
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, localcontext

from desk import orders
from desk.broker import Pretend
from desk.lines import Line
from desk.orders import Charges, Leg, Settings
from desk.store import Bar
from desk.strategy import ARITHMETIC, Action, Decision
from lab import cell, published, reproduce
from lab.cell import Cell, Key, Record, Trade
from lab.reproduce import Reproduction

#: His A-GATE (AG-01) asks for years of history; thirty trades is the fewest whose mean
#: return a t-statistic can fairly judge, and two standard errors is the textbook bar.
MIN_TRADES = 30
T_PASS = Decimal(2)
#: Pounds per unit of a line's currency at each day: the day's rate, for the days it trades.
Rates = Mapping[date, Decimal]


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
    paid: Decimal  #: pounds the shares' value took at the buy's fill, at that day's rate
    received: Decimal  #: pounds their value brought at the sale's fill, at its own day's rate
    costs: Charges  #: every cost of both legs, line by line, from the desk's one cost model
    held: tuple[date, date]  #: the day its buy filled, and the day its sale did

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
    reproduced: tuple[Reproduction, ...]  #: the author's own results behind it, if on file

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
    """The verdict on the record's trades, priced on the bars that made it, each fill at its
    own day's rate of exchange; none before the reproductions its rule waits for."""
    published.proven(record.key.cell.strategy)
    reproduce.settled(record.key.cell.strategy, reproduced)  #: before anything is priced
    if cell.key(record.key.cell, bars) != record.key:
        raise ValueError(f"{record.key.cell}: these bars or this code did not make the record")
    read = cell.shown(record.key.cell, bars)
    at = {bar.day: n for n, bar in enumerate(read)}
    done = [t for t in record.trades if t.sold is not None and at[t.sold] + 1 < len(read)]
    with localcontext(ARITHMETIC):
        return verdict(
            record.key,
            tuple(_price(record.key.cell, trade, read, at, settings, rates) for trade in done),
            reproduced,
        )


def verdict(
    key: Key, priced: tuple[Priced, ...], reproduced: Sequence[Reproduction] = ()
) -> Verdict:
    """The first rung's one rule, on trades already priced, once the rule's author's own
    result is reproduced."""
    behind = reproduce.settled(key.cell.strategy, reproduced)
    with localcontext(ARITHMETIC):
        t = standard_errors([p.gain for p in priced])
    if t is None or len(priced) < MIN_TRADES:
        answer = Answer.THIN if priced else Answer.FAULT
    else:
        answer = Answer.PASS if t >= T_PASS else Answer.FAIL
    return Verdict(key, orders.BROKER, priced, t, answer, behind)


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
        raise ValueError(f"{c.symbol}, bought {trade.bought}: still held, so it has no price")
    line, decided, out = c.line, at[trade.bought], at[trade.sold] + 1
    decision = Decision(c.strategy, c.symbol, trade.bought, Action.BUY)
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
    return Priced(trade, order.quantity, paid, received, buying + selling, (bought.day, sale[2]))


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
