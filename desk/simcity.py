"""simcity - SIMCITY. ONE COMMAND lives the desk's day through a hundred seeded worlds of the saved
data at the pretend broker, and writes one record of the night. A WORLD is the saved lines on their
own days, months dealt again by the world's number, which also deals the faults and mishaps a real
desk meets. THE CENSUS names each part of the money path with the scenarios that ran it; a part
none ran, or a promise broken, turns the night red."""

from __future__ import annotations

import csv
import random
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import replace
from datetime import date, datetime, timedelta
from decimal import Decimal
from itertools import pairwise
from pathlib import Path
from shutil import rmtree
from types import ModuleType

from desk import book, broker, day, halt, kill, orders, strategy
from desk.broker import Crash, Fault, Pretend, Report
from desk.lines import YARDSTICK, Line
from desk.orders import HOLDINGS, Order, Sale, Settings, pennies
from desk.simcity_census import Census
from desk.simcity_incidents import (
    CANCELLED,
    DEAF,
    HOLE,
    LEFT,
    LIVE,
    LOCKED,
    PARKED,
    SHUT,
    SILENT,
    SLOW,
    STALE,
    STOP_SILENT,
    UNBARRED,
    UNHELD,
    beside,
    cancelled,
    deaf,
    gateway_silent,
    hole,
    locked,
    minutes,
    parked,
    silent,
    slow,
    stale,
    unbarred,
    unheld,
    unreachable,
)
from desk.simcity_parts import MONTH, Archive, Night
from desk.simcity_parts import _market as dealt
from desk.simcity_parts2 import _behind, _gapped, _killed
from desk.store import Bar
from desk.strategy import Action

Rates = Mapping[str, Decimal]  #: the pounds per unit of each currency, every day of the night

__all__ = ["MONTH", "Archive", "Night", "_gapped"]  #: given on from simcity_parts, 2

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
STOPS = "a stop is moved and a sale is weighed against the gap limit"
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

    def retest(self, symbol: str, on: date) -> None:
        """The day's bar as the world made it again is tried against the line's resting stop."""
        self._test(symbol, self._bars.get((symbol, on)))

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


THROUGH = "a gap opens below a resting stop"
BELOW = Decimal("0.9")  #: the gap scenario's open, against the stop it jumps


def history(bars: Sequence[Bar]) -> list[Decimal]:
    """The line's own gaps in the saved days: each open over the close before it."""
    return [b.open / a.close for a, b in pairwise(bars)]


def _market(archive: Archive, rng: random.Random) -> dict[Line, tuple[Bar, ...]]:
    """A WORLD'S MARKET with its overnight gaps: the days dealt again (simcity_parts), then each
    day opened away from the world's close before it by a gap drawn from the line's own saved
    history before that day, point-in-time; a copy of the world's draw does it, so no other
    draw moves. A line's first day, with no history before it, keeps the open it was dealt."""
    market, draw = dealt(archive, rng), random.Random()  # noqa: S311 - a repeatable draw
    draw.setstate(rng.getstate())
    for line, bars in market.items():
        gaps = history(archive[line])
        for at in range(1, len(bars)):
            if gaps[: at - 1]:
                start = pennies(bars[at - 1].close * draw.choice(gaps[: at - 1]))
                bars = (*bars[:at], widen(bars[at], start), *bars[at + 1 :])
        market[line] = tuple(bars)
    return market


def widen(bar: Bar, start: Decimal) -> Bar:
    """The bar opened at start, its range stretched to hold the open."""
    return replace(bar, open=start, high=max(bar.high, start), low=min(bar.low, start))


def _through(life: _Life, on: date) -> bool:
    """A held line opens below its resting stop: the stop sells at the open, not at its level,
    and the day's record counts the loss beyond the stop. False when no stop rests: still owed."""
    stops = life.pretend.resting_stops()
    if not stops:
        return False
    symbol, (shares, level) = next(iter(stops.items()))
    start = pennies(level * BELOW)
    life.market = {
        x: tuple(widen(b, start) if x.symbol == symbol and b.day == on else b for b in bars)
        for x, bars in life.market.items()
    }
    life.pretend.reopen(on, life.market)
    life.pretend.retest(symbol, on)
    record = life.live(on)
    sold = [
        f for f in book.fills(life.desk) if f.symbol == symbol and f.day == on and f.quantity < 0
    ]
    life.promise(
        "a gap through a stop sells at the open below it", [f.price for f in sold] == [start]
    )
    life.promise("the day of a gap through a stop is recorded", record.profit is not None)
    return True


