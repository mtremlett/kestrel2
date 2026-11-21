"""conformance_parts - the steps of a conformance run at ONE broker, and the pretend broker's run
of them: the plan's orders, each step, the account put back (split from desk/conformance.py,
R-RUNNER-234; that module imports what is here and is the command)."""

from __future__ import annotations

import random
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

from desk import archive, book, day, keeper, venues
from desk.broker import Broker, Pretend
from desk.command import CAPITAL
from desk.halt import Blocker
from desk.lines import LINES, Line
from desk.orders import Order, Refused, Sale, Settings, order_id_of, size
from desk.running import DAY
from desk.store import Bar
from desk.strategy import Action, Decision

TRIGGER = "the stop triggered"  #: the step whose real side is IBKR's own stop firing
FAILED, UNTRIED = "FAILED, ", "not tried: an earlier step failed"
ROOM = Settings(CAPITAL)  #: the desk's one capital sizes the orders, as on its own day
NOT_SIZED = (Decimal(1), Decimal(1))  #: the gate refuses before a price is used
Fall = Callable[[Order], str | None]  #: the market made to reach a buy's stop: what it found
PUT_BACK = "nothing to put back"  #: what the last step answers when it found the account as it was


@dataclass(frozen=True)
class Plan:
    """A run's orders, each dated the session before today, made before any is sent."""

    today: date
    refusal: Decision  #: a buy of a line no retail customer may buy: the gate refuses it
    first: Order  #: one share of the line
    sale: Sale  #: of that share
    second: Order  #: the line at the desk's own size
    stamp: str  #: the run's own minute: an id told apart from every earlier run's of the day


@dataclass(frozen=True)
class Side:
    """One broker a run trades at, on a record of its own, and its two doors."""

    root: Path
    broker: Broker
    check: Callable[[], Sequence[str] | None]  #: the day's check, run now: what it names
    fall: Fall


def _named(line: Line, today: date, name: str) -> Decision:
    """An order's name: dated its venue's session before today (placing.Paper._cleared)."""
    before = venues.sessions(line.venue, today - 9 * DAY, today)[-2]
    return Decision(name, line.symbol, before, Action.BUY)


def _last(line: Line, today: date, home: Path | None) -> Bar:
    """A line's bar of the session before today: from the desk's store (the long database, IBKR
    first) when a home is given, else the archive; none, and nothing is sized."""
    last = _named(line, today, "bar").day
    if home is None:
        held, source = archive.fetch(line, today), "the archive"
    else:
        try:
            held, source = keeper.saved(home, today, [line])[0][line], "the store"
        except keeper.Stale as e:
            raise ValueError(f"{line.symbol}: the store has no bar of {last}: {e}") from e
    bars = [bar for bar in held if bar.day == last]
    if not bars:
        raise ValueError(f"{line.symbol}: {source} has no bar of {last}, the session before")
    return bars[-1]


def plan(
    lines: Sequence[Line],
    refused: Line,
    today: date,
    fx: Mapping[str, Decimal],
    stamp: str,
    home: Path | None = None,
    seed: int | None = None,
) -> Plan:
    """The run's orders: on the line given that traded the most money in its last session (or,
    given a seed, the line that seed draws of them, the same line for the same seed and lines),
    sized at its close by the desk's own sizer; and one share of the line to be refused. Every
    order id carries the stamp: book.send answers an id the broker already knows from the broker's
    word of it, so a second run of a day on the first's ids would send nothing."""
    if not lines:
        raise ValueError("the broker lists no plain line of the market for the run to trade")
    bars = {line: _last(line, today, home) for line in lines}
    line = max(bars, key=lambda line: bars[line].close * bars[line].volume * fx[line.currency])
    if seed is not None:  #: a soak's round, drawn so the rounds reach every plain line
        line = random.Random(seed).choice(sorted(bars, key=lambda line: line.symbol))  # noqa: S311 - a drawn line, no secret
    its = line.venue.lower() + stamp  #: each run names its orders its own: the refusal's too

    def sized(name: str, line: Line, close: Decimal) -> Order:
        return size(_named(line, today, name + its), line, close, fx[line.currency], ROOM, {})

    first = replace(sized("conf1", line, bars[line].close), quantity=1)
    named = _named(line, today, f"conf2{its}")
    sale = Sale(order_id_of(named), line, 1, session=named.day)
    refusal = _named(refused, today, "conf0" + its)
    return Plan(today, refusal, first, sale, sized("conf3", line, bars[line].close), stamp)


