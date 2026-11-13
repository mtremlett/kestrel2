"""kill: one command stops every new order and cancels the working ones, the stops stay, the
desk says so, and only a drill that kept every promise is on the record."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from desk import book, kill
from desk.broker import Crash, Fault, Pretend
from desk.lines import Line
from desk.orders import Order, Refused, Sale, Settings
from desk.store import Bar

A, B, C = (Line(symbol, "LSE", "GBP", 1) for symbol in "ABC")
MON, TUE, ROOM = date(2025, 11, 10), date(2025, 11, 11), Settings(Decimal(10_000))
NOW, LATER = (datetime(2025, 11, 10, hour, 30, tzinfo=UTC) for hour in (9, 15))
WEEK = {
    line: tuple(Bar(on, Decimal(50), Decimal(51), Decimal(49), Decimal(51), 1) for on in (MON, TUE))
    for line in (A, B, C)
}


def _buy(root: Path, broker: Pretend, order_id: str, line: Line) -> book.Sent:
    return book.send(root, broker, Order(order_id, line, 10, *map(Decimal, (50, 1, 45))), ROOM)


def _desk(root: Path) -> Pretend:
    """A is held under its stop; B's order is left working by a desk that died."""
    broker = Pretend(WEEK, {"B": Fault.STRAND})
    broker.open(MON)
    _buy(root, broker, "o-1", A)
    with pytest.raises(Crash):
        _buy(root, broker, "o-2", B)
    return broker


def test_one_command_stops_new_orders_cancels_the_working_ones_and_says_so(tmp_path: Path) -> None:
    broker = _desk(tmp_path)
    said = kill.pull(tmp_path, broker, NOW, "the market is falling")
    assert said == kill.Killed(NOW, "the market is falling", ("o-2",), (("A", 10),), ())
    for part in ("ON", "2025-11-10 09:30 UTC", "the market is falling", "o-2", "A 10", "its stop"):
        assert part in said.words(), f"the desk did not say {part!r}: {said.words()}"
    with pytest.raises(Refused, match="o-3: .*kill switch"):
        _buy(tmp_path, broker, "o-3", C)
    with pytest.raises(Refused, match="s-1: .*kill switch"):
        book.send(tmp_path, broker, Sale("s-1", A, 10), ROOM)
    broker.open(TUE)
    assert broker.holdings() == (("A", 10),) == broker.stops(), "B filled, or A's stop was taken"
    assert kill.pull(tmp_path, broker, LATER, "pulled twice").cancelled == (), "nothing was left"
    kill.release(tmp_path, LATER, "his word")
    assert _buy(tmp_path, broker, "o-3", C).filled == 10, "released, the desk still sent nothing"
    with pytest.raises(ValueError, match="not on"):
        kill.release(tmp_path, LATER, "released twice")
    broker.cancel_stop("A")  #: a holding with no stop is named, never passed over
    bare = kill.pull(tmp_path, broker, LATER, "again")
    assert bare.differ == ("A",) and "NOT the broker's on A" in bare.words()


def test_the_switch_is_on_before_the_broker_is_asked_so_a_dead_line_still_stops_the_desk(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    broker = _desk(tmp_path)

    def dead() -> tuple[str, ...]:
        raise ConnectionError("the broker does not answer")

    monkeypatch.setattr(broker, "cancel", dead)
    with pytest.raises(ConnectionError):  #: stated, never a quiet "nothing was working"
        kill.pull(tmp_path, broker, NOW, "the line is down")
    with pytest.raises(Refused, match="the line is down"):
        _buy(tmp_path, broker, "o-3", C)
    assert broker.submitted() == ("o-1", "o-2")


def test_a_drill_that_keeps_every_promise_is_on_the_record_for_a_month_and_no_other_is(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert not kill.drilled(tmp_path, MON)
    kept = kill.drill(tmp_path, NOW)
    assert len(kept) == 8 and all("DRILL" not in promise for promise in kept)
    assert book.killed(tmp_path) is None, "the drill stopped the real desk"
    assert [day for day in range(-1, 33) if kill.drilled(tmp_path, MON + timedelta(day))] == list(
        range(32)
    ), "a drill counts from its own day for 31 more"
    monkeypatch.setattr(Pretend, "cancel", lambda _: ())  #: a broker that cancels nothing
    with pytest.raises(kill.Failed, match="cancelled.*never filled"):
        kill.drill(tmp_path / "broken", NOW)
    assert not kill.drilled(tmp_path / "broken", MON), "a broken drill was recorded as a drill"
