"""book, its invariants (TST-04, canon B4): in seeded worlds of random markets, orders, faults
and restarts, after every step the book is its fills and each order's answer has only moved
forward, and at every day's end the money adds up. The money is set against the test's own
sums over the broker's fills, each fill costed by the one cost model: they prove every cost
is counted once and where it belongs, not that the model is right (test_orders does)."""

from __future__ import annotations

import random
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import replace
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from desk import book, day, venues
from desk.broker import Crash, Fault, Fill, Pretend, Report
from desk.lines import STAMP_DUTY, YARDSTICK, Line
from desk.orders import Charges, Order, Refused, Sale, Settings, charges, leg_of, pennies
from desk.store import Bar

#: A taxed London share, a line of three times its market, a dollar line, and the yardstick.
SHARE, TRIPLE = Line("A", "LSE", "GBP", 1, STAMP_DUTY), Line("T", "LSE", "GBP", 3)
LINES = (SHARE, TRIPLE, Line("U", "US", "USD", 1), YARDSTICK)
#: Twelve sessions of both venues, after the eve the first day's record measures the market from.
EVE, *DAYS = venues.sessions("LSE", date(2025, 11, 7), date(2025, 11, 25))
CAPITAL, CENT, NONE = Settings(Decimal(10_000)), Decimal("0.01"), Charges(*(Decimal(0),) * 5)
TINY = Decimal("1e-15")  #: pounds: a cost shared between round trips is divided by its shares


def _market(rng: random.Random) -> dict[Line, tuple[Bar, ...]]:
    """Each line's days: each opens within 7% of the last close and falls up to a tenth. On
    about one session in six a line does not trade, a suspension recorded on it; the
    yardstick trades on them all."""
    market = {}
    for line in LINES:
        bars, last = [], Decimal(rng.randrange(20, 80))
        for on in (EVE, *DAYS):
            start = (last * rng.randrange(93, 108) / 100).quantize(CENT)
            low = (start * rng.randrange(90, 101) / 100).quantize(CENT)
            last = rng.choice((low, start))
            if line == YARDSTICK or rng.random() > 0.15:
                bars.append(Bar(on, start, start + 1, low, last, 1))
        shut = frozenset({EVE, *DAYS} - {bar.day for bar in bars})
        market[replace(line, suspended=shut)] = tuple(bars)
    return market


