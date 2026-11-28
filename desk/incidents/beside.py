"""incident beside: SimCity's scenario for one real night (see `git log`, DECISIONS)."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from desk import book

if TYPE_CHECKING:
    from desk.simcity import _Life

LEFT = "shares the book lacks rest at the broker under a stop"

SOLD = "shares the book lacks, under a stop at the broker, are left under it and never sold"


def beside(life: _Life, on: date) -> None:
    """Shares the book never saw rest at the broker under their own stop. The desk must not
    sell them on top of the stop (that sells twice): after the day the broker holds them
    all, still under the stop. A hand then clears them."""
    free = sorted({x.symbol for x in life.market} - set(book.positions(life.desk)))
    symbol = life.rng.choice(free)
    level = min(b.low for x, bars in life.market.items() if x.symbol == symbol for b in bars)
    shares = life.rng.randint(1, 50)
    life.pretend.inject(symbol, shares)
    life.pretend.put_stop_back(symbol, level / 2)
    life.live(on)
    held = dict(life.pretend.holdings()).get(symbol, 0)
    life.promise(SOLD, held == shares and dict(life.pretend.stops()).get(symbol, 0) == shares)
    life.pretend.cancel_stop(symbol)  # a hand clears the stranger, so the world goes on
    life.pretend.inject(symbol, -held)
