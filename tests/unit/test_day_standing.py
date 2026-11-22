"""The day's standing against the loss and order-rate limits, given to the gate on the send path."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from desk import book, day, day_money, orders
from desk.broker import Pretend
from desk.halt import Blocker, Stopped
from desk.lines import Line
from desk.orders import Charges, Order, Settings
from desk.risk import Standing
from desk.store import Bar

ROOM = Settings(Decimal(10_000))
MON, TUE, A = date(2025, 11, 10), date(2025, 11, 11), Line("A", "LSE", "GBP", 1)
BARS = {A: tuple(Bar(d, Decimal(50), Decimal(51), Decimal(49), Decimal(51), 1) for d in (MON, TUE))}


def test_a_lost_day_is_the_standing_that_makes_the_send_path_refuse_a_buy(tmp_path: Path) -> None:
    free = Charges(*[Decimal(0)] * 5)
    lost = day.Record(MON, Decimal(-300), free, Decimal(0), (), Decimal(0), 0)
    book._write(tmp_path / day.RECORDS, [day.HEADER, day._row(lost)])
    standing = day.standing(tmp_path, TUE)
    assert standing == Standing(Decimal(300), Decimal(300), 0)
    broker, order = Pretend(BARS, {}), Order("o-1", A, 1, *map(Decimal, (50, 1, 45)))
    broker.open(TUE)
    try:
        book.send(tmp_path, broker, order, Settings(Decimal(10_000)), None, standing)
    except Stopped as stopped:
        assert stopped.blocker is Blocker.GATE and "day-loss limit" in str(stopped)
    else:
        raise AssertionError("a buy past the day's loss limit was sent")


def test_a_held_leveraged_lines_exposure_is_at_its_leverage_and_caps_the_next_buy(
    tmp_path: Path,
) -> None:
    three = Line("T", "LSE", "GBP", 3, underlying="idx")
    bars = {three: BARS[A]}
    broker = Pretend({**bars}, {})
    broker.open(TUE)
    settings = Settings(Decimal(10_000))
    book.send(tmp_path, broker, Order("o-1", three, 10, *map(Decimal, (51, 1, 45))), settings)
    pounds = day_money.exposure(tmp_path, bars, {"GBP": Decimal(1)})
    assert pounds == {"idx": Decimal(10 * 51 * 3)}, "shares x close x rate x leverage"
    other = Order(
        "o-2", Line("U", "LSE", "GBP", 1, underlying="idx"), 20, *map(Decimal, (51, 1, 45))
    )
    try:
        book.send(tmp_path, broker, other, settings, None, None, {"idx": Decimal(3_500)})
    except Stopped as stopped:
        assert stopped.blocker is Blocker.GATE and "idx exposure" in str(stopped)
    else:
        raise AssertionError("a buy past the underlying's cap was sent")


def test_a_day_that_opens_past_a_loss_limit_tells_him_once_a_drawdown_alert(tmp_path: Path) -> None:
    free = Charges(*[Decimal(0)] * 5)
    lost = day.Record(MON, Decimal(-300), free, Decimal(0), (), Decimal(0), 0)
    book._write(tmp_path / day.RECORDS, [day.HEADER, day._row(lost)])
    told: list[tuple[str, str]] = []
    for _ in range(2):
        day._alert(tmp_path, TUE, Settings(Decimal(10_000)), lambda n, w: told.append((n, w)))
    assert [n for n, _ in told] == ["drawdown 2025-11-11"] * 2 and "DRAWDOWN ALERT" in told[0][1]


def test_a_fall_past_1500_from_the_highest_point_tells_him_and_a_smaller_one_does_not(
    tmp_path: Path,
) -> None:
    free = Charges(*[Decimal(0)] * 5)
    told: list[tuple[str, str]] = []
    for profit in (2_000, -1_500, -1):
        n = len(day.records(tmp_path))
        rows = [day.HEADER, *(day._row(r) for r in day.records(tmp_path))]
        rows.append(
            day._row(
                day.Record(MON + timedelta(n), Decimal(profit), free, Decimal(0), (), Decimal(0), 0)
            )
        )
        book._write(tmp_path / day.RECORDS, rows)
        day._peak_fall(tmp_path, TUE, lambda n, w: told.append((n, w)))
    assert [w for _, w in told] == ["DRAWDOWN ALERT: £1501 below its highest; paper, trading on."]


def test_a_buy_that_moves_with_a_held_line_is_refused_and_one_that_does_not_goes(
    tmp_path: Path,
) -> None:
    days = [date(2025, 9, 1) + timedelta(days=i) for i in range(30)]
    wiggle = [Decimal(100 + (i * 7) % 5 + i % 3) for i in range(30)]
    other = [Decimal(100 + (i * 11) % 7 - i % 2) for i in range(30)]

    def line(symbol: str, closes: list[Decimal]) -> tuple[Line, tuple[Bar, ...]]:
        return Line(symbol, "LSE", "GBP", 1), tuple(
            Bar(d, c, c, c, c, 1) for d, c in zip(days, closes, strict=True)
        )

    held, twin, apart = line("H", wiggle), line("T", [c * 2 for c in wiggle]), line("P", other)
    archive = dict([held, twin, apart])
    broker = Pretend(archive, {})
    broker.open(days[-1])
    book.send(tmp_path, broker, Order("o-1", held[0], 1, *map(Decimal, (100, 1, 90))), ROOM)
    moves = orders.moves({"H"}, archive, "T")
    assert set(moves) == {"H", "T"} and orders.moves({"H"}, archive, "P").keys() == {"H", "P"}
    try:
        book.send(
            tmp_path,
            broker,
            Order("o-2", twin[0], 1, *map(Decimal, (100, 1, 90))),
            ROOM,
            None,
            None,
            None,
            moves,
        )
    except Stopped as stopped:
        assert stopped.blocker is Blocker.GATE and "correlated 1.00 with held H" in str(stopped)
    else:
        raise AssertionError("a buy moving with a held line was sent")
    sent = book.send(
        tmp_path,
        broker,
        Order("o-3", apart[0], 1, *map(Decimal, (100, 1, 90))),
        ROOM,
        None,
        None,
        None,
        orders.moves({"H"}, archive, "P"),
    )
    assert sent.filled == 1


def test_the_currency_apart_from_trading_is_told_once_a_trade_has_closed(tmp_path: Path) -> None:
    dollar, told = Line("U", "US", "USD", 1), list[tuple[str, str]]()
    broker = Pretend({dollar: BARS[A]}, {})
    for on, rate in ((MON, "0.8"), (TUE, "0.75")):
        broker.open(on)
        book.record_rates(tmp_path, on, {"GBP": Decimal(1), "USD": Decimal(rate)})
        if on == MON:
            book.send(
                tmp_path, broker, Order("o-2", dollar, 10, *map(Decimal, (50, 0.8, 45))), ROOM
            )
    day._currency(tmp_path, {dollar: BARS[A]}, TUE, lambda n, w: told.append((n, w)))
    assert [n for n, _ in told] == ["currency 2025-11-11"] and "£-25.50 on open holdings" in told[
        0
    ][1]
    told.clear()
    book.send(tmp_path, broker, orders.Sale("s-2", dollar, 10), ROOM)
    day._currency(tmp_path, {dollar: BARS[A]}, TUE, lambda n, w: told.append((n, w)))
    assert [n for n, _ in told] == ["currency 2025-11-11"] and "£-25" in told[0][1]


def test_the_interest_on_idle_cash_is_told_once_a_fill_has_begun_it(tmp_path: Path) -> None:
    told, broker = list[tuple[str, str]](), Pretend(BARS, {})
    day._interest(tmp_path, BARS, TUE, ROOM, lambda n, w: told.append((n, w)))
    assert told == []
    broker.open(MON)
    book.record_rates(tmp_path, MON, {"GBP": Decimal(1)})
    book.send(tmp_path, broker, Order("o-4", A, 1, *map(Decimal, (50, 1, 45))), ROOM)
    day._interest(tmp_path, BARS, TUE, ROOM, lambda n, w: told.append((n, w)))
    assert [n for n, _ in told] == ["interest 2025-11-11"] and "£2.18" in told[0][1]
