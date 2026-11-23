"""conformance - THE CONFORMANCE TRADES, AS A COMMAND (his request, 14 November 2026):

    python -m desk.paper --conformance london|us [--soak]
One run for each market, in its hours, on the PAPER account, beside the desk's own book:
the real broker is given the orders the desk's day will give it, through the desk's own send
path (book.send), and each real result is recorded beside the pretend broker's
(broker.Pretend) in `conformance` under the folder the environment names (KESTREL2_DATA).
It is A DESK OF ITS OWN, with a record and a client id of its own (CLIENT): whose an order
or a fill is, is told by the client that placed it, so neither desk takes the other's fills
into its ledger or cancels its orders.

THE STEPS (`_steps`), on the venue's plain line that traded the most money in its last
session: a refusal (one share of a line the instrument master says no retail customer may
buy, which the desk's gate, day._buy, refuses before it leaves: R-PAPER-14; Monday's tape, 16
November, is the record of the real broker's rejection, "Rejected: no retail trading", and no
order is sent to observe it again); a market buy of one share, its stop resting; its sale, the
stop cancelled first (R-MONEY-17: no sale goes while a stop rests); a buy of the desk's own
size (a part fill, if given, shows in its fills); that buy's stop made to sell
(the real one is put above the market, `_raised`, so IBKR fills it as a stop; the pretend one is
priced from that fill); and the account left as found. Each step's two sides must name the SAME
action, judged on fills and holdings (a stop fill against a stop fill); the broker's status words
("Cancelled by Trader": the run's own swap of the buy's stop for the raised one) are
recorded, not judged; a step whose sides differ fails the run. A step that fails is recorded
as failed, in the error's words; none after it is tried but the last, which puts the account back.

BESIDE THE DESK (R-RUNNER-201): the run is looped every thirty minutes, each run its own record.
It trades only a line the desk neither holds nor has an order working on; the desk's holdings
and its client's orders are not seen by this run's door (its Door's apart), so its day check and its
quiet read the account as this desk's own; it ends flat in its own lines, and a desk holding
found changed at its end is named a FIRST-LIGHT FAULT. It never begins within five minutes of
a desk round, or in one (ROUNDS): the desk's round has the account.

NOTHING IS DONE, code 0: the market is not in continuous trading, or the rejection's is shut
today, or a desk round is near. NOTHING IS SENT, code not 0, unless the gateway is ready, both
desks' kill switches off, this one's drilled, and the account QUIET of this desk's own: nothing
of its own held, no order of its own open."""

from __future__ import annotations

import os
import time
from collections.abc import Callable, Mapping, Sequence
from contextlib import suppress
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from functools import partial
from pathlib import Path

from desk import (
    book,
    clearance,
    command,
    gateway,
    kill,
    listing,
    paper,
    placing,
    venues,
)
from desk import conformance_tape as tape
from desk.conformance_parts import (
    FAILED as FAILED,
)
from desk.conformance_parts import (
    ROOM as ROOM,
)
from desk.conformance_parts import (
    TRIGGER as TRIGGER,
)
from desk.conformance_parts import (
    UNTRIED as UNTRIED,
)
from desk.conformance_parts import (
    Fall as Fall,
)
from desk.conformance_parts import (
    Plan as Plan,
)
from desk.conformance_parts import (
    Side as Side,
)
from desk.conformance_parts import (
    _leave as _leave,
)
from desk.conformance_parts import (
    _send as _send,
)
from desk.conformance_parts import (
    live as live,
)
from desk.conformance_parts import (
    plan as plan,
)
from desk.conformance_parts import (
    pretend as pretend,
)
from desk.ended import action, reasons
from desk.lines import LINES, Line
from desk.listing import Listing
from desk.orders import Order
from desk.running import VENUES

MARKETS = {"london": "LSE", "us": "US"}  #: the command's word for each venue
CLIENT = 223  #: the conformance desk's own client id at the gateway: the desk's is paper.DESK
ROOT, HEAD = "conformance", ("at", "step", "real", "pretend", "it said")
WHOLE = "the run"
ABOVE, WAITS = Decimal("1.05"), 30  #: a stop this far above the price paid; its seconds to sell
Wait = Callable[[float], None]  #: what lets a second pass
NOTHING, BARRED = "CONFORMANCE {}: nothing done, {}.", "CONFORMANCE {} NOT BEGUN, nothing sent: "
DONE = "CONFORMANCE {}: {} of {} steps done on {}, each recorded beside the pretend broker's in {}."
GIVEN = "the broker gave no reason"  #: an order it cancelled is never recorded with none
ROUNDS = tape.ROUNDS  #: a desk round's hours, where history.py reads them
#: Seen 16 November 2026 at the paper broker: a stop put above the market rests PreSubmitted
#: and does not sell; only a fall to its level fires one. The step records that, it does not fail.
RESTED = "it rested PreSubmitted"
STILL = "{}: put above the market " + RESTED + ", not sold in {} seconds"
SEEDED = " Its line drawn by seed {}."  #: a soak's round: the seed that drew its line
AMISS = " FAILED: {}. A later day tries again; {}."
AS_FOUND, NOT_AS_FOUND = (
    "the account left as found",
    "the last step named, THE ACCOUNT IS NOT AS FOUND",
)