def _unstopped(life: _Life, on: date) -> None:
    """The stop under a holding of the seed's choosing is cancelled by hand, and put back after
    the day's record if the same shares are still held; one time in FORGOTTEN it never is."""
    held = life.rng.choice(life.pretend.stops())
    put_back = life.pretend.lose_stop(held[0])
    life.live(on)
    if life.rng.randrange(FORGOTTEN) and held in life.pretend.holdings():
        put_back()


Event = tuple[str, Callable[[_Life, date], object]]
EVENTS: tuple[Event, ...] = (
    (STALE, stale),
    (BEHIND, _behind),
    (UNSTOPPED, _unstopped),
    (GAPPED, _gapped),
    (KILLED, _killed),
    (THROUGH, _through),
    (HOLE, hole),
    (LEFT, beside),
    (CANCELLED, cancelled),
    (PARKED, parked),
    (DEAF, deaf),
    (UNHELD, unheld),
    (UNBARRED, unbarred),
    (LOCKED, locked),
    (LIVE, minutes),
    (SILENT, silent),
    (SLOW, slow),
    (STOP_SILENT, gateway_silent),
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
            folder = (
                root / "worlds" / str(seed)
            )  #: kept after the night, emptied as its world starts
            if folder.exists():
                rmtree(folder)  #: a leftover that cannot go fails loudly, naming its path
            folder.mkdir(parents=True)
            lives.append(_Life(folder, archive, room, rates, seed, census))
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


def _stops(life: _Life) -> None:
    """The first stop resting is moved to the level it has, and a buy sized at that stop is sold
    at its own price: no scenario's draw decides whether these parts run (R-RUNNER-391)."""
    symbol, (shares, level) = next(iter(life.pretend.resting_stops().items()))
    life.pretend.restop(symbol, level)
    life.promise(
        "a stop moved to its own level stays there",
        life.pretend.resting_stops()[symbol][1] == level,
    )
    line = next(x for x in life.market if x.symbol == symbol)
    order = Order(f"stops-{symbol}", line, shares, level * 2, life.rates[line.currency], level)
    kept = orders.gap_loss(order, order.price) == 0 and not orders.gapped(
        order, order.price, life.room
    )
    life.promise("a sale at the price it was sized at loses nothing to a gap", kept)
    buy = strategy.Decision("rule", symbol, life.records[-1].day, strategy.Action.BUY)
    price, fx, held = Decimal(100), life.rates[line.currency], book.positions(life.desk)
    gap = orders.stop_under(line, price) - 1  #: the live price gaps under the signal's stop
    try:
        orders.size(buy, line, price, fx, life.room, held, gap)
        refused = False
    except orders.Refused:
        refused = True
    life.promise("a gap down past the stop refuses the buy", refused)


def _told(trips: tuple[book.RoundTrip, ...]) -> bool:
    """The profit attributed by line, and by days held, is each the trips' own total."""
    totals = (
        sum(book.attributed(trips, by).values(), Decimal(0))
        for by in (lambda t: t.buy.symbol, lambda t: (t.sell.day - t.buy.day).days)
    )
    return all(total == sum((t.profit for t in trips), Decimal(0)) for total in totals)


def _live(life: _Life) -> None:
    """The life, day by day, and its reckoning. On one in EVENTFUL of the mornings it holds a line
    under its stop after a plain record, a thing is done to it, each in the seed's order."""
    census, pretend, todo = life.census, life.pretend, list[Event]()
    for on in sorted({b.day for bs in life.market.values() for b in bs if b.day > life.began}):
        census.now(DAY)
        pretend.open(on)
        fit = life.records and not life.records[-1].mismatches and pretend.stops()
        if fit and STOPS not in life.done:
            census.now(STOPS)
            _stops(life)
            life.done.add(STOPS)
            census.now(DAY)
        if fit and life.rng.randrange(EVENTFUL) == 0:
            todo = todo or life.rng.sample(EVENTS, len(EVENTS))
            scenario, happen = todo.pop()
            census.now(scenario)
            ran = happen(life, on) is not False  #: False: it could not run today, still owed
            todo += [] if ran else [(scenario, happen)]
            life.done |= {scenario} if ran else set()
        elif SHUT not in life.done:  #: once, on a plain morning; it draws nothing from the seed
            census.now(SHUT)
            unreachable(life, on)
            life.done.add(SHUT)
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
    life.promise("profit told by line and by days held adds up to the trips'", _told(trips))
    stories = book.told(trips, life.market)
    life.promise("every trade is told with the bar its signal read", len(stories) == len(trips))
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
