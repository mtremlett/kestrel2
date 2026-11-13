"""broker: fills at the open under its own ids, a stop left resting, every fault stated."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from desk.broker import Crash, Disconnected, Fault, Fill, Pretend
from desk.lines import Line
from desk.orders import Order, Sale
from desk.store import Bar

A, B = Line("A", "LSE", "GBP", 1), Line("B", "US", "USD", 1)
MON, TUE, WED = date(2025, 11, 10), date(2025, 11, 11), date(2025, 11, 12)


#: Each day: its open, then its low; high and close a pound over the open. B has no Tuesday.
DAYS = {A: ((MON, 50, 49), (TUE, 48, 44), (WED, 40, 39)), B: ((MON, 20, 19), (WED, 18, 17))}
ARCHIVE = {
    line: tuple(Bar(d, Decimal(o), c := Decimal(o + 1), Decimal(lo), c, 1) for d, o, lo in x)
    for line, x in DAYS.items()
}


def _order(order_id: str, line: Line = A, quantity: int = 10, stop: str = "45") -> Order:
    return Order(order_id, line, quantity, Decimal(50), Decimal(1), Decimal(stop))


def _broker(faults: dict[str, Fault] | None = None, *orders: Order) -> Pretend:
    broker = Pretend(ARCHIVE, faults or {})
    broker.open(MON)
    for order in orders:
        broker.place(order)
    return broker


def test_a_buy_fills_at_the_open_under_the_brokers_id_and_leaves_its_stop() -> None:
    broker = _broker()
    report, second = (broker.place(o) for o in (_order("o-1"), _order("o-2", B, 3, "15")))
    (fill,), (other,) = report.fills, second.fills
    assert report.reason is None and fill == Fill(
        fill.execution_id, "o-1", "A", 10, Decimal(50), MON
    )
    assert fill.execution_id not in {"o-1", other.execution_id} and broker.fills() == (fill, other)
    assert broker.positions() == {"A": 10, "B": 3} and broker.report("o-9") is None
    assert broker.resting_stops() == {"A": (10, Decimal(45)), "B": (3, Decimal(15))}
    assert broker.report("o-1") == report and broker.place(_order("o-3", A, 5, "47")).reason is None
    assert broker.resting_stops()["A"] == (15, Decimal(47)), "one stop covers the whole line"
    again = _broker(None, _order("o-1"), _order("o-2", B, 3, "15"), _order("o-3", A, 5, "47"))
    assert again.fills() == broker.fills(), "the same orders gave other fills"


def test_each_fault_is_stated_and_hits_only_the_symbols_first_order() -> None:
    broker = _broker({"A": Fault.REJECT, "B": Fault.PARTIAL})
    rejected, partial = broker.place(_order("o-1")), broker.place(_order("o-2", B, 9, "15"))
    assert rejected.fills == () and rejected.reason and partial.reason
    assert broker.positions() == {"B": 4} and broker.resting_stops() == {"B": (4, Decimal(15))}
    assert broker.place(_order("o-3")).reason is None, "a fault outlived the first order"
    broker = _broker({"A": Fault.DISCONNECT})
    with pytest.raises(Disconnected, match="o-1"):
        broker.place(_order("o-1"))
    assert broker.place(_order("o-1")).reason is None and broker.submitted() == ("o-1",)
    broker = Pretend(ARCHIVE, {"A": Fault.CRASH})  #: a fault waits for an order that meets a market
    assert broker.place(_order("o-0")).reason, "it filled before the market opened"
    broker.open(MON)
    with pytest.raises(Crash):
        broker.place(_order("o-1"))
    duplicate = broker.place(_order("o-1"))
    assert duplicate.reason and broker.submitted() == ("o-0", "o-1", "o-1"), "duplicate silent"
    assert broker.positions() == {"A": 10}, "the order was lost in the crash, or filled twice"
    assert broker.report("o-1").fills == broker.fills()  # type: ignore[union-attr]
    with pytest.raises(ValueError, match="Z"):
        Pretend(ARCHIVE, {"Z": Fault.REJECT})


def test_a_stop_sells_at_its_level_or_a_gapped_open_even_on_the_day_of_its_buy() -> None:
    broker = _broker(None, _order("o-1", A, 10, "45"), _order("o-2", B, 3, "18.5"))
    broker.open(TUE)
    (sold,) = broker.fills()[2:]  #: B has no market on Tuesday: its stop waits, and no buy fills
    assert (sold.order_id, sold.quantity, sold.price) == ("o-1-stop", -10, Decimal(45))
    assert broker.place(_order("o-4", B, 3, "15")).reason and broker.positions() == {"B": 3}
    assert broker.place(_order("o-3", stop="47")).reason is None and broker.positions() == {"B": 3}
    broker.open(WED)
    assert broker.positions() == {} == broker.resting_stops() and broker.fills()[-1].price == 18
    broker.inject("B", 7)
    assert (broker.positions(), broker.resting_stops(), len(broker.fills())) == ({"B": 7}, {}, 6)
    with pytest.raises(ValueError, match="2025-11-11"):
        broker.open(TUE)


def test_a_sale_fills_at_the_open_and_takes_its_shares_off_the_lines_stop() -> None:
    broker = _broker({"A": Fault.PARTIAL}, _order("o-1", B, 3, "15"), _order("o-2", A, 20))
    (fill,) = broker.place(Sale("s-1", A, 4)).fills  #: the fault was the buy's: half of 20
    assert (fill.quantity, fill.price, fill.day) == (-4, Decimal(50), MON)
    assert broker.positions() == {"A": 6, "B": 3} and broker.resting_stops()["A"] == (
        6,
        Decimal(45),
    )
    assert broker.place(Sale("s-2", A, 6)).reason is None and broker.positions() == {"B": 3}
    broker.open(TUE)  #: A's day falls through 45: no stop is left to sell what was sold
    assert len(broker.fills()) == 4 and broker.resting_stops() == {"B": (3, Decimal(15))}
