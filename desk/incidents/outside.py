"""incident outside: SimCity's scenario for one real night (see `git log`, DECISIONS)."""

from __future__ import annotations

from dataclasses import replace
from datetime import date
from typing import TYPE_CHECKING

from desk import book
from desk.lines import YARDSTICK

if TYPE_CHECKING:
    from desk.simcity import _Life

OUTSIDE = "a line no ISA can hold is never bought"


def outside(life: _Life, on: date) -> None:
    """Every line but the yardstick and those held is recorded as outside an ISA for the day: no
    buy of such a line reaches the broker (the yardstick's own key is the day's, and is kept)."""
    whole, reached, held = life.market, len(life.pretend.submitted()), book.positions(life.desk)
    barred = {x.symbol for x in whole if x.symbol not in held and x != YARDSTICK}
    life.market = {
        x if x.symbol not in barred else replace(x, isa=False): b for x, b in whole.items()
    }
    life.live(on)
    sent = life.pretend.submitted()[reached:]
    life.promise(OUTSIDE, not any(i.rpartition("-")[2] in barred for i in sent))
    life.market = whole
