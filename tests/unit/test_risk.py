"""risk: the pre-trade gate refuses a new entry once the day's loss reaches 2% of capital, the
week's 5%, or the day's fourth new line is used (R-RUNNER-156); on paper a drawdown alerts."""

from __future__ import annotations

import random
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from desk import halt, orders
from desk.lines import Line
from desk.orders import Order, Refused, Settings
from desk.risk import Standing

TEN_K = Settings(capital=Decimal(10_000))
NOW = datetime(2025, 11, 17, 10, tzinfo=UTC)


def _buy(symbol: str) -> Order:
    return Order(
        f"o-{symbol}", Line(symbol, "LSE", "GBP", 1), 10, Decimal(50), Decimal(1), Decimal(45)
    )


def _standing(day: int = 0, week: int = 0, lines: int = 0) -> Standing:
    return Standing(Decimal(day), Decimal(week), lines)


def test_the_gate_refuses_past_a_loss_limit_or_a_fifth_new_line_and_buys_under_all_three() -> None:
    orders.gate(_buy("A"), TEN_K, {}, _standing(199, 499, 3))  #: under all three buys
    for standing, named in (
        (_standing(day=200), "day-loss limit"),
        (_standing(week=500), "week-loss limit"),
        (_standing(lines=4), "4 new lines"),
    ):
        with pytest.raises(Refused, match=named):
            orders.gate(_buy("A"), TEN_K, {}, standing)
    orders.gate(
        _buy("A"), TEN_K, {"A": 5}, _standing(lines=4)
    )  #: more of a held line is no new line
    with pytest.raises(Refused, match="day-loss limit"):
        orders.gate(_buy("A"), TEN_K, {"A": 5}, _standing(day=200))
    with pytest.raises(ValueError, match="never below"):
        _standing(day=-1)
    with pytest.raises(ValueError, match="limits of"):
        Settings(Decimal(1), new_lines=0)


def test_no_sequence_of_fills_lets_a_fifth_new_line_or_a_buy_past_a_loss_limit_through() -> None:
    rng = random.Random(156)  # noqa: S311 - a repeatable test walk
    for _ in range(200):
        held: dict[str, int] = {}
        day = week = Decimal(0)
        lines = 0
        for _ in range(30):
            symbol = rng.choice("ABCDEFG")
            if rng.random() < 0.3:
                held.pop(symbol, None)  #: sold
                day, week = day + rng.randint(0, 90), week + rng.randint(0, 90)
                continue
            standing = Standing(day, week, lines)
            try:
                orders.gate(_buy(symbol), TEN_K, held, standing)
            except Refused:
                continue
            assert day < 200 and week < 500, "a buy went through past a loss limit"
            lines += symbol not in held
            held[symbol] = held.get(symbol, 0) + 10
            assert lines <= 4, "a fifth new line went through"


def test_on_paper_a_drawdown_alerts_and_records_would_have_halted_and_never_halts(
    tmp_path: Path,
) -> None:
    assert halt.drawdown(tmp_path, NOW, _standing(199, 499), TEN_K) is None
    alert = halt.drawdown(tmp_path, NOW, _standing(day=250), TEN_K)
    assert alert is not None and "DRAWDOWN ALERT" in alert and "day-loss limit" in alert
    assert halt.drawdown(tmp_path, NOW, _standing(day=250), TEN_K) == alert  #: once recorded
    assert len((tmp_path / halt.WOULD).read_text(encoding="utf-8").splitlines()) == 2
    assert "week-loss limit" in str(halt.drawdown(tmp_path, NOW, _standing(week=600), TEN_K))
    assert halt.kept(tmp_path) == halt.in_force(tmp_path) == ()  #: no halt, so it still trades
    orders.gate(_buy("A"), TEN_K, {})  #: and nothing in the gate stopped it
