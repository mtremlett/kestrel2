"""conformance - THE CONFORMANCE TRADES, AS A COMMAND (his request, 14 November 2026):

    python -m desk.paper --conformance london|us

One run for each market, in its hours, on the PAPER account: the real broker is given the
orders the desk's day will give it, through the desk's own send path (book.send), and each
real result is recorded beside the pretend broker's (broker.Pretend) in `conformance` under
the folder the environment names (KESTREL2_DATA). It is A DESK OF ITS OWN, with a record and
a client id of its own (CLIENT): whose an order or a fill is, is told by the client that
placed it, so neither desk takes the other's fills into its ledger or cancels its orders.

THE STEPS (`_steps`), on the venue's plain line that traded the most money in its last
session: a rejection (one share of a line the instrument master says no retail customer may
buy); a market buy of one share, its stop resting; its sale, the stop cancelled; a buy of
the desk's own size (a part fill, if given, shows in its fills); that buy's stop made to sell
(the real one is put above the market, `_raised`; the pretend one's market falls to it); and
the account left as found. A step that fails is recorded as failed, in the error's words;
none after it is tried but the last, which puts the account back.

NOTHING IS DONE, code 0: the market is not in continuous trading, or the rejection's is shut
today; a whole run of the market is on record; or today's is, whole or not (one that failed
is tried again on a later day). NOTHING IS SENT, code not 0, unless the gateway is ready, both
desks' kill switches off, this one's drilled, and the account QUIET: nothing held, no order open."""

from __future__ import annotations

import csv
import os
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

from desk import archive, book, clearance, command, gateway, kill, listing, paper, placing, venues
from desk.broker import Broker, Fault, Pretend
from desk.command import CAPITAL
from desk.lines import LINES, Line
from desk.listing import Listing
from desk.orders import Order, Refused, Sale, Settings, order_id_of, size
from desk.running import DAY, VENUES
from desk.store import Bar
from desk.strategy import Action, Decision

MARKETS = {"london": "LSE", "us": "US"}  #: the command's word for each venue
CLIENT = 223  #: the conformance desk's own client id at the gateway: the desk's is paper.CLIENT
ROOT, HEAD = "conformance", ("at", "step", "real", "pretend")
WHOLE, FAILED, UNTRIED = "the run", "FAILED, ", "not tried: an earlier step failed"
ROOM = Settings(CAPITAL)  #: the desk's one capital sizes the orders, as on its own day
ABOVE, WAITS = Decimal("1.05"), 30  #: a stop this far above the price paid; its seconds to sell
Wait = Callable[[float], None]  #: what lets a second pass
Fall = Callable[[Order], None]  #: the market made to reach a buy's stop, which then sells
NOTHING, BARRED = "CONFORMANCE {}: nothing done, {}.", "CONFORMANCE {} NOT BEGUN, nothing sent: "
DONE = "CONFORMANCE {}: {} of {} steps done on {}, each recorded beside the pretend broker's in {}."
AMISS = " FAILED: {}. A later day tries again; the last step named, THE ACCOUNT IS NOT AS FOUND."


@dataclass(frozen=True)
class Plan:
    """A run's orders, each dated the session before today, made before any is sent."""

    today: date
    refusal: Order  #: one share of a line no retail customer may buy
    first: Order  #: one share of the line
    sale: Sale  #: of that share
    second: Order  #: the line at the desk's own size


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


def _last(line: Line, today: date) -> Bar:
    """A line's bar of the session before today, from the archive; none, and nothing is sized."""
    last = _named(line, today, "bar").day
    bars = [bar for bar in archive.fetch(line, today) if bar.day == last]
    if not bars:
        raise ValueError(f"{line.symbol}: the archive has no bar of {last}, the session before")
    return bars[-1]


