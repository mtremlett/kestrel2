"""simcity - SIMCITY. ONE COMMAND lives the desk's day through a hundred seeded worlds of the saved
data at the pretend broker, and writes one record of the night. A WORLD is the saved lines on their
own days, months dealt again by the world's number, which also deals the faults and the mishaps a
real desk meets. THE CENSUS names each part of the money path with the scenarios that ran it. A part
none ran, or a promise broken, turns the night red."""

from __future__ import annotations

import csv
import random
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from contextlib import suppress
from dataclasses import replace
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType

from desk import book, broker, day, halt, kill, orders, strategy
from desk.broker import Crash, Fault, Pretend, Report
from desk.lines import YARDSTICK
from desk.orders import HOLDINGS, Order, Sale, Settings
from desk.simcity_census import Census
from desk.simcity_incidents import (
    CANCELLED,
    DEAF,
    HOLE,
    LEFT,
    STALE,
    UNHELD,
    beside,
    cancelled,
    deaf,
    hole,
    stale,
    unheld,
)
from desk.simcity_parts import MONTH, Archive, Night, _market
from desk.strategy import Action

Rates = Mapping[str, Decimal]  #: the pounds per unit of each currency, every day of the night

__all__ = ["MONTH", "Archive", "Night", "_market"]  #: what desk.simcity gives from simcity_parts

NIGHTS = "simcity.csv"
HEADER = (
    *("at", "verdict", "worlds", "days", "clean", *(fault.name.lower() for fault in Fault)),
    *("deaths", "withheld", "trips", "profit", "market", "idle", "bare", "broken"),
)
#: THE MONEY PATH: the modules an order travels through, from a rule's decision to the record.
PATH: tuple[ModuleType, ...] = (strategy, orders, broker, book, day, kill)
WORLDS = range(100)  #: a night's worlds, each named by the number that seeds its every draw
FAULTY = 4  #: of the orders at the broker's door, one in so many finds a fault waiting
EVENTFUL = 8  #: of the mornings a desk is fit for it, one in so many has something done to it
FORGOTTEN = 8  #: of the stops cancelled by hand, one in so many is never put back
RULES = "the rules alone, on all the data"
DAY = "a day of the desk"
RESTART = "the desk dies mid-send and is started again"
FAULTS = "the broker's faults"
BEHIND = "a position appears behind the desk's back"
UNSTOPPED = "a stop is cancelled by hand"
GAPPED = "every line opens at its low"
KILLED = "the kill switch is pulled, released and drilled"
RECKONING, TRIPS = "the night's reckoning", "the round trips are told"


class _Counted(Pretend):
    """One world's pretend broker: one in FAULTY orders finds a seeded fault waiting, counted."""

    def __init__(self, archive: Archive, rng: random.Random) -> None:
        super().__init__(archive, {})
        self._rng, self.met = rng, Counter[Fault | None]()
        self.buys = 0  #: the orders to buy that reached the door

    def place(self, order: Order | Sale) -> Report:
        self.buys += isinstance(order, Order)
        if self._rng.randrange(FAULTY) == 0:
            self._faults[order.line.symbol] = self._rng.choice(tuple(Fault))
        waiting = self._faults.get(order.line.symbol)
        try:
            return super().place(order)
        finally:  #: counted however the order ended, an error raised to the desk too
            self.met[None if order.line.symbol in self._faults else waiting] += 1

    def reopen(self, on: date, market: Archive) -> None:
        """The market's bars for the day as the world has made them again."""
        self._bars.update(
            {(x.symbol, b.day): b for x, bars in market.items() for b in bars if b.day == on}
        )

    def lose_stop(self, symbol: str) -> Callable[[], None]:
        """Cancel a resting stop by hand; what is given back puts it back as it was."""
        stop = self._stops[symbol]
        self.cancel_stop(symbol)
        return lambda: self.put_stop_back(symbol, stop.level)