def _raised(side: placing.Paper, root: Path, listed: Listing, wait: Wait, door: paper.Door) -> Fall:
    """THE REAL STOP MADE TO SELL: the line's one stop is put above the price the buy just
    paid (ABOVE), by the adapter's own rule (Paper.settle), and the account read each second
    until the shares are gone; WAITS seconds unsold is an error. SOLD OR NOT, the line is then
    left under the buy's own stop for what is still held, or under none: no stop stays above
    the market for a sale to meet, and none rests with no share behind it."""

    def fall(order: Order) -> str | None:
        paid = [fill.price for fill in book.fills(root) if fill.order_id == order.order_id]
        held, stops = placing.on(paper.read(door), listed, door)
        if not (paid and held):
            raise ValueError(f"{order.order_id}: no share of it is held for a stop to sell")
        name, above = f"{order.order_id}-stop", listed.floor(max(paid) * ABOVE)
        try:
            with suppress(placing.Unprotected):  #: ended as it was sent: sold, if the shares go
                side.settle(listed, held, stops, placing.Stop(held, above, name))
            for _ in range(WAITS):
                if not placing.on(paper.read(door), listed, door)[0]:
                    return None
                wait(1)
            return STILL.format(name, WAITS)
        finally:
            held, stops = placing.on(paper.read(door), listed, door)
            back = placing.Stop(held, listed.floor(order.stop), name) if held else None
            side.settle(listed, held, stops, back)

    return fall


def why(now: datetime) -> tuple[bool, str]:
    """THE READ: each cancelled order of the day and why, as client CLIENT, read-only; never
    in a desk round's hours."""
    door = paper.Door(CLIENT)
    if tape.round_at(now, 0):
        return False, "CONFORMANCE WHY: not read now, a desk round runs 08:00-08:30 and 14:30-15:00"
    said = [f"{ref}: {words or GIVEN}" for ref, words in reasons(door).items()]
    return True, "\n".join(said) or "CONFORMANCE WHY: no order was cancelled today"


def _barred(
    root: Path, market: str, refused: Line, now: datetime, door: paper.Door
) -> tuple[bool, str] | None:
    """Why no run is begun now, and whether that is all well; None when one may begin."""
    venue, today, hours = MARKETS[market], now.date(), venues.open_at(MARKETS[market], now)
    if hours is None or now >= hours.close or not venues.sessions(refused.venue, today, today):
        return True, NOTHING.format(market, f"{VENUES[venue]} is shut, or the rejection's market")
    if tape.round_at(now, tape.LEAD):
        return True, NOTHING.format(market, "a desk round runs 08:00-08:30 and 14:30-15:00")
    known, killed = (
        gateway.known(now, door=door),
        book.killed(root) or book.killed(root.parent / command.ROOT),
    )
    if not known or killed:
        return False, BARRED.format(market) + (killed or known.words)
    return None


def _noted(
    root: Path,
    record: Path,
    run: Plan,
    beside: dict[str, str],
    clock: Callable[[], datetime],
    door: paper.Door,
) -> tuple[list[tuple[str, ...]], list[str], Callable[[str, str], None]]:
    """The record's rows, the steps whose two sides did different things (the run's fault), and
    the note that writes a step's row: the pretend side priced at the real stop's fill."""
    rows, differ = list[tuple[str, ...]]([HEAD]), list[str]()

    def note(step: str, real: str) -> None:
        try:
            cancelled = [
                f"{ref}: {words or GIVEN}" for ref, words in reasons(door).items() if ref in real
            ]
        except TimeoutError as slow:  # the reason is a note; a slow answer never ends the round
            cancelled = [f"reason not read: {slow}"]
        stopped = [f.price for f in book.fills(root) if f.order_id == f"{run.second.order_id}-stop"]
        if step == TRIGGER and (stopped or RESTED in real):
            beside.update(pretend(run, stopped[-1] if stopped else None, not stopped))
        rows.append((clock().isoformat(), step, real, beside.get(step, ""), "; ".join(cancelled)))
        book._write(record, rows)
        broken = any(row[2].startswith((FAILED, UNTRIED)) for row in rows[1:])  #: compared only
        same = action(real, "") == action(beside.get(step, ""), "")
        if not (broken or same or step == WHOLE):
            differ.append(step)

    return rows, differ, note


