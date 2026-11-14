"""simcity - SIMCITY. ONE COMMAND lives the desk's day through a hundred seeded worlds of the saved
data, at the pretend broker with all its faults, and writes one record of the night. A WORLD is
the saved lines on their own days, each line's months dealt again by the world's number; by it
too come the broker's faults and what goes wrong on a real desk: it dies mid-send and is started
again, a position appears behind its back, a stop is cancelled by hand, the kill switch is
pulled. THE CENSUS names each part of the money path with the scenarios that ran it. A part none
ran, or a promise broken in a world, turns the night red and names the world."""

from __future__ import annotations

import cProfile
import csv
import random
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from itertools import chain, pairwise
from pathlib import Path
from tempfile import TemporaryDirectory
from types import CodeType, ModuleType

from desk import book, broker, day, halt, kill, orders, strategy
from desk.broker import Crash, Fault, Pretend, Report
from desk.lines import Line
from desk.orders import HOLDINGS, Order, Sale, Settings, pennies
from desk.store import Bar
from desk.strategy import Action

Archive = Mapping[Line, Sequence[Bar]]
Rates = Mapping[str, Decimal]  #: the pounds per unit of each currency, every day of the night

NIGHTS = "simcity.csv"
HEADER = (
    *("at", "verdict", "worlds", "days", "clean", *(fault.name.lower() for fault in Fault)),
    *("deaths", "withheld", "trips", "profit", "market", "idle", "bare", "broken"),
)
#: THE MONEY PATH: the modules an order travels through, from a rule's decision to the record.
PATH: tuple[ModuleType, ...] = (strategy, orders, broker, book, day, kill)
WORLDS = range(100)  #: a night's worlds, each named by the number that seeds its every draw
MONTH = 20  #: sessions of a line's that stay together, in their saved order, in every world
FAULTY = 4  #: of the orders at the broker's door, one in so many finds a fault waiting
EVENTFUL = 8  #: of the mornings a desk is fit for it, one in so many has something done to it
FORGOTTEN = 8  #: of the stops cancelled by hand, one in so many is never put back
RULES = "the rules alone, on all the data"
DAY = "a day of the desk"
RESTART = "the desk dies mid-send and is started again"
FAULTS = "the broker's faults"
BEHIND = "a position appears behind the desk's back"
UNSTOPPED = "a stop is cancelled by hand"
KILLED = "the kill switch is pulled, released and drilled"
RECKONING = "the night's reckoning"


@dataclass(frozen=True)
class Night:
    """ONE NIGHT'S RECORD: what the desk's lives came to, added up over the worlds, the census,
    and every promise of the desk's that the night saw broken, with how many worlds broke it
    and the first of them. Green is no part bare and no promise broken."""

    at: datetime
    worlds: int  #: seeded worlds lived, each from holding nothing to its end or the desk's stop
    days: int  #: sessions lived in them all, each with its own day's record
    met: Mapping[Fault | None, int]  #: the orders at the broker's door, by the fault each met
    deaths: int  #: times the desk died mid-send and was started again
    withheld: int  #: days whose profit was withheld, the book not the broker's
    trips: int  #: round trips closed, in the worlds lived to their end
    profit: Decimal  #: pounds after every cost: the days' records added up
    market: Decimal  #: pounds the capital would have made simply holding the market
    idle: tuple[str, ...]  #: the rules that held no line in any world lived to its end
    census: Mapping[str, tuple[str, ...]]  #: each part of the money path, and what ran it
    broken: tuple[str, ...]

    @property
    def bare(self) -> tuple[str, ...]:
        """The parts no scenario ran."""
        return tuple(part for part, ran in self.census.items() if not ran)

    @property
    def green(self) -> bool:
        return not (self.bare or self.broken)

    def words(self) -> str:
        """One message, in plain English, for whoever must be told."""
        met = "; ".join(f"{fault.value}: {n}" for fault, n in self.met.items() if fault)
        idle = f" Rules that never held a line: {', '.join(self.idle)}." if self.idle else ""
        bare = f" NO SCENARIO for {', '.join(self.bare)}." if self.bare else ""
        broken = f" BROKEN: {'; '.join(self.broken)}." if self.broken else ""
        return (
            f"SIMCITY {'GREEN' if self.green else 'RED'}, {self.at:%Y-%m-%d %H:%M} UTC. The desk "
            f"lived {self.worlds} seeded worlds, {self.days} days, at the pretend broker. Of its "
            f"orders {self.met[None]} met no fault; {met}. It died mid-send and was started "
            f"again {self.deaths} times. On {self.withheld} days the book was not the broker's "
            f"and the profit withheld. "
            f"{self.trips} round trips made {self.profit} pounds after every cost; holding the "
            f"market made {self.market}.{idle} Census: {len(self.census)} parts of the money "
            f"path, {len(self.bare)} with no scenario.{bare}{broken}"
        )