class _Life:
    """One desk's life in one world: its market, its broker, and its promises kept or not."""

    def __init__(
        self, desk: Path, archive: Archive, room: Settings, rates: Rates, seed: int, census: Census
    ) -> None:
        self.desk, self.room, self.rates, self.seed, self.census = desk, room, rates, seed, census
        self.rng = random.Random(seed)  # noqa: S311 - a repeatable draw, not a secret
        self.market = _market(archive, self.rng)
        self.pretend = _Counted(self.market, self.rng)
        self.began = self.market[YARDSTICK][0].day if YARDSTICK in self.market else date.min
        self.left = {x.symbol for x, bars in self.market.items() if bars[0].day > self.began}
        self.records, self.deaths, self.trips = list[day.Record](), 0, 0
        self.kept, self.done, self.held = dict[str, bool](), set[str](), set[str]()
        self.stopped = ""  #: the day the desk said it could not go on, and its words

    def promise(self, words: str, kept: bool) -> None:
        self.kept[words] = kept and self.kept.get(words, True)

    def live(self, on: date) -> day.Record:
        """One day whole, from the data saved by its end, and its record."""
        saved = {
            x: [b for b in bars if b.day <= on]
            for x, bars in self.market.items()
            if bars[0].day < on
        }
        scenario, buys = self.census.scenario, self.pretend.buys
        record = self._run(saved, on)
        self.census.now(scenario)
        odd = set(record.mismatches) - book.adopted(self.desk, on)  #: strangers, sold, are none
        quiet = not (odd and self.pretend.buys > buys)
        self.promise("nothing is bought on a day the book is not the broker's", quiet)
        held, stopped = book.positions(self.desk), dict(self.pretend.stops())
        net = Counter[str]()  #: shares of a stranger's not sold: none of the desk's lines
        for f in book.fills(self.desk):
            net[f.symbol] += f.quantity * (orders.strategy_of(f.order_id) == "stranger")
        own = len(held.keys() - {s for s, n in net.items() if n > 0})
        self.promise(f"never more than {HOLDINGS} lines are held", own <= HOLDINGS)
        self.promise("no order is left working at a day's end", not self.pretend.working())
        bare = {*held} - {*stopped} - {*record.mismatches}
        self.promise("a line held with no stop at the broker is named that day", not bare)
        mine = dict(self.pretend.holdings())  #: a line whose shares are not the book's is not
        told = {b.reason.partition(":")[0] for b in halt.morning(self.desk, on)[halt.Blocker.BOOK]}
        untold = {s for s, n in held.items() if s not in stopped and mine.get(s) == n} - told
        self.promise("a line held with no stop is on that day's list, with its stop", not untold)
        named = odd and held == stopped == mine
        self.promise("no line is named on a day the book is the broker's", not named)
        self.records.append(record)
        return record

    def _run(self, saved: Archive, on: date) -> day.Record:
        try:
            return day.run(self.desk, saved, self.pretend, self.room, on, self.rates, True)
        except Crash:  #: the desk died mid-send: it is started again, and runs the same day
            self.deaths += 1
            self.census.now(RESTART)
            return self._run(saved, on)


def _behind(life: _Life, on: date) -> None:
    """Shares the desk did not buy are at the broker before the day: the seed's number of them,
    on a line the desk does not hold (a sale beside its own shares takes the pretend broker's
    stop down with it, desk/broker.py). The desk sells them, or names them."""
    free = {line.symbol for line in life.market} - set(book.positions(life.desk))
    symbol = life.rng.choice(sorted(free))
    life.pretend.inject(symbol, life.rng.randint(1, 50))
    record = life.live(on)
    mine = [
        f.quantity for f in book.fills(life.desk) if f.order_id == f"{on:%Y%m%d}-stranger-{symbol}"
    ]
    sold = bool(mine) and sum(mine) == 0
    life.promise(
        "a position the desk did not make is sold or named", sold or symbol in record.mismatches
    )


def _unstopped(life: _Life, on: date) -> None:
    """The stop under a holding of the seed's choosing is cancelled by hand, and put back after
    the day's record if the same shares are still held; one time in FORGOTTEN it never is."""
    held = life.rng.choice(life.pretend.stops())
    put_back = life.pretend.lose_stop(held[0])
    life.live(on)
    if life.rng.randrange(FORGOTTEN) and held in life.pretend.holdings():
        put_back()