class World:
    """One seed's desk: its market, its broker with a fault waiting for most lines' first
    order, the orders it has made, and its accounts carried from day to day."""

    def __init__(self, seed: int, root: Path) -> None:
        self.rng, self.root = random.Random(seed), root  # noqa: S311 - a repeatable draw
        self.market = _market(self.rng)
        self.lines = {line.symbol: line for line in self.market}
        faults = {s: f for s in self.lines if (f := self.rng.choice((None, None, *Fault)))}
        self.broker = Pretend(self.market, faults)
        self.bars = {(line.symbol, b.day): b for line, bars in self.market.items() for b in bars}
        self.orders, self.seen = list[Order | Sale](), dict[str, Report]()
        self.rates, self.closes = dict[date, dict[str, Decimal]](), dict[str, Decimal]()
        self.last, self.counted, self.costs = date.min, 0, NONE
        self.cash = self.worth = Decimal(0)

    def dawn(self, on: date) -> None:
        self.broker.open(on)
        self.rates[on] = {"GBP": Decimal(1), "USD": Decimal(self.rng.randrange(70, 86)) / 100}
        book.record_rates(self.root, on, self.rates[on])
        self.closes.update({s: self.bars[s, on].close for s in self.lines if (s, on) in self.bars})
        self.states()

    def step(self, on: date) -> None:
        """One thing the desk does: send an order again as a desk restarted would, the newer
        the likelier; sell some of a line, or more than it holds; or buy."""
        rng = self.rng
        line, roll = rng.choice(tuple(self.lines.values())), rng.random()
        held = dict(self.broker.holdings()).get(line.symbol, 0)
        if roll < 0.3 and self.orders:
            self.send(rng.choice(self.orders[-rng.randint(1, len(self.orders)) :]))
        elif roll < 0.6 and held:
            self.send(Sale(f"s-{len(self.orders)}", line, rng.randint(1, held + 1 + held // 4)))
        else:
            price = self.bars[line.symbol, on].open if (line.symbol, on) in self.bars else CENT
            stop, fx = price * rng.randrange(75, 96) / 100, self.rates[on][line.currency]
            self.send(Order(f"o-{len(self.orders)}", line, rng.randint(1, 40), price, fx, stop))
        self.states()
        self.positions()

    def send(self, order: Order | Sale) -> None:
        """SENDING IS IDEMPOTENT: an order the broker has is never judged or sent again, and
        nothing more is filled (states: nor is any order received twice). The answer is the
        broker's own, or for an order lost on the way none filled and why; and the broker's
        fills are in the ledger."""
        broker = self.broker
        before, made = broker.report(order.order_id), broker.fills()
        if order not in self.orders:
            self.orders.append(order)
        try:
            sent = book.send(self.root, broker, order, CAPITAL)
        except (Refused, Crash):
            assert before is None, f"{order.order_id}: the broker had it, and it was judged again"
            return
        now = broker.report(order.order_id)  #: None: the connection dropped, so never received
        if before is not None:
            assert (now, broker.fills()) == (before, made), f"{order.order_id}: sent again"
        filled = sum(abs(fill.quantity) for fill in now.fills) if now else 0
        assert (sent.order_id, sent.filled) == (order.order_id, filled), f"{sent}: not {now}"
        assert (sent.reason == now.reason) if now else sent.reason, f"{sent}: not {now}'s reason"
        assert book.fills(self.root) == broker.fills(), f"{order.order_id}: a fill unwritten"

    def states(self) -> None:
        """ORDERS MOVE ONLY THROUGH VALID STATES: never received, then received once, working
        (the broker's reason says so, in that word) or final. A final answer never changes
        and a received order is never forgotten; its answer holds every fill made under its
        id, on its own line and for no more than its shares, and its reason is None only
        when it filled whole."""
        made, received = self.broker.fills(), self.broker.submitted()
        assert len(set(received)) == len(received), f"an order received twice: {received}"
        for order in self.orders:
            was, now = self.seen.get(order.order_id), self.broker.report(order.order_id)
            mine = tuple(fill for fill in made if fill.order_id == order.order_id)
            if now is None:
                assert was is None and not mine, f"{order.order_id}: received, then forgotten"
                continue
            assert was in (None, now) or "working" in str(was and was.reason), f"{was} became {now}"
            filled = sum(f.quantity for f in mine) * (1 if isinstance(order, Order) else -1)
            assert now.fills == mine and {f.symbol for f in mine} <= {order.line.symbol}, f"{now}"
            assert 0 <= filled <= order.quantity, f"{order.order_id}: {filled} shares filled"
            assert (now.reason is None) == (filled == order.quantity), f"{now}"
            self.seen[order.order_id] = now

    def positions(self) -> None:
        """POSITIONS EQUAL THE SUM OF FILLS: the ledger is the broker's fills, none lost,
        changed or written twice; and the book, the broker's holdings and the stops resting
        there are each what the fills add up to."""
        made, total = self.broker.fills(), Counter[str]()
        assert book.reconcile(self.root, self.broker) == (), "the book is not the broker's"
        assert book.fills(self.root) == made, "the ledger is not the broker's fills"
        for fill in made:
            total[fill.symbol] += fill.quantity
        held = {symbol: shares for symbol, shares in sorted(total.items()) if shares}
        assert book.positions(self.root) == held == dict(self.broker.holdings())
        assert held == dict(self.broker.stops()), "shares held with no stop resting for them all"

    def pounds(self, fill: Fill, shares: int) -> tuple[Decimal, Charges]:
        """Some of a fill's shares in pounds at its own day's rate, with their share of its
        costs from the one cost model."""
        line, whole = self.lines[fill.symbol], abs(fill.quantity)
        fx = self.rates[fill.day][line.currency]
        cost = charges(line, leg_of(fill.order_id, fill.quantity), whole, fill.price, fx)
        return fill.price * shares * fx, cost.part(shares, whole)

    def dealt(self, fills: Iterable[Fill]) -> tuple[Decimal, Charges]:
        """The pounds the fills moved, in for a sale and out for a buy, and their costs."""
        priced = [(fill.quantity, *self.pounds(fill, abs(fill.quantity))) for fill in fills]
        money = Decimal(sum(-value if shares > 0 else value for shares, value, _ in priced))
        return money, sum((cost for _, _, cost in priced), NONE)

    def dusk(self, on: date) -> None:
        """First the day's dealing as the ledger stands before the record: on a day the desk
        did nothing, its stops' sales are not in it yet and are counted the next day. EVERY
        FILL'S MONEY AND COSTS ARE COUNTED ONCE over the days. Then what makes PROFIT
        REALISED PLUS UNREALISED LESS COSTS, with the worth the day's record holds: the money
        the fills moved is the round trips' gross less what the shares still held were
        bought for, and every cost is in a round trip or was paid to buy shares still held.
        Then the record; and on half the nights every working order is cancelled."""
        ledger, held, lines = book.fills(self.root), book.positions(self.root), self.lines.values()
        cash, costs = book.dealt(self.root, lines, on, self.last, self.counted)
        self.cash, self.costs = self.cash + cash, self.costs + costs
        self.last, self.counted = on, len(ledger)
        money, paid = self.dealt(ledger)
        assert (self.cash, self.costs) == (money, paid), "a fill counted twice, or in no day"
        trips, (basis, owed) = book.round_trips(self.root, lines), self.unsold(ledger, held)
        assert money == sum(t.gross for t in trips) - basis, "a sale closed the wrong buys"
        assert all(t.profit == t.gross - t.costs.total for t in trips), "a trip's profit"
        assert abs(paid.total - sum(t.costs.total for t in trips) - owed) < TINY, "a cost lost"
        self.record(on)
        if self.rng.random() < 0.5:
            self.broker.cancel()
        self.states()

    def unsold(self, ledger: Sequence[Fill], held: dict[str, int]) -> tuple[Decimal, Decimal]:
        """What the shares still held were bought for, and what buying them cost: sales
        close the oldest buys, so the newest bought are what is left."""
        value, costs, left = Decimal(0), Decimal(0), Counter(held)
        for fill in reversed(ledger):
            if fill.quantity > 0 and (shares := min(fill.quantity, left[fill.symbol])):
                left[fill.symbol] -= shares
                paid, cost = self.pounds(fill, shares)
                value, costs = value + paid, costs + cost.total
        return value, costs

    def record(self, on: date) -> None:
        """EQUITY IS CASH PLUS MARKET VALUE, day by day: the day's record (day.publish) is
        worth what the broker's holdings are at the day's closes and rates, and its profit
        is, to the penny, that less the day before's, plus the money the day's own fills
        moved, less their costs."""
        kept, fx = day.publish(self.root, self.market, self.broker, CAPITAL, on), self.rates[on]
        held = self.broker.holdings()
        worth = Decimal(sum(n * self.closes[s] * fx[self.lines[s].currency] for s, n in held))
        money, paid = self.dealt(fill for fill in self.broker.fills() if fill.day == on)
        assert (kept.worth, kept.costs) == (worth, paid.published()), f"{on}: {kept}"
        assert kept.profit == pennies(worth - self.worth + money - paid.total), f"{on}: {kept}"
        self.worth = worth


@pytest.mark.parametrize("seed", range(25))
def test_in_any_world_of_orders_faults_and_restarts_the_money_adds_up(
    seed: int, tmp_path: Path
) -> None:
    world = World(seed, tmp_path)
    for on in DAYS:
        world.dawn(on)
        for _ in range(world.rng.randrange(8)):
            world.step(on)
        world.dusk(on)
