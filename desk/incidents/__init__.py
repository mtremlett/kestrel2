"""incidents - SimCity's scenarios met by a real night, one module each: its title and its function.
This registry is the one list: a new incident is its own file and a line here."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from typing import TYPE_CHECKING

from desk.incidents import (
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

if TYPE_CHECKING:
    from desk.simcity import _Life

Event = tuple[str, Callable[["_Life", date], object]]
#: drawn on a morning the desk is fit for it, the seed's order; the first is the keeper's stale one
DRAWN: tuple[Event, ...] = (
    (stale.STALE, stale.stale),
    (hole.HOLE, hole.hole),
    (beside.LEFT, beside.beside),
    (cancelled.CANCELLED, cancelled.cancelled),
    (parked.PARKED, parked.parked),
    (deaf.DEAF, deaf.deaf),
    (unheld.UNHELD, unheld.unheld),
    (unbarred.UNBARRED, unbarred.unbarred),
    (locked.LOCKED, locked.locked),
    (minutes.LIVE, minutes.minutes),
    (silent.SILENT, silent.silent),
    (slow.SLOW, slow.slow),
    (gateway_silent.STOP_SILENT, gateway_silent.gateway_silent),
)
LONE: Event = (unreachable.SHUT, unreachable.unreachable)  #: lived once, on a plain morning
