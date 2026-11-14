"""promotion - BEFORE PAPER, AND AFTER IT: a strategy goes onto paper only with the ladder's
pass and a kill condition written first, and comes off it promoted only on thirty effective
paper trades, net positive (STR-17, LAD-11).

BEFORE PAPER. A candidate is a strategy of the desk's with the ladder's own line for it
(`lab/ladder.py`), never a bare word: every rung the one verdict rule names (`lab/deflated.py`)
answered on it, the rule read again over those answers a pass, and the line saying the same;
and with its kill condition: the numbers, written down before
its first paper trade, at which it is stopped. Written first, because a limit chosen while
the losses are being watched is always a little further off. A candidate without the pass or
without the condition cannot be made at all. The condition is two measured things, either
one enough: its paper profit after every cost fallen so many pounds beneath its highest
point (nothing made, until it has been ahead), or so many trades lost in a row. A fall deeper
than the A-GATE's own (AG-05) is no condition, and is refused.

ON PAPER. The facts are the desk's own ledger's: its fills (`book.fills`) and the round
trips made of them (`book.round_trips`), in pounds after every cost of both legs; nothing is
priced here. An order filled in parts is one trade, its round trips put together, and it is
a trade only once every share it bought is sold: until then the money its sales made is
counted, and it is no trade. Another strategy's fills are not read. A buy on or before the
day the condition was written is refused loudly, held or sold: the condition would be
judging what it was written after. Refused too: round trips the fills do not hold, and an
order that bought again after a day it sold on, which is two trades under one name. The
standing is read at a day's end, after the day's record, never part-way through its sales.

EFFECTIVE TRADES. Trades held together are one bet made several times: five lines bought
on one morning rise and fall with the one market. So the trades counted are the most that
can be chosen with no two held on the same day, a day one is sold and another bought
counted as shared. It errs low, on purpose: thirty bets that looked like more is the old
desk's mistake.

THE STANDING, in the ladder's own words (`rung.Answer`). FAIL: killed by its own condition, and
nothing after revives it. THIN: not killed, and under thirty effective trades, whatever they
made: not enough evidence, never a fail, and none yet is not a fault. DOUBT: thirty or more and
not a penny ahead after costs, by the one rounding policy: kept on paper, not promoted. PASS:
thirty or more, net positive, never killed. The fall is read on the money, at the end of each
day a sale was made on, the day's sales together, a part sale's with the rest. The row of losers
is read on whole trades in the order the ledger sold their last shares, a trade that made
nothing ending the row. Both read only what cannot change afterwards, so a later sale never
unmakes a kill. Only sales are read: what a held share has lost is the stop's to bound, and is
seen here when it sells.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

from desk.book import RoundTrip
from desk.broker import Fill
from desk.orders import pennies, strategy_of
from desk.strategy import STRATEGIES
from lab.deflated import NAMED, rule
from lab.rung import MIN_TRADES, Answer

#: The A-GATE's own fall (AG-05, pounds): no candidate's kill condition may sit beneath it.
DEEPEST = Decimal(1500)


@dataclass(frozen=True)
class Kill:
    """A kill condition: either part met, and the strategy is stopped."""

    fall: Decimal  #: pounds beneath its highest paper profit, after every cost
    losers: int  #: trades lost, one after another

    def __post_init__(self) -> None:
        if not (self.fall.is_finite() and 0 < self.fall <= DEEPEST):
            raise ValueError(f"a fall of {self.fall} pounds: one above nothing, to {DEEPEST}")
        if self.losers < 1:
            raise ValueError(f"{self.losers} losing trades in a row is no condition")


@dataclass(frozen=True)
class Candidate:
    """A strategy allowed onto paper: the ladder's line passing it, and its kill condition first."""

    ladder: Mapping[str, Any]  #: the ladder's line for the strategy on one of the desk's lines
    declared: date  #: the day its kill condition was written; its paper trades come after
    kill: Kill

    @property
    def strategy(self) -> str:
        return str((self.ladder.get("cell") or [""])[0])

    def __post_init__(self) -> None:
        if self.strategy not in STRATEGIES:
            raise ValueError(f"{self.strategy}: no strategy of the desk's to put on paper")
        rungs, said = self.ladder.get("rungs", {}), self.ladder.get("answer")
        if not set(NAMED) <= set(rungs):
            raise ValueError(f"{self.strategy} has not passed the ladder: no {NAMED} in {rungs}")
        verdict = rule({name: Answer[rungs[name][0]] for name in NAMED})
        if verdict is not Answer.PASS or said != verdict.name:
            raise ValueError(
                f"{self.strategy} has not passed the ladder: its rungs give {verdict.name}, "
                f"its line says {said}"
            )


