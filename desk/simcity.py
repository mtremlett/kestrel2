"""simcity - SIMCITY, SMALL. ONE COMMAND lives the desk's whole day on every session of the
saved data, at the pretend broker with every one of its faults, and writes one record of the
night. What goes wrong on a real desk is done to this one on the way: it dies mid-send and is
started again, a position appears behind its back, a stop is cancelled by hand, the kill
switch is pulled. THE CENSUS names every part of the money path with the scenarios that ran
it, measured as the night runs and never claimed. A part no scenario ran, or a promise of
the desk's seen broken, turns the night red."""

from __future__ import annotations

import cProfile
import csv
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from itertools import cycle
from pathlib import Path
from tempfile import TemporaryDirectory
from types import CodeType, ModuleType

from desk import book, broker, day, kill, orders, strategy
from desk.broker import Crash, Fault, Pretend, Report
from desk.lines import Line
from desk.orders import Order, Sale, Settings
from desk.store import Bar
from desk.strategy import Action

Archive = Mapping[Line, Sequence[Bar]]
Rates = Mapping[str, Decimal]  #: the pounds per unit of each currency, every day of the night

NIGHTS = "simcity.csv"
HEADER = (
    *("at", "verdict", "days", "clean", *(fault.name.lower() for fault in Fault), "deaths"),
    *("withheld", "trips", "profit", "market", "idle", "bare", "broken"),
)
#: THE MONEY PATH: the modules an order travels through, from a rule's decision to the day's
#: record, and the switch that stops it.
PATH: tuple[ModuleType, ...] = (strategy, orders, broker, book, day, kill)
#: The scenarios, as the census names them.
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
    """ONE NIGHT'S RECORD: what the desk's life came to, the census, and every promise of the
    desk's that the night saw broken. Green is no part bare and no promise broken."""

    at: datetime
    days: int  #: sessions lived, each with its own day's record
    met: Mapping[Fault | None, int]  #: the orders at the broker's door, by the fault each met
    deaths: int  #: times the desk died mid-send and was started again
    withheld: int  #: days whose profit was withheld, the book not the broker's
    trips: int  #: round trips closed
    profit: Decimal  #: pounds after every cost: the days' records added up
    market: Decimal  #: pounds the capital would have made simply holding the market
    idle: tuple[str, ...]  #: the rules that never held a line all night
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
            f"lived {self.days} days at the pretend broker. Of its orders {self.met[None]} met no "
            f"fault; {met}. It died mid-send and was started again {self.deaths} times. On "
            f"{self.withheld} days the book was not the broker's and the profit withheld. "
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
                for wrapper in ("fget", "func", "__func__", "__wrapped__"):
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


class _Counted(Pretend):
    """The pretend broker, counting the orders at its door by the fault each met there: the
    one waiting on its line that the broker used up on it, or none."""

    def __init__(self, archive: Archive, faults: Mapping[str, Fault]) -> None:
        super().__init__(archive, faults)
        self.met: Counter[Fault | None] = Counter()
        self.buys = 0  #: the orders to buy that reached the door

    def place(self, order: Order | Sale) -> Report:
        self.buys += isinstance(order, Order)
        waiting = self._faults.get(order.line.symbol)
        try:
            return super().place(order)
        finally:  #: counted however the order ended, an error raised to the desk too
            self.met[None if order.line.symbol in self._faults else waiting] += 1


class _Life:
    """One desk's life over the saved data, a fault of the broker's waiting on every line,
    and what the night has seen of the desk's promises."""

    def __init__(self, desk: Path, archive: Archive, room: Settings, rates: Rates) -> None:
        self.desk, self.archive, self.room, self.rates = desk, archive, room, rates
        symbols = sorted(line.symbol for line in archive)
        self.pretend = _Counted(archive, dict(zip(symbols, cycle(Fault), strict=False)))
        self.census, self.records = _Census(), list[day.Record]()
        self.deaths, self.kept = 0, dict[str, bool]()

    def promise(self, words: str, kept: bool) -> None:
        self.kept[words] = kept and self.kept.get(words, True)

    def live(self, on: date) -> day.Record:
        """One day whole, from the data saved by its end, and its record."""
        saved = {line: [b for b in bars if b.day <= on] for line, bars in self.archive.items()}
        scenario, buys = self.census.scenario, self.pretend.buys
        record = self._run(saved, on)
        self.census.now(scenario)
        quiet = not (record.mismatches and self.pretend.buys > buys)
        self.promise("nothing is bought on a day the book is not the broker's", quiet)
        few = len(book.positions(self.desk)) <= orders.HOLDINGS
        self.promise(f"never more than {orders.HOLDINGS} lines are held", few)
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
    """Shares the desk did not buy are at the broker before the day, and gone after its record."""
    symbol = min(line.symbol for line in life.archive)
    life.pretend.inject(symbol, 7)
    record = life.live(on)
    life.pretend.inject(symbol, -7)
    life.promise("a position the desk did not make is named", record.mismatches == (symbol,))