def parts() -> dict[CodeType, str]:
    """THE PARTS: all that a module of the money path offers by name, each function and each
    method or property of its classes, under the name the code gives it. A name beginning
    with an underscore is its callers' business, and a Protocol's methods are a question's
    wording with nothing to run."""
    found: dict[CodeType, str] = {}
    for module in PATH:
        for name, thing in vars(module).items():
            own = getattr(thing, "__module__", None) == module.__name__
            if name.startswith("_") or not own or getattr(thing, "_is_protocol", False):
                continue
            members = vars(thing).items() if isinstance(thing, type) else ((name, thing),)
            for inner, member in members:
                for wrapper in ("fget", "__wrapped__"):  #: a property; a class's or static method
                    member = getattr(member, wrapper, member)
                code = getattr(member, "__code__", None)
                if isinstance(code, CodeType) and not inner.startswith("_"):
                    found[code] = f"{module.__name__.rpartition('.')[2]}.{code.co_qualname}"
    return found


class _Census:
    """THE CENSUS, MEASURED: which parts ran, and in which scenario. The standard library's
    profiler sees every call made while a scenario is in force; nothing is claimed by hand."""

    def __init__(self) -> None:
        self._parts = parts()
        self.ran: dict[str, set[str]] = {name: set() for name in sorted(self._parts.values())}
        self._profile = cProfile.Profile(subcalls=False, builtins=False)
        self.scenario: str | None = None

    def now(self, scenario: str | None) -> None:
        """From here every call is this scenario's; with none, the watching ends."""
        if self.scenario is not None:
            self._profile.disable()
            for code in (entry.code for entry in self._profile.getstats()):
                if isinstance(code, CodeType) and code in self._parts:
                    self.ran[self._parts[code]].add(self.scenario)
            self._profile.clear()
        self.scenario = scenario
        if scenario is not None:
            self._profile.enable()


def _market(archive: Archive, rng: random.Random) -> dict[Line, tuple[Bar, ...]]:
    """A WORLD'S MARKET: every saved line on its own days, from its own first bar. Each day's
    bar keeps its shape against the close before it, to the penny, and those days are dealt
    again a MONTH at a time, each line's months in an order of its own: a world's lines do
    not move as one, and each still ends where its saved history does."""
    market = {}
    for line in sorted(archive, key=lambda line: line.symbol):
        bars = archive[line]
        steps = list(pairwise(bars))
        months = [steps[at : at + MONTH] for at in range(0, len(steps), MONTH)]
        rng.shuffle(months)
        made = list(bars[:1])
        level = made[0].close if made else Decimal(0)  #: the world's close, before rounding
        for kept, (before, bar) in zip(bars[1:], chain.from_iterable(months), strict=True):
            shape = (bar.open, bar.high, bar.low, bar.close)
            start, high, low, close = (pennies(p * level / before.close) for p in shape)
            made.append(Bar(kept.day, start, high, low, close, bar.volume))
            level *= bar.close / before.close
        market[line] = tuple(made)
    return market


class _Counted(Pretend):
    """One world's pretend broker. For one in FAULTY of the orders at its door a fault, drawn
    by the world's seed, is set waiting on the order's line; each order is counted by the fault
    it met there: the one waiting on its line that the broker used up on it, or none."""

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

    def lose_stop(self, symbol: str) -> Callable[[], None]:
        """Cancel a resting stop by hand; what is given back puts it back as it was."""
        stop = self._stops[symbol]
        self.cancel_stop(symbol)
        return lambda: self._stops.update({symbol: stop})


class _Life:
    """One desk's life in one world: its market, its broker, and its promises kept or not."""

    def __init__(
        self, desk: Path, archive: Archive, room: Settings, rates: Rates, seed: int, census: _Census
    ) -> None:
        self.desk, self.room, self.rates, self.seed, self.census = desk, room, rates, seed, census
        self.rng = random.Random(seed)  # noqa: S311 - a repeatable draw, not a secret
        self.market = _market(archive, self.rng)
        self.pretend = _Counted(self.market, self.rng)
        self.records, self.deaths, self.trips = list[day.Record](), 0, 0
        self.kept, self.done, self.held = dict[str, bool](), set[str](), set[str]()
        self.stopped = ""  #: the day the desk said it could not go on, and its words

    def promise(self, words: str, kept: bool) -> None:
        self.kept[words] = kept and self.kept.get(words, True)

    def live(self, on: date) -> day.Record:
        """One day whole, from the data saved by its end, and its record."""
        saved = {line: [b for b in bars if b.day <= on] for line, bars in self.market.items()}
        scenario, buys = self.census.scenario, self.pretend.buys
        record = self._run(saved, on)
        self.census.now(scenario)
        quiet = not (record.mismatches and self.pretend.buys > buys)
        self.promise("nothing is bought on a day the book is not the broker's", quiet)
        held, stopped = book.positions(self.desk), dict(self.pretend.stops())
        self.promise(f"never more than {HOLDINGS} lines are held", len(held) <= HOLDINGS)
        self.promise("no order is left working at a day's end", not self.pretend.working())
        bare = {*held} - {*stopped} - {*record.mismatches}
        self.promise("a line held with no stop at the broker is named that day", not bare)
        mine = dict(self.pretend.holdings())  #: a line whose shares are not the book's is not
        told = {b.reason.partition(":")[0] for b in halt.morning(self.desk, on)[halt.Blocker.BOOK]}
        untold = {s for s, n in held.items() if s not in stopped and mine.get(s) == n} - told
        self.promise("a line held with no stop is on that day's list, with its stop", not untold)
        same = held == stopped == mine
        named = bool(record.mismatches)
        self.promise("no line is named on a day the book is the broker's", not (same and named))
        self.records.append(record)
        return record

    def _run(self, saved: Archive, on: date) -> day.Record:
        try:
            return day.run(self.desk, saved, self.pretend, self.room, on, self.rates)
        except Crash:  #: the desk died mid-send: it is started again, and runs the same day
            self.deaths += 1
            self.census.now(RESTART)
            return self._run(saved, on)


