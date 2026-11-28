"""incident silent: SimCity's scenario for one real night (see `git log`, DECISIONS)."""

from __future__ import annotations

from datetime import UTC, date, datetime, time
from typing import TYPE_CHECKING

from desk import book, kill
from desk.broker import Report
from desk.orders import Order, Sale

if TYPE_CHECKING:
    from desk.simcity import _Life

SILENT = "a broker silent after an order is sent: the kill switch is on, the alarm names the order"


def silent(life: _Life, on: date) -> None:
    """The broker says nothing to the first order it is sent (18 November, "timed out"). The
    desk must not guess what became of it: the kill switch goes on, the day ends in the alarm
    naming the order and the silence, nothing is booked; released, the same day then runs."""
    at = datetime.combine(on, time(7), UTC)
    failed = list[str]()

    def mute(order: Order | Sale) -> Report:
        failed.append(order.order_id)
        raise TimeoutError("timed out")

    life.pretend.place = mute  # type: ignore[method-assign]  # the world's broker, told to go quiet
    try:
        life.live(on)
    except book.Alarm as alarm:  #: the send path's own word that it does not know the order
        named = bool(failed) and failed[0] in str(alarm) and "timed out" in str(alarm)
        life.promise(SILENT, named and book.killed(life.desk) is not None)
        kill.release(life.desk, at, "SimCity releases it")
        del life.pretend.place  # the world's broker speaks again
        life.live(on)
    else:
        del life.pretend.place
        life.promise(SILENT, not failed)  #: no order was sent: nothing to be silent to
