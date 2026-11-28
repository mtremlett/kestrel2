"""incident dropped: SimCity's scenario for one real night (see `git log`, DECISIONS)."""

from __future__ import annotations

from datetime import UTC, date, datetime, time
from typing import TYPE_CHECKING

from desk import book, halt
from desk.orders import Order

if TYPE_CHECKING:
    from desk.simcity import _Life

DROPPED = "a halt takes down a buy still working at the broker, and leaves every stop resting"


def dropped(life: _Life, on: date) -> None:
    """A buy is working at the broker when a halt is called (the 19 November VHYG buy). The halt
    must cancel it by its id and leave the stops resting; the day then runs, no order left."""
    held = book.positions(life.desk)
    line = next(x for x in sorted(life.market, key=lambda x: x.symbol) if x.symbol not in held)
    price = life.market[line][-1].close
    order = Order(f"drop-{line.symbol}", line, 1, price, life.rates[line.currency], price / 2)
    life.pretend._working[order.order_id] = order  # noqa: SLF001 - a buy the world's broker holds
    stops, at = life.pretend.stops(), datetime.combine(on, time(7), UTC)
    stopped = halt.stop(life.desk, life.pretend, at, "SimCity halts a working buy")
    life.promise(DROPPED, stopped.cancelled == (order.order_id,) and life.pretend.stops() == stops)
    halt.lift(life.desk, stopped.halt, at, "SimCity lifts it")
    life.live(on)
