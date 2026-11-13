"""THE SEVEN SCENES, as approved by the operator on 13 November 2026 (docs/SCENES.md).

One test per scene, in the scene's own order and words. Each runs on the tiny synthetic
rehearsal data in rehearsal.py with a fixed clock, so it gives the same answer on any
machine, every time.
A scene that is not yet passing must stop at a part of the desk that raises
NotImplementedError; check.py turns any other failure red.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import astuple
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from rehearsal import (
    BAD,
    CLEAN,
    HISTORY,
    LAST,
    LINES,
    SESSIONS,
    SPOILT,
    TODAY,
    WRONG_UNIT,
    before,
)

from desk import book, day, orders, store, strategy
from desk.broker import Crash, Fault, Pretend

# ---------------------------------------------------------------- the money

SETTINGS = orders.Settings(capital=Decimal(10_000))
RATES = {"GBP": Decimal(1), "USD": Decimal("0.79")}  #: pounds per unit, every rehearsal day


def _order(symbol: str) -> orders.Order:
    """Ten shares of a London line at its last close, with its stop at 30."""
    line = next(line for line in LINES if line.symbol == symbol)
    return orders.Order(f"o-{symbol}", line, 10, CLEAN[line][-1].close, Decimal(1), Decimal(30))


def _run_days(root: Path, broker: Pretend, days: Sequence[date]) -> list[day.Record]:
    records = []
    for on in days:
        broker.open(on)
        records.append(day.run(root, before(CLEAN, on), broker, SETTINGS, on, RATES))
    return records


# ---------------------------------------------------------------- the scenes


def test_scene_1_the_days_data_is_clean_or_the_line_is_parked(tmp_path: Path) -> None:
    parked = store.prepare(tmp_path, SPOILT, TODAY)

    assert [(p.symbol, p.day) for p in parked] == [(BAD.symbol, TODAY)]
    assert parked[0].reason.strip(), "a parked line names its reason"
    for line in LINES:
        if line != BAD:
            assert store.read(tmp_path, line.symbol) == CLEAN[line], f"{line.symbol} incomplete"
    kept = store.read(tmp_path, BAD.symbol)
    assert WRONG_UNIT not in kept, "the bad bar reached the store"
    assert [b.day for b in kept] == sorted({b.day for b in kept}), "a date is stored twice"


def test_scene_2_the_decision_cannot_see_the_future(tmp_path: Path) -> None:
    parked = {p.symbol for p in store.prepare(tmp_path, SPOILT, TODAY)}
    trading = [line.symbol for line in LINES if line.symbol not in parked]
    bars = {symbol: store.read(tmp_path, symbol) for symbol in trading}

    every = strategy.decide(bars)
    names = {d.strategy for d in every}
    assert len(trading) == 19 and len(names) == 5
    assert len(every) == len(names) * sum(
        len(b) for b in bars.values()
    ), "a line or one of its own days went unanswered"
    for cut in SESSIONS:
        blind = {s: tuple(bar for bar in b if bar.day <= cut) for s, b in bars.items()}
        assert set(strategy.decide(blind)) == {
            d for d in every if d.day <= cut
        }, f"the decisions up to {cut} changed when the later bars were deleted"


def test_scene_3_a_size_and_a_stop_from_one_number() -> None:
    line = LINES[10]
    buy = strategy.Decision("any", line.symbol, LAST, strategy.Action.BUY)
    price, fx = Decimal("50.25"), Decimal("0.79")  #: dollars, and pounds per dollar

    order = orders.size(buy, line, price, fx, SETTINGS, {})
    assert order.quantity > 0 and (order.line, order.price, order.fx) == (line, price, fx)
    spend = orders.cost(order)
    assert order.quantity * price * fx < spend <= SETTINGS.capital, "pounds, currency cost counted"
    orders.gate(order, SETTINGS, {})

    #: one penny less than this order costs: the sizer and the gate must both move
    less = orders.Settings(capital=spend - Decimal("0.01"))
    assert (
        orders.size(buy, line, price, fx, less, {}).quantity < order.quantity
    ), "sizer did not move"
    with pytest.raises(orders.Refused):
        orders.gate(order, less, {})
    with pytest.raises(TypeError):
        orders.Order("o-1", line, 10, price, fx)  # type: ignore[call-arg]
    for stop in (Decimal(0), price):
        with pytest.raises(ValueError, match="stop"):
            orders.Order("o-1", line, 10, price, fx, stop)


def test_scene_4_the_order_is_sent_and_the_stop_rests_at_the_broker(tmp_path: Path) -> None:
    faults = {
        "L02": Fault.REJECT,
        "L03": Fault.PARTIAL,
        "L04": Fault.DISCONNECT,
        "L06": Fault.CRASH,
    }
    broker = Pretend(CLEAN, faults)
    broker.open(LAST)

    sent: dict[str, book.Sent] = {}
    for symbol in ("L01", "L02", "L03", "L04"):
        sent[symbol] = book.send(tmp_path, broker, _order(symbol), SETTINGS)
    assert sent["L01"].filled == 10 and sent["L01"].reason is None
    assert 0 < sent["L03"].filled < 10
    for symbol in ("L02", "L03", "L04"):
        assert sent[symbol].reason, f"{faults[symbol].value} on {symbol} passed in silence"

    with pytest.raises(orders.Refused):
        book.send(tmp_path, broker, _order("L05"), orders.Settings(capital=Decimal(1)))
    assert "o-L05" not in broker.submitted(), "an order went round the pre-trade gate"

    with pytest.raises(Crash):
        book.send(tmp_path, broker, _order("L06"), SETTINGS)
    book.send(tmp_path, broker, _order("L06"), SETTINGS)  #: the desk restarts and sends again
    assert broker.submitted().count("o-L06") == 1, "an order was sent twice"

    assert book.fills(tmp_path) == broker.fills(), "the ledger is not the broker's fills"
    held = broker.positions()
    assert held["L01"] == 10 and held["L06"] == 10
    assert broker.resting_stops() == {
        s: (n, Decimal(30)) for s, n in held.items()
    }, "a position without its stop, or a stop of the wrong size or level"


def test_scene_5_the_position_is_closed(tmp_path: Path) -> None:
    #: the whole fourteen months: the rules need months of history before they trade
    broker = Pretend(HISTORY, {})
    for on in sorted({bar.day for bars in HISTORY.values() for bar in bars})[1:]:
        broker.open(on)
        day.trade(tmp_path, before(HISTORY, on), broker, SETTINGS, on, RATES)

    trips = book.round_trips(tmp_path, LINES)
    assert trips, "no complete round trip: a buy and a sell of the same line"
    ids = {fill.execution_id for fill in broker.fills()}
    pounds = {line.symbol for line in LINES if line.currency == "GBP"}
    for trip in trips:
        if trip.buy.symbol in pounds:
            assert trip.gross == (trip.sell.price - trip.buy.price) * trip.buy.quantity
        assert trip.buy.symbol == trip.sell.symbol and trip.buy.quantity == -trip.sell.quantity > 0
        assert {trip.buy.execution_id, trip.sell.execution_id} <= ids, "an id not the broker's"
        assert trip.costs > 0 and trip.profit == trip.gross - trip.costs


def test_scene_6_the_book_is_the_brokers(tmp_path: Path) -> None:
    #: every line's first order is rejected: the desk meant to buy and did not
    broker = Pretend(CLEAN, {line.symbol: Fault.REJECT for line in LINES})
    records = _run_days(tmp_path, broker, SESSIONS[1:-1])
    assert all(r.mismatches == () and r.profit is not None for r in records)
    assert broker.positions() and book.positions(tmp_path) == broker.positions()

    broker.inject("L07", 7)
    (last,) = _run_days(tmp_path, broker, SESSIONS[-1:])
    assert last.mismatches == ("L07",), "a position the desk does not know about went unseen"
    assert last.profit is None, "a mismatched day was reported as a plain number"


def test_scene_7_a_day_that_counts_and_the_same_day_replayed(tmp_path: Path) -> None:
    broker = Pretend(CLEAN, {})
    records = _run_days(tmp_path, broker, SESSIONS[1:])

    assert all(r.mismatches == () and r.profit is not None for r in records)
    charged = [sum(column) for column in zip(*(astuple(r.costs) for r in records), strict=True)]
    assert all(total > 0 for total in charged), "a cost line was never charged"
    assert any(r.market != 0 for r in records), "what holding the market earned is missing"
    again = _run_days(tmp_path / "again", Pretend(CLEAN, {}), SESSIONS[1:])
    assert again == records, "the same days replayed from the saved data gave other records"
    with pytest.raises(TypeError):
        day.Costs(Decimal(1), Decimal(1), Decimal(1), Decimal(1))  # type: ignore[call-arg]