def _unstopped(life: _Life, on: date) -> None:
    """The stop under a holding is cancelled by hand, and nothing puts it back: the line is
    named every day until its rule sells it."""
    symbol = life.pretend.stops()[0][0]
    life.pretend.cancel_stop(symbol)
    record = life.live(on)
    named = record.mismatches == (symbol,) or symbol not in book.positions(life.desk)
    life.promise("a holding that lost its stop is named until it is sold", named)


def _killed(life: _Life, on: date) -> None:
    """The switch is pulled before the day and released after its record; then the drill."""
    at, reached = datetime.combine(on, time(7), UTC), life.pretend.submitted()
    said = kill.pull(life.desk, life.pretend, at, "SimCity pulls it for a day")
    life.live(on)
    quiet = life.pretend.submitted() == reached and "KILL SWITCH ON" in said.words()
    life.promise("with the kill switch on nothing reaches the broker, and the desk says so", quiet)
    kill.release(life.desk, at, "SimCity releases it")
    kill.drill(life.desk, at)
    life.promise("the kill switch's drill is on the record", kill.drilled(life.desk, on))


Event = tuple[str, Callable[[_Life, date], object]]
#: What is done to the desk, in this order.
EVENTS: tuple[Event, ...] = ((BEHIND, _behind), (UNSTOPPED, _unstopped), (KILLED, _killed))


def run(root: Path, archive: Archive, room: Settings, rates: Rates, at: datetime) -> Night:
    """THE ONE COMMAND. A desk that holds nothing lives every session of the archive after
    its first, on a book of its own that is thrown away; the night's one record is added to
    those kept under root, dated at, and given back. Red or green, it is kept."""
    if at.utcoffset() != timedelta(0):
        raise ValueError(f"SimCity's night at {at}: not a time in UTC")
    path, rows = root / NIGHTS, [list(HEADER)]
    if path.exists():
        with path.open(newline="", encoding="utf-8") as kept:
            rows = list(csv.reader(kept))
        if rows[:1] != [list(HEADER)]:
            raise ValueError(f"{path}: not SimCity's nights")
    with TemporaryDirectory() as scratch:
        life = _Life(Path(scratch), archive, room, rates)
        try:
            night = _live(life, at)
        finally:
            life.census.now(None)
    said = ("; ".join(names) for names in (night.idle, night.bare, night.broken))
    money = (night.deaths, night.withheld, night.trips, night.profit, night.market)
    verdict = "GREEN" if night.green else "RED"
    row = (at.isoformat(), verdict, night.days, *night.met.values(), *money, *said)
    book._write(path, [*rows, row])
    return night


def _live(life: _Life, at: datetime) -> Night:
    """The life, day by day. Each thing done to the desk waits for the first morning on which
    it holds a line under its stop and its last record was a plain one: no two are muddled."""
    census, pretend, todo = life.census, life.pretend, list(EVENTS)
    census.now(RULES)
    alone = strategy.decide({line.symbol: bars for line, bars in life.archive.items()})
    asked = {(decision.strategy, decision.action) for decision in alone}
    both = {(rule, to) for rule in strategy.STRATEGIES for to in (Action.BUY, Action.SELL)}
    life.promise("every rule asks to buy and to sell somewhere in the data", both <= asked)
    for on in sorted({bar.day for bars in life.archive.values() for bar in bars})[1:]:
        census.now(DAY)
        pretend.open(on)
        if todo and life.records and not life.records[-1].mismatches and pretend.stops():
            scenario, happen = todo.pop(0)
            census.now(scenario)
            happen(life, on)
        else:
            life.live(on)
    census.now(RECKONING)
    return _reckon(life, at, [f"never happened: {scenario}" for scenario, _ in todo])


def _reckon(life: _Life, at: datetime, never: Sequence[str]) -> Night:
    """What the life came to: the desk's last promises tried, and the night's record made."""
    records, fills, reached = life.records, book.fills(life.desk), life.pretend.submitted()
    days, last = len(records), records[-1]
    cash, costs = book.dealt(life.desk, life.archive, last.day, date.min, 0)
    profit = sum((r.profit for r in records if r.profit is not None), Decimal(0))
    market = sum((r.market for r in records if r.profit is not None), Decimal(0))
    withheld = sum(r.profit is None for r in records)
    near = abs(profit - (last.worth + cash - costs.total)) <= days * Decimal("0.005")
    ends = near and last.profit is not None
    life.promise("the night ends plain, its days' profits adding up to the ledger's", ends)
    life.promise("the ledger is the broker's own fills", fills == life.pretend.fills())
    life.promise("no order reached the broker twice", len(set(reached)) == len(reached))
    trips = len(book.round_trips(life.desk, life.archive))
    held = {orders.strategy_of(fill.order_id) for fill in fills if fill.quantity > 0}
    idle = tuple(rule for rule in strategy.STRATEGIES if rule not in held)
    life.census.now(None)
    census = {part: tuple(sorted(ran)) for part, ran in life.census.ran.items()}
    met = {fault: life.pretend.met[fault] for fault in (None, *Fault)}
    census |= {f"broker.Fault.{f.name}": (FAULTS,) if met[f] else () for f in Fault}
    broken = (*(words for words, kept in life.kept.items() if not kept), *never)
    return Night(at, days, met, life.deaths, withheld, trips, profit, market, idle, census, broken)