def _moved(door: paper.Door, held: Mapping[str, Decimal]) -> str:
    """Said when a desk holding, as the run began, is not as it was: a FIRST-LIGHT FAULT."""
    now = {h.name: h.shares for h in paper.whole(door).holdings}
    moved = [f"{n} {was} -> {now.get(n, 0)}" for n, was in held.items() if now.get(n, 0) != was]
    return f" FIRST-LIGHT FAULT: the desk's holdings changed: {'; '.join(moved)}." * bool(moved)


def trade(
    root: Path,
    market: str,
    clock: Callable[[], datetime],
    wait: Wait = time.sleep,
    seeded: bool = False,
) -> tuple[bool, str]:
    """THE COMMAND: whether all is well, and its one line (when, the module's words say). A soak's
    run is SEEDED: its line drawn by its moment in whole seconds, said, so it can be run again."""
    now, refused = clock(), next(line for line in LINES if line.retail is False)
    seed, home = (int(now.timestamp()) if seeded else None), root.parent
    door = paper.Door(CLIENT)  #: this run's own client; its apart set once the desk's share is read
    if barred := _barred(root, market, refused, now, door):
        return barred
    today, fits = now.date(), (MARKETS[market], 1, True)  #: the venue's own, plain, open to retail
    kill.drill(root, now)  #: no order on a day the switch was not seen to work: raised if broken
    listings = listing.read(LINES, door)
    held, busy = tape.share(paper.whole(door))
    door = replace(door, apart=paper.Apart(frozenset(held)))  #: the desk's share is not this run's
    if found := (*(clearance.check(root, now, door).found or ()), *book.positions(root)):
        return False, f"{BARRED.format(market)}the paper account is not quiet: {'; '.join(found)}"
    listed = {x.line: x for x in listings.values() if isinstance(x, Listing)}
    plain = [
        line
        for line in listed
        if (line.venue, line.leverage, line.retail) == fits
        if listed[line].contract not in busy and paper.own(line) not in held
    ]
    run = plan(plain, refused, today, command.rates(home, today), f"{now:%H%M}", home, seed)
    beside, broker = pretend(run), placing.Paper(listings, root, clock, door)
    fall = _raised(broker, root, listed[run.second.line], wait, door)
    side = Side(root, broker, lambda: clearance.check(root, clock(), door).found, fall)
    record = root / f"trades-{market}-{now:%Y%m%d-%H%M}.csv"
    rows, differ, note = _noted(root, record, run, beside, clock, door)
    try:
        failed = live(side, run, note)
    except BaseException:  #: whatever stopped the run, the account is still put back
        _leave(side, run)
        raise
    failed += [
        f"{step} (THE TWO SIDES DID DIFFERENT THINGS)" for step in differ if step not in failed
    ]
    note(WHOLE, f"{FAILED}at: {'; '.join(failed)}" if failed else "whole")
    counts = (market, len(beside) - len(failed), len(beside), run.second.line.symbol, record)
    state = NOT_AS_FOUND if rows[-2][2].startswith(FAILED) else AS_FOUND  #: the last step's row
    fault = _moved(door, held)
    said = DONE.format(*counts) + SEEDED.format(seed) * seeded
    return not (failed or fault), said + AMISS.format("; ".join(failed), state) * bool(
        failed
    ) + fault


def main(
    argv: Sequence[str],
    env: Mapping[str, str] = os.environ,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> int:
    """THE COMMAND LINE: its one line of answer printed, and 0 when all is well."""
    root = Path(env["KESTREL2_DATA"]) / ROOT
    soaks = list(argv) in [["--conformance", m, "--soak"] for m in MARKETS]  #: one hourly round
    asks = soaks or list(argv) in [["--conformance", m] for m in MARKETS]
    if not (asks or list(argv) == ["--conformance-why"]) or not root.is_absolute():
        raise SystemExit("python -m desk.paper --conformance london|us|-why, KESTREL2_DATA whole")
    go = (
        partial(tape.soak, trade=partial(trade, seeded=True)) if soaks else trade
    )  #: a soak records its round
    good, line = go(root, argv[1], clock) if asks else why(clock())
    print(line)  # noqa: T201 - the command's answer to whoever asked
    return int(not good)