def plan(lines: Sequence[Line], refused: Line, today: date, fx: Mapping[str, Decimal]) -> Plan:
    """The run's orders: on the line given that traded the most money in its last session,
    sized at its close by the desk's own sizer; and one share of the line to be refused."""
    if not lines:
        raise ValueError("the broker lists no plain line of the market for the run to trade")
    bars = {line: _last(line, today) for line in lines}
    line = max(bars, key=lambda line: bars[line].close * bars[line].volume * fx[line.currency])
    its = line.venue.lower()  #: each market's run names its orders its own: the refusal's too

    def sized(name: str, line: Line, close: Decimal) -> Order:
        return size(_named(line, today, name + its), line, close, fx[line.currency], ROOM, {})

    first = replace(sized("conf1", line, bars[line].close), quantity=1)
    sale = Sale(order_id_of(_named(line, today, f"conf2{its}")), line, 1)
    refusal = replace(sized("conf0", refused, _last(refused, today).close), quantity=1)
    return Plan(today, refusal, first, sale, sized("conf3", line, bars[line].close))


def _send(side: Side, order: Order | Sale) -> str:
    """An order through the desk's send path, only on a clean check; and its answer."""
    if found := side.check():
        raise Refused(f"{order.order_id}: not sent, the day's check named: {'; '.join(found)}")
    sent = book.send(side.root, side.broker, order, ROOM)
    done = f"{order.order_id}: {sent.filled} of {order.quantity} shares done"
    return done + f" ({sent.reason})" * bool(sent.reason)


def _leave(side: Side, run: Plan) -> str:
    """THE ACCOUNT PUT BACK: working orders cancelled, shares sold, the check clean; or an error."""
    did = [f"cancelled {name}" for name in side.broker.cancel()]
    book.collect(side.root, side.broker)
    for symbol, shares in book.positions(side.root).items():
        line = next(line for line in LINES if line.symbol == symbol)
        name = _named(line, run.today, f"conf9{run.second.line.venue.lower()}")
        did.append(_send(side, Sale(order_id_of(name), line, shares)))
    found, held = side.check(), book.positions(side.root)
    if found or held:
        raise ValueError(f"the account is not as found: the book holds {held}; the check: {found}")
    return "; ".join(did) or "nothing to put back"


