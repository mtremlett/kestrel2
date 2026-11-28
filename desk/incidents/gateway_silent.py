"""incident gateway_silent: SimCity's scenario for one real night (see `git log`, DECISIONS)."""

from __future__ import annotations

from datetime import UTC, date, datetime, time
from decimal import Decimal
from typing import TYPE_CHECKING

from desk import bars, book, conformance_parts, keeper, venues
from desk.broker import Pretend
from desk.conformance_parts import Side
from desk.keeper_rotate import Kept, record
from desk.lines import LINES, YARDSTICK
from desk.orders import Order
from desk.running_notes import DAY
from desk.store import Bar

if TYPE_CHECKING:
    from desk.simcity import _Life

STOP_SILENT = (
    "a gateway silent when the stop is to fire fails that step by name and puts the account back"
)


def gateway_silent(life: _Life, on: date) -> bool:
    """The gateway says nothing when the conformance run's stop is to fire (17 November,
    "conformance-us", TimeoutError). The step must be recorded as failed, naming TimeoutError;
    the last step must still put the account back, so neither the book nor the broker holds a
    share and no order rests. False on a day London is shut: still owed."""
    if on not in venues.sessions(YARDSTICK.venue, on, on):
        life.live(on)  #: London keeps a holiday on a US session: no run is planned, still owed
        return False
    held = [x for x in life.begun(on) if x.venue == YARDSTICK.venue]
    line = next(x for x in LINES if x.retail and x.leverage == 1 and x.venue == YARDSTICK.venue)
    whole = life.market[held[0]]  #: the world's bars on a line the desk's own list knows
    home = life.desk / f"silent-{on}"
    with bars.writing(home / keeper.HOT) as round_:
        round_.daily(line, [b for b in whole if b.day < on])
    record(
        home / keeper.DAILY / line.venue,
        Kept(on, datetime.combine(on, time(), UTC), 1, {}, frozenset()),
    )
    refused = next(x for x in LINES if x.retail is False)
    run = conformance_parts.plan([line], refused, on, {line.currency: Decimal(1)}, "0000", home)
    price = run.second.price
    world = Pretend({line: (Bar(on, *(price,) * 4, 0), Bar(on + DAY, *(price,) * 4, 0))}, {})
    world.open(on)

    def quiet(_order: Order) -> str:
        raise TimeoutError("timed out")

    said: dict[str, str] = {}
    side = Side(home, world, lambda: (), quiet)
    failed = conformance_parts.live(side, run, said.__setitem__)
    answer = said.get(conformance_parts.TRIGGER, "")
    left = book.positions(home) or dict(world.holdings()) or world.stops()
    life.promise(
        STOP_SILENT, failed == [conformance_parts.TRIGGER] and "TimeoutError" in answer and not left
    )
    life.live(on)
    return True