def _behind(life: _Life, on: date) -> None:
    """Shares the desk did not buy are at the broker before the day, and gone after its
    record: the seed's number of them, on a line of its choosing, held by the desk or not."""
    symbol = life.rng.choice(sorted(line.symbol for line in life.market))
    shares = life.rng.randint(1, 50)
    life.pretend.inject(symbol, shares)
    record = life.live(on)
    life.pretend.inject(symbol, -shares)
    life.promise("a position the desk did not make is named", record.mismatches == (symbol,))


def _unstopped(life: _Life, on: date) -> None:
    """The stop under a holding of the seed's choosing is cancelled by hand, and put back after
    the day's record if the same shares are still held; one time in FORGOTTEN it never is."""
    held = life.rng.choice(life.pretend.stops())
    put_back = life.pretend.lose_stop(held[0])
    life.live(on)
    if life.rng.randrange(FORGOTTEN) and held in life.pretend.holdings():
        put_back()


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
EVENTS: tuple[Event, ...] = ((BEHIND, _behind), (UNSTOPPED, _unstopped), (KILLED, _killed))


def run(
    root: Path,
    archive: Archive,
    room: Settings,
    rates: Rates,
    at: datetime,
    worlds: Sequence[int] = WORLDS,
) -> Night:
    """THE ONE COMMAND. In each world a desk that holds nothing lives every session of the
    archive after its first, on a book of its own that is thrown away; the night's one record
    is added to those kept under root, dated at, and given back. Red or green, it is kept.
    worlds are the numbers of the worlds to live: one alone is that world again, exactly. A
    world in which the desk refuses to go on ends there, and is a promise broken."""
    if at.utcoffset() != timedelta(0):
        raise ValueError(f"SimCity's night at {at}: not a time in UTC")
    path, rows = root / NIGHTS, [list(HEADER)]
    if path.exists():
        with path.open(newline="", encoding="utf-8") as kept:
            rows = list(csv.reader(kept))
        if rows[:1] != [list(HEADER)]:
            raise ValueError(f"{path}: not SimCity's nights")
    census, lives, seed = _Census(), list[_Life](), None
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
    """The life, day by day, and its reckoning. Something is done to the desk on one in
    EVENTFUL of the mornings it holds a line under its stop and its last record was a plain
    one, so no two are muddled: each thing in turn, in an order the seed deals and deals again."""
    census, pretend, todo = life.census, life.pretend, list[Event]()
    for on in sorted({bar.day for bars in life.market.values() for bar in bars})[1:]:
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
    life.promise("the ledger is the broker's own fills", fills == pretend.fills())
    life.promise("no order reached the broker twice", len(set(reached)) == len(reached))
    bars = {(line.symbol, bar.day): bar for line, days in life.market.items() for bar in days}
    ranged = (bars[f.symbol, f.day].low <= f.price <= bars[f.symbol, f.day].high for f in fills)
    life.promise("every fill is inside its day's range in its world", all(ranged))
    life.trips = len(book.round_trips(life.desk, life.market))
    life.held = {orders.strategy_of(fill.order_id) for fill in fills if fill.quantity > 0}


def _night(
    at: datetime, lives: Sequence[_Life], census: _Census, alone: Sequence[strategy.Decision]
) -> Night:
    """What the worlds came to, added up, and the night's record made: a promise broken is
    named once, with how many worlds broke it and the first of them; a desk that stopped,
    with what it said in the first."""
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
    both = {(rule, to) for rule in strategy.STRATEGIES for to in (Action.BUY, Action.SELL)}
    if not both <= asked:
        broken.append("every rule asks to buy and to sell somewhere in the saved data")
    done = set[str]().union(*(life.done for life in lives))
    broken += [f"never happened: {scenario}" for scenario, _ in EVENTS if scenario not in done]
    held = set[str]().union(*(life.held for life in lives))
    idle = tuple(rule for rule in strategy.STRATEGIES if rule not in held)
    deaths, trips = (sum(life.deaths for life in lives), sum(life.trips for life in lives))
    profit = sum((record.profit or Decimal(0) for record in plain), Decimal(0))
    market = sum((record.market for record in plain), Decimal(0))
    money = (len(records) - len(plain), trips, profit, market)
    return Night(at, len(lives), len(records), met, deaths, *money, idle, ran, tuple(broken))


if __name__ == "__main__":
    from desk import simcitycmd

    raise SystemExit(simcitycmd.main())