def _steps(run: Plan) -> tuple[tuple[str, Callable[[Side], str | None]], ...]:
    """The run's steps, each with its name: what it answers, or nothing beyond having been done."""
    return (
        ("a rejection", lambda side: _send(side, run.refusal)),
        ("a market buy at the open, its stop resting", lambda side: _send(side, run.first)),
        ("a sale, the stop cancelled", lambda side: _send(side, run.sale)),
        ("a buy of the desk's size, a part fill if given", lambda side: _send(side, run.second)),
        ("the stop triggered", lambda side: side.fall(run.second)),
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


def pretend(run: Plan) -> dict[str, str]:
    """The run at the pretend broker: the sizing prices, a refusal, a fall to the stop."""
    today, buy, no = run.today, run.second, run.refusal
    bars: dict[Line, tuple[Bar, ...]]
    bars = {order.line: (Bar(today, *(order.price,) * 4, 0),) for order in (no, buy)}
    bars[buy.line] += (Bar(today + DAY, buy.price, buy.price, buy.stop, buy.price, 0),)
    broker = Pretend(bars, {no.line.symbol: Fault.REJECT})
    broker.open(today)
    said: dict[str, str] = {}
    with TemporaryDirectory() as scratch:
        side = Side(Path(scratch), broker, lambda: (), lambda _: broker.open(today + DAY))
        live(side, run, said.__setitem__)
    return said


def _raised(side: placing.Paper, root: Path, listed: Listing, wait: Wait) -> Fall:
    """THE REAL STOP MADE TO SELL: the line's one stop is put above the price the buy just
    paid (ABOVE), by the adapter's own rule (Paper.settle), and the account read each second
    until the shares are gone; WAITS seconds unsold is an error. SOLD OR NOT, the line is then
    left under the buy's own stop for what is still held, or under none: no stop stays above
    the market for a sale to meet, and none rests with no share behind it."""

    def fall(order: Order) -> None:
        paid = [fill.price for fill in book.fills(root) if fill.order_id == order.order_id]
        held, stops = placing.on(paper.read(), listed)
        if not (paid and held):
            raise ValueError(f"{order.order_id}: no share of it is held for a stop to sell")
        name, above = f"{order.order_id}-stop", listed.floor(max(paid) * ABOVE)
        try:
            side.settle(listed, held, stops, placing.Stop(held, above, name))
            for _ in range(WAITS):
                if not placing.on(paper.read(), listed)[0]:
                    return
                wait(1)
            raise TimeoutError(f"{name}: put above the market, it has not sold in {WAITS} seconds")
        finally:
            held, stops = placing.on(paper.read(), listed)
            back = placing.Stop(held, listed.floor(order.stop), name) if held else None
            side.settle(listed, held, stops, back)

    return fall


def _recorded(root: Path, market: str, today: date) -> str | None:
    """Why the market's run is not made again: a whole one is on record, or today's is."""
    for path in sorted(root.glob(f"trades-{market}-*.csv")):
        with path.open(newline="", encoding="utf-8") as kept:
            rows = list(csv.reader(kept))
        if rows[:1] != [list(HEAD)]:
            raise ValueError(f"{path}: not a record of the conformance trades, so nothing is sent")
        if rows[-1][1:3] == [WHOLE, "whole"] or path.stem.endswith(f"{today:%Y%m%d}"):
            return f"its run is already recorded in {path}"
    return None


def _barred(root: Path, market: str, refused: Line, now: datetime) -> tuple[bool, str] | None:
    """Why no run is begun now, and whether that is all well; None when one may begin."""
    venue, today, hours = MARKETS[market], now.date(), venues.open_at(MARKETS[market], now)
    if hours is None or now >= hours.close or not venues.sessions(refused.venue, today, today):
        return True, NOTHING.format(market, f"{VENUES[venue]} is shut, or the rejection's market")
    if why := _recorded(root, market, today):
        return True, NOTHING.format(market, why)
    known, killed = gateway.known(now), book.killed(root) or book.killed(root.parent / command.ROOT)
    if not known or killed:
        return False, BARRED.format(market) + (killed or known.words)
    return None


def trade(
    root: Path, market: str, clock: Callable[[], datetime], wait: Wait = time.sleep
) -> tuple[bool, str]:
    """THE COMMAND: whether all is well, and its one line (when, the module's words say)."""
    now, refused = clock(), next(line for line in LINES if line.retail is False)
    if barred := _barred(root, market, refused, now):
        return barred
    today, fits = now.date(), (MARKETS[market], 1, True)  #: the venue's own, plain, open to retail
    kill.drill(root, now)  #: no order on a day the switch was not seen to work: raised if broken
    listings = listing.read(LINES)
    if found := (*(clearance.check(root, now).found or ()), *book.positions(root)):
        return False, f"{BARRED.format(market)}the paper account is not quiet: {'; '.join(found)}"
    listed = {x.line: x for x in listings.values() if isinstance(x, Listing)}
    plain = [line for line in listed if (line.venue, line.leverage, line.retail) == fits]
    run = plan(plain, refused, today, command.rates(root, today))
    beside, broker = pretend(run), placing.Paper(listings, root, clock)
    fall = _raised(broker, root, listed[run.second.line], wait)
    side = Side(root, broker, lambda: clearance.check(root, clock()).found, fall)
    record, rows = root / f"trades-{market}-{today:%Y%m%d}.csv", [HEAD]

    def note(step: str, real: str) -> None:
        rows.append((clock().isoformat(), step, real, beside.get(step, "")))
        book._write(record, rows)

    try:
        failed = live(side, run, note)
    except BaseException:  #: whatever stopped the run, the account is still put back
        _leave(side, run)
        raise
    note(WHOLE, f"{FAILED}at: {'; '.join(failed)}" if failed else "whole")
    counts = (market, len(beside) - len(failed), len(beside), run.second.line.symbol, record)
    return not failed, DONE.format(*counts) + AMISS.format("; ".join(failed)) * bool(failed)


def main(
    argv: Sequence[str],
    env: Mapping[str, str] = os.environ,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> int:
    """THE COMMAND LINE: its one line of answer printed, and 0 when all is well."""
    root = Path(env["KESTREL2_DATA"]) / ROOT
    if list(argv) not in [["--conformance", m] for m in MARKETS] or not root.is_absolute():
        raise SystemExit("python -m desk.paper --conformance london|us, KESTREL2_DATA a whole path")
    paper.CLIENT = (
        CLIENT  #: this process is the conformance desk's, at the door and in its readings
    )
    good, line = trade(root, argv[1], clock)
    print(line)  # noqa: T201 - the command's answer to whoever asked
    return int(not good)