@dataclass(frozen=True)
class Trade:
    order: str  #: the id of the order that bought it
    bought: date
    sold: date  #: the day its last share was sold
    profit: Decimal  #: pounds, after every cost


@dataclass(frozen=True)
class Standing:
    candidate: Candidate
    trades: int  #: its paper trades wholly sold, an order filled in parts once
    effective: int  #: the most of them no two of which were held on one day
    profit: Decimal  #: pounds, after every cost, of every sale so far
    killed: str | None  #: the day its kill condition was met, and which part; None if never
    answer: Answer


def standing(candidate: Candidate, fills: Iterable[Fill], trips: Iterable[RoundTrip]) -> Standing:
    """Where a candidate stands on its paper trades so far, from the desk's own ledger: its
    fills, and the round trips made of them."""
    bought = _bought(candidate, fills)
    mine = [t for t in trips if strategy_of(t.buy.order_id) == candidate.strategy]
    trades = _trades(bought, mine)
    profit, killed = (
        sum((t.profit for t in mine), Decimal(0)),
        _killed(candidate.kill, mine, trades),
    )
    bets = effective(trades)
    if killed is not None:
        answer = Answer.FAIL
    elif bets < MIN_TRADES:
        answer = Answer.THIN
    else:
        answer = Answer.PASS if pennies(profit) > 0 else Answer.DOUBT
    return Standing(candidate, len(trades), bets, profit, killed, answer)


def effective(trades: Sequence[Trade]) -> int:
    """The most trades that can be chosen with no two held on the same day."""
    count, last = 0, date.min
    for trade in sorted(trades, key=lambda t: t.sold):
        if trade.bought > last:
            count, last = count + 1, trade.sold
    return count


def _bought(candidate: Candidate, fills: Iterable[Fill]) -> dict[str, tuple[int, date]]:
    """The shares each of the candidate's orders bought and the last day it bought on, every
    one after the declaration."""
    bought: dict[str, tuple[int, date]] = {}
    for fill in fills:
        if fill.quantity < 0 or strategy_of(fill.order_id) != candidate.strategy:
            continue
        if fill.day <= candidate.declared:
            raise ValueError(
                f"{fill.order_id}: bought on {fill.day}, not after its kill condition was "
                f"written ({candidate.declared}): a condition judges only what follows it"
            )
        shares, last = bought.get(fill.order_id, (0, fill.day))
        bought[fill.order_id] = shares + fill.quantity, max(last, fill.day)
    return bought


def _trades(
    bought: Mapping[str, tuple[int, date]], trips: Sequence[RoundTrip]
) -> tuple[Trade, ...]:
    """The orders wholly sold, each one's round trips put together, in the order the ledger
    sold their last shares."""
    sold: dict[str, int] = {}
    whole: dict[str, Trade] = {}
    for trip in trips:
        order = trip.buy.order_id
        sold[order] = sold.get(order, 0) + trip.buy.quantity
        shares, last = bought.get(order, (0, date.min))
        if sold[order] > shares:
            raise ValueError(f"{order}: more shares sold than the fills given bought")
        if trip.sell.day < last:
            raise ValueError(f"{order}: bought again on {last}, after a sale on {trip.sell.day}")
        part = whole.pop(order, Trade(order, trip.buy.day, trip.sell.day, Decimal(0)))
        whole[order] = Trade(
            order,
            min(part.bought, trip.buy.day),
            max(part.sold, trip.sell.day),
            part.profit + trip.profit,
        )
    done = (trade for order, trade in whole.items() if sold[order] == bought[order][0])
    return tuple(sorted(done, key=lambda t: t.sold))


def _killed(kill: Kill, trips: Sequence[RoundTrip], trades: Sequence[Trade]) -> str | None:
    """The first day the condition was met, and which part of it; None if it never was."""
    met: list[tuple[date, str]] = []
    days: dict[date, Decimal] = {}
    for trip in trips:
        days[trip.sell.day] = days.get(trip.sell.day, Decimal(0)) + trip.profit
    made = highest = Decimal(0)
    for day in sorted(days):
        made += days[day]
        if highest - made >= kill.fall:
            met.append(
                (day, f"by {day} it had fallen {pennies(highest - made)} from its highest point")
            )
            break
        highest = max(highest, made)
    row = 0
    for trade in trades:
        row = row + 1 if trade.profit < 0 else 0
        if row >= kill.losers:
            met.append((trade.sold, f"by {trade.sold} it had lost {row} trades in a row"))
            break
    return min(met)[1] if met else None