def _send(side: Side, order: Order | Sale) -> str:
    """An order through the desk's send path, only on a clean check; and its answer."""
    if found := side.check():
        raise Refused(f"{order.order_id}: not sent, the day's check named: {'; '.join(found)}")
    sent = book.send(side.root, side.broker, order, ROOM)
    done = f"{order.order_id}: {sent.filled} of {order.quantity} shares done"
    return done + f" ({sent.reason})" * bool(sent.reason)


def _gate(side: Side, run: Plan) -> str:
    """THE REFUSAL: a buy of a line no retail customer may buy goes to the desk's own gate
    (day._buy), which must refuse it, in its own words, before anything leaves; else an error."""
    line = next(x for x in LINES if x.symbol == run.refusal.symbol)
    sent = day._buy(side.root, side.broker, run.refusal, line, NOT_SIZED, ROOM, run.today, None)
    if sent.blocker is not Blocker.GATE or sent.filled:
        raise ValueError(f"{sent.order_id}: the gate did not refuse it: {sent.reason}")
    return sent.reason or ""


def _leave(side: Side, run: Plan) -> str:
    """THE ACCOUNT PUT BACK: working orders cancelled, shares sold, the check clean; or an error."""
    did = [f"cancelled {name}" for name in side.broker.cancel()]
    book.collect(side.root, side.broker)
    for symbol, shares in book.positions(side.root).items():
        line = next(line for line in LINES if line.symbol == symbol)
        name = _named(line, run.today, f"conf9{run.second.line.venue.lower()}{run.stamp}")
        did.append(_send(side, Sale(order_id_of(name), line, shares, session=name.day)))
    found, held = side.check(), book.positions(side.root)
    if found or held:
        raise ValueError(f"the account is not as found: the book holds {held}; the check: {found}")
    return "; ".join(did) or PUT_BACK


def _steps(run: Plan) -> tuple[tuple[str, Callable[[Side], str | None]], ...]:
    """The run's steps, each with its name: what it answers, or nothing beyond having been done."""
    return (
        ("a refusal", lambda side: _gate(side, run)),
        ("a market buy at the open, its stop resting", lambda side: _send(side, run.first)),
        ("a sale, the stop cancelled first", lambda side: _send(side, run.sale)),
        ("a buy of the desk's size, a part fill if given", lambda side: _send(side, run.second)),
        (TRIGGER, lambda side: side.fall(run.second)),
        ("the account left as found", lambda side: _leave(side, run)),
    )


def _seen(side: Side, since: int) -> str:
    """What a step left, as the desk sees any broker: new fills, holdings, resting stops."""
    book.collect(side.root, side.broker)
    fills = [f"{f.order_id} {f.quantity:+} at {f.price}" for f in book.fills(side.root)[since:]]
    held = [f"{name} {shares}" for name, shares in side.broker.holdings() if shares]
    stops = [f"{name} {shares}" for name, shares in side.broker.stops()]
    left = {"fills": fills, "held": held, "stops": stops}
    return "; ".join(f"{what}: {', '.join(of) or 'none'}" for what, of in left.items())


def live(side: Side, run: Plan, note: Callable[[str, str], None]) -> list[str]:
    """A RUN AT ONE BROKER: each step noted as it is done; the names of those that failed."""
    steps, failed = _steps(run), list[str]()
    for name, act in steps:
        since, said = len(book.fills(side.root)), UNTRIED
        try:
            if not failed or name == steps[-1][0]:
                said = f"{act(side) or 'done'}; {_seen(side, since)}"
        except Exception as fault:  # noqa: BLE001 - a step that fails is the run's finding, named
            said = f"{FAILED}{type(fault).__name__}: {fault}"
            failed.append(name)
        note(name, said)
    return failed


def pretend(run: Plan, price: Decimal | None = None, rests: bool = False) -> dict[str, str]:
    """The run at the pretend broker: the sizing prices, a refusal, and the stop triggered at
    the price given, the real stop's fill (a stop put above the market sells at the market, as
    IBKR's does); without one, a fall to the stop's own level. With rests, the stop is left
    resting unsold, as London's rested on 16 November: the last step then sells the shares."""
    today, buy = run.today, run.second
    at = buy.stop if price is None else price
    bars = {buy.line: (Bar(today, *(buy.price,) * 4, 0), Bar(today + DAY, *(at,) * 4, 0))}
    broker = Pretend(bars, {})
    broker.open(today)
    said: dict[str, str] = {}

    def fall(_: Order) -> None:
        if rests:
            return
        broker.open(today + DAY)
        if broker.holdings():  #: the stop above the market: it sells at once, at that bar
            broker.place(Sale(f"{buy.order_id}-stop", buy.line, buy.quantity))

    with TemporaryDirectory() as scratch:
        live(Side(Path(scratch), broker, lambda: (), fall), run, said.__setitem__)
    return said