def _gapped(life: _Life, on: date) -> None:
    """Every line opens at the day's low, a gap down from the close before it; the stop under
    each buy it fills is then moved under that fill, never left where the close put it."""
    life.market = {
        x: tuple(replace(b, open=b.low) if b.day == on else b for b in bars)
        for x, bars in life.market.items()
    }
    life.pretend.reopen(on, life.market)
    life.live(on)
    lines = {x.symbol: x for x in life.market}
    paid = {f.symbol: f.price for f in book.fills(life.desk) if f.quantity > 0 and f.day == on}
    due = {s: orders.stop_under(lines[s], p) for s, p in paid.items()}
    rests = {s: level for s, (_, level) in life.pretend.resting_stops().items()}
    fits = all(rests[s] == due[s] for s in rests & due.keys())
    life.promise("a stop rests where its fill puts it", fits)
    held = {f.symbol: f for f in book.fills(life.desk) if f.quantity > 0 and f.day == on}
    before = {x.symbol: [b.close for b in bars if b.day < on] for x, bars in life.market.items()}
    for s in sorted(s for s, closes in before.items() if not closes):
        life.promise(f"FAULT line {s}: no bar before the gap day, its gap is unrunnable", False)
    shut = {s: closes[-1] for s, closes in before.items() if closes}
    sold = [
        orders.Order(
            f"gap-{s}",
            lines[s],
            f.quantity,
            shut[s],
            life.rates[lines[s].currency],
            orders.stop_under(lines[s], shut[s]),
        )
        for s, f in held.items()
        if s in shut
    ]
    gone = [o.order_id for o in sold if orders.gapped(o, held[o.line.symbol].price, life.room)]
    life.promise("a gap down to the low leaves a stop's loss inside the gap limit", not gone)


def _killed(life: _Life, on: date) -> None:
    """The switch is pulled before the day and released after its record; then the drill."""
    at, reached = datetime.combine(on, time(7), UTC), life.pretend.submitted()
    said = kill.pull(life.desk, life.pretend, at, "SimCity pulls it for a day")
    life.live(on)
    quiet = life.pretend.submitted() == reached and "KILL SWITCH ON" in said.words()
    life.promise("with the kill switch on nothing reaches the broker, and the desk says so", quiet)
    kill.release(life.desk, at, "SimCity releases it")
    with suppress(kill.Failed):  #: a drill that failed is not on the record: said below
        kill.drill(life.desk, at)
    life.promise("the kill switch's drill is on the record", kill.drilled(life.desk, on))


Event = tuple[str, Callable[[_Life, date], object]]
EVENTS: tuple[Event, ...] = (
    (STALE, stale),
    (BEHIND, _behind),
    (UNSTOPPED, _unstopped),
    (GAPPED, _gapped),
    (KILLED, _killed),
    (HOLE, hole),
    (LEFT, beside),
    (CANCELLED, cancelled),
    (DEAF, deaf),
    (UNHELD, unheld),
)


def run(
    root: Path,
    archive: Archive,
    room: Settings,
    rates: Rates,
    at: datetime,
    worlds: Sequence[int] = WORLDS,
) -> Night:
    """THE ONE COMMAND. In each world a desk that holds nothing lives every session of the
    archive after the yardstick's first, on a book of its own thrown away; the night's one
    record is added to those kept under root, dated at, and given back. Red or green, it is
    kept. worlds are the numbers of the worlds to live: one alone is that world again. A world
    in which the desk refuses to go on ends there, and is a promise broken."""
    if at.utcoffset() != timedelta(0):
        raise ValueError(f"SimCity's night at {at}: not a time in UTC")
    path, rows = root / NIGHTS, [list(HEADER)]
    if path.exists():
        with path.open(newline="", encoding="utf-8") as kept:
            rows = list(csv.reader(kept))
        if rows[:1] != [list(HEADER)]:
            raise ValueError(f"{path}: not SimCity's nights")
    census, lives, seed = Census(PATH), list[_Life](), None
    try:
        census.now(RULES)
        alone = strategy.decide({line.symbol: bars for line, bars in archive.items()})
        for seed in worlds:
            census.now(None)  #: the making of a world is SimCity's own work, and no scenario's
            with TemporaryDirectory() as scratch:
                lives.append(_Life(Path(scratch), archive, room, rates, seed, census))
                try:
                    _live(lives[-1])
                except ValueError as refusal:  #: the desk's own word that it cannot go on
                    lives[-1].stopped = f"on day {len(lives[-1].records) + 1}, saying: {refusal}"
    except Exception as died:
        died.add_note(f"SimCity's night died with world {seed} being lived (None: none yet)")
        raise
    finally:
        census.now(None)
    night = _night(at, lives, census, alone)
    said = ("; ".join(names) for names in (night.idle, night.bare, night.broken))
    money = (night.deaths, night.withheld, night.trips, night.profit, night.market)
    verdict = "GREEN" if night.green else "RED"
    row = (at.isoformat(), verdict, night.worlds, night.days, *night.met.values(), *money, *said)
    book._write(path, [*rows, row])
    return night


