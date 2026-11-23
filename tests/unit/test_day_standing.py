"""The day's standing against the loss and order-rate limits, given to the gate on the send path."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from desk import book, day, day_money, halt, intraday, orders, paper, strategy
from desk.broker import Pretend, Report
from desk.halt import Blocker, Stopped
from desk.lines import LINES, YARDSTICK, Line
from desk.orders import Charges, Order, Settings
from desk.risk import Standing
from desk.store import Bar

ROOM = Settings(Decimal(10_000))
MON, TUE, A = date(2025, 11, 10), date(2025, 11, 11), Line("A", "LSE", "GBP", 1)
BARS = {
    A: tuple(Bar(d, Decimal(50), Decimal(51), Decimal(49), Decimal(51), 10**7) for d in (MON, TUE))
}


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
            Bar(d, c, c, c, c, 10**7) for d, c in zip(days, closes, strict=True)
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


def test_currency_and_interest_are_read_back_unchanged_and_older_files_still_read(
    tmp_path: Path,
) -> None:
    free = Charges(*[Decimal(0)] * 5)
    kept = day.Record(MON, Decimal(5), free, Decimal(0), (), Decimal(0), 0, (), 0, None)
    both = day.Record(
        TUE,
        Decimal(7),
        free,
        Decimal(0),
        (),
        Decimal(0),
        0,
        (),
        0,
        None,
        *map(Decimal, ("1.50", "0.25")),
    )
    book._write(tmp_path / day.RECORDS, [day.HEADER, *(day._row(r) for r in (kept, both))])
    assert day.records(tmp_path) == (kept, both)
    old = [*day.HEADER[:11], *day.HEADER[13:]]  #: the header written before FX, by place
    rows: list[Sequence[object]] = [old, [*day._row(kept)[:11], *day._row(kept)[13:]]]
    book._write(tmp_path / day.RECORDS, rows)
    assert day.records(tmp_path) == (kept,)


def test_the_zoo_stands_apart_so_neither_spends_the_others_losses_or_new_lines(
    tmp_path: Path,
) -> None:
    bars, zoo = {YARDSTICK: BARS[A]}, "20251110-zoo_flip-VUAG-0800"
    broker = Pretend(bars, {})
    broker.open(MON)
    book.record_rates(tmp_path, MON, {"GBP": Decimal(1)})
    book.send(tmp_path, broker, Order(f"{zoo}B", YARDSTICK, 1, *map(Decimal, (50, 1, 45))), ROOM)
    assert (day.standing(tmp_path, MON).new_lines, day.standing(tmp_path, MON, True).new_lines) == (
        0,
        1,
    )
    book.send(tmp_path, broker, orders.Sale(f"{zoo}S", YARDSTICK, 1), ROOM)
    free = Charges(*[Decimal(0)] * 5)
    lost = day.Record(MON, Decimal(-300), free, Decimal(0), (), Decimal(0), 0)
    book._write(tmp_path / day.RECORDS, [day.HEADER, day._row(lost)])
    ours, theirs = day.standing(tmp_path, TUE), day.standing(tmp_path, TUE, True)
    assert theirs.day_loss > 0 and ours.day_loss + theirs.day_loss == 300  # one record, split


def test_the_zoos_holdings_never_fill_the_desks_five_nor_the_desks_the_zoos(tmp_path: Path) -> None:
    lines = [Line(s, "LSE", "GBP", 1) for s in "ABCDEFGHIJ"]
    broker = Pretend({line: BARS[A] for line in lines}, {})
    broker.open(MON)

    def buy(oid: str, line: Line) -> int:
        return book.send(
            tmp_path, broker, Order(oid, line, 1, *map(Decimal, (50, 1, 45))), ROOM
        ).filled

    assert [buy(f"20251110-zoo_x-{ln.symbol}-0800B", ln) for ln in lines[:5]] == [1] * 5
    assert buy("20251110-trend-F", lines[5]) == 1  # the zoo's five leave the desk its own
    assert [buy(f"20251110-d{n}-{ln.symbol}", ln) for n, ln in enumerate(lines[6:9])] == [1] * 3
    with pytest.raises(Stopped, match="5 holdings already"):  # the zoo has five: its sixth goes not
        buy("20251110-zoo_x-J-0805B", lines[9])
    gone = book.send(tmp_path, broker, orders.Sale("20251110-goflat-A", lines[0], 1), ROOM)
    assert gone.filled == 1  # go flat, the second kill level, still sells the zoo's shares


class _In:
    """Always in the market."""

    def step(self, bar: Bar, holding: bool) -> bool:  # noqa: ARG002  # a double: it reads nothing
        return True


def test_the_daily_zoo_buys_one_share_a_rule_only_when_on_and_yields_the_desks_lines(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert len(intraday.ZOO_DAILY) == 23 and all(
        n.startswith(orders.ZOO) for n in intraday.ZOO_DAILY
    )
    wed, a, b = date(2025, 11, 12), YARDSTICK, next(ln for ln in LINES if ln.symbol == "ISF")
    bars = {ln: tuple(replace(BARS[A][0], day=d) for d in (MON, TUE, wed)) for ln in (a, b)}
    broker, rates = Pretend(bars, {}), {"GBP": Decimal(1)}

    def upto(on: date) -> dict[Line, tuple[Bar, ...]]:  # the bars saved before the day
        return {a: tuple(bar for bar in bars[a] if bar.day < on)}

    monkeypatch.setattr(strategy, "STRATEGIES", {})
    monkeypatch.setattr(intraday, "ZOO_DAILY", {"zoo_in": _In})
    monkeypatch.setattr(intraday, "zoo_lines", lambda: (a,))
    broker.open(TUE)
    day.trade(tmp_path, upto(TUE), broker, ROOM, TUE, rates)
    assert book.positions(tmp_path) == {}  # the switch off: the zoo sends nothing
    day.trade(tmp_path, upto(TUE), broker, ROOM, TUE, rates, zoo=True)
    assert book.positions(tmp_path) == {"VUAG": 1}  # on: one share, under its own allowance
    assert (day.standing(tmp_path, TUE).new_lines, day.standing(tmp_path, TUE, True).new_lines) == (
        0,
        1,
    )
    monkeypatch.setattr(orders, "HOLDINGS", 1)  # the zoo's line fills none of the desk's holdings
    book.send(
        tmp_path, broker, Order("20251111-desk_in-ISF", b, 1, *map(Decimal, (50, 1, 45))), ROOM
    )
    monkeypatch.setattr(orders, "HOLDINGS", 5)
    monkeypatch.setattr(strategy, "STRATEGIES", {"desk_in": _In})
    broker.open(wed)
    sessions, place = list[date | None](), broker.place

    def placed(order: Order | orders.Sale) -> Report:  # the session each order is dated
        sessions.append(order.session)
        return place(order)

    monkeypatch.setattr(broker, "place", placed)
    day.trade(tmp_path, upto(wed), broker, ROOM, wed, rates, zoo=True)
    assert set(sessions) == {TUE}  # dated the session it was decided on, as the paper door demands
    assert book.positions(tmp_path)["VUAG"] > 1  # the zoo yielded the line the desk's rule bought
    assert [f.order_id.split("-")[1] for f in book.fills(tmp_path) if f.day == wed] == [
        "zoo_in",
        "desk_in",
    ]


def test_a_round_sends_only_what_the_steps_time_allows_and_carries_the_rest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One cap over the whole round (R-RUNNER-456): the desk's buys, then the zoo's, ask the
    broker for paper.MAX_ORDERS in all; a buy the gate refuses takes no slot; every order past
    the cap is decided, chained in the story and on the morning's list as CARRIED."""
    lines = [ln for ln in LINES if ln.retail and ln.leverage == 1 and ln.isa][:20]
    cheap = replace(BARS[A][0], open=Decimal(5), high=Decimal(5), low=Decimal(5), close=Decimal(5))
    bars = {ln: tuple(replace(cheap, day=d) for d in (MON, TUE)) for ln in lines}
    monkeypatch.setattr(strategy, "STRATEGIES", {"desk_in": _In})
    monkeypatch.setattr(intraday, "ZOO_DAILY", {"zoo_in": _In})
    monkeypatch.setattr(intraday, "zoo_lines", lambda: tuple(lines))
    monkeypatch.setattr(orders, "HOLDINGS", 20)
    first, rates = {ln: (bars[ln][0],) for ln in lines}, {ln.currency: Decimal(1) for ln in lines}
    for killed, cap in ((frozenset({"desk_in"}), paper.MAX_ORDERS), (frozenset(), 2)):
        root, broker = tmp_path / str(cap), Pretend(bars, {})
        monkeypatch.setattr(paper, "MAX_ORDERS", cap)
        broker.open(TUE)
        answers = day.trade(root, first, broker, ROOM, TUE, rates, killed=killed, zoo=True)
        carried = {s.order_id for s in answers if s.blocker is Blocker.CARRIED}
        assert len(broker.submitted()) == sum(s.blocker is None for s in answers) == cap
        rules = {"zoo_in"} if killed else {"desk_in", "zoo_in"}  #: a killed rule's buys take none
        assert {i.split("-")[1] for i in carried} == rules
        assert {c.order_id for c in book.chains(root) if c.blocker == "CARRIED"} == carried
        assert {b.order_id for b in halt.morning(root, TUE)[Blocker.CARRIED]} == carried


def test_a_monday_opens_free_of_fridays_loss_and_a_record_of_today_still_counts(
    tmp_path: Path,
) -> None:
    """London refused every buy on Mon 23 Nov for Friday's 386.17 pounds lost: a loss never
    crosses into a new week, as the week's own loss does not; within the week it stands."""
    free, fri = Charges(*[Decimal(0)] * 5), MON - timedelta(days=3)
    lost = day.Record(fri, Decimal("-386.17"), free, Decimal(0), (), Decimal(0), 0)
    book._write(tmp_path / day.RECORDS, [day.HEADER, day._row(lost)])
    assert day.standing(tmp_path, MON) == Standing(Decimal(0), Decimal(0), 0)
    today = replace(lost, day=MON, profit=Decimal(-300))
    book._write(tmp_path / day.RECORDS, [day.HEADER, day._row(lost), day._row(today)])
    assert day.standing(tmp_path, MON) == Standing(Decimal(300), Decimal(300), 0)