def _live(life: _Life) -> None:
    """The life, day by day, and its reckoning. On one in EVENTFUL of the mornings it holds a line
    under its stop after a plain record, a thing is done to it, each in the seed's order."""
    census, pretend, todo = life.census, life.pretend, list[Event]()
    for on in sorted({b.day for bs in life.market.values() for b in bs if b.day > life.began}):
        census.now(DAY)
        pretend.open(on)
        fit = life.records and not life.records[-1].mismatches and pretend.stops()
        if fit and life.rng.randrange(EVENTFUL) == 0:
            todo = todo or life.rng.sample(EVENTS, len(EVENTS))
            scenario, happen = todo.pop()
            census.now(scenario)
            happen(life, on)
            life.done.add(scenario)
        else:
            life.live(on)
    census.now(RECKONING)
    records, fills, reached = life.records, book.fills(life.desk), pretend.submitted()
    plain = [record for record in records if record.profit is not None]
    last, worth = (plain[-1].day, plain[-1].worth) if plain else (date.min, Decimal(0))
    cash, costs = book.dealt(life.desk, life.market, last, date.min, 0)
    profit = sum((record.profit or 0 for record in plain), Decimal(0))
    near = abs(profit - (worth + cash - costs.total)) <= len(plain) * Decimal("0.005")
    life.promise("the days' profits add up to the ledger's", near)
    theirs = tuple(f for f in fills if not f.execution_id.startswith("stranger-"))
    life.promise("the ledger is the broker's own fills", theirs == pretend.fills())
    life.promise("no order reached the broker twice", len(set(reached)) == len(reached))
    bars = {(line.symbol, bar.day): bar for line, days in life.market.items() for bar in days}
    ranged = (bars[f.symbol, f.day].low <= f.price <= bars[f.symbol, f.day].high for f in theirs)
    life.promise("every fill is inside its day's range in its world", all(ranged))
    census.now(TRIPS)
    trips = book.round_trips(life.desk, life.market)
    shut = sum(-t.sell.quantity for t in trips) == sum(-f.quantity for f in fills if f.quantity < 0)
    life.promise("the round trips close every share the fills sold", shut)
    life.trips = len(trips)
    cash, costs = book.dealt(life.desk, life.market, date.max, date.min, 0)
    kind = book.conformance_cost(life.desk, life.market)
    life.promise("the conformance cost is cash less costs", kind == cash - costs.total)
    life.held = {orders.strategy_of(fill.order_id) for fill in fills if fill.quantity > 0}


def _night(
    at: datetime, lives: Sequence[_Life], census: Census, alone: Sequence[strategy.Decision]
) -> Night:
    """What the worlds came to: a promise broken is named once, with its worlds."""
    records = [record for life in lives for record in life.records]
    plain = [record for record in records if record.profit is not None]
    met = {fault: sum(life.pretend.met[fault] for life in lives) for fault in (None, *Fault)}
    ran = {part: tuple(sorted(scenarios)) for part, scenarios in census.ran.items()}
    ran |= {f"broker.Fault.{f.name}": (FAULTS,) if met[f] else () for f in Fault}
    broke: dict[str, list[int]] = {}
    for life in lives:
        for words in (words for words, kept in life.kept.items() if not kept):
            broke.setdefault(words, []).append(life.seed)
    broken = [f"{words} (in {len(w)} worlds, the first world {w[0]})" for words, w in broke.items()]
    if halt := [f"world {life.seed} {life.stopped}" for life in lives if life.stopped]:
        broken.append(f"the desk stops on no day (in {len(halt)} worlds, the first {halt[0]})")
    asked = {(decision.strategy, decision.action) for decision in alone}
    if not {(r, to) for r in strategy.STRATEGIES for to in (Action.BUY, Action.SELL)} <= asked:
        broken.append("every rule asks to buy and to sell somewhere in the saved data")
    done = set().union(*(life.done for life in lives))
    broken += [f"never happened: {scenario}" for scenario, _ in EVENTS if scenario not in done]
    idle = tuple(r for r in strategy.STRATEGIES if not any(r in life.held for life in lives))
    profit = sum((record.profit or Decimal(0) for record in plain), Decimal(0))
    market = sum((record.market for record in plain), Decimal(0))
    money = (len(records) - len(plain), sum(life.trips for life in lives), profit, market)
    left = tuple(sorted({symbol for life in lives for symbol in life.left}))
    deaths = sum(life.deaths for life in lives)
    return Night(at, len(lives), len(records), met, deaths, *money, idle, ran, tuple(broken), left)


if __name__ == "__main__":
    from desk import simcitycmd

    raise SystemExit(simcitycmd.main())
