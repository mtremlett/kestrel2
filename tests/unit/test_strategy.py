"""The five frozen strategies: each buys and sells on the day its published rule says, worked
out by hand below, and none of them can see a bar after the day it decides."""

from __future__ import annotations

import random
from collections.abc import Sequence
from datetime import date, timedelta
from decimal import Decimal

import pytest

from desk import strategy
from desk.store import Bar
from desk.strategy import Action

START = date(2020, 1, 1)


def _bars(closes: Sequence[float | int], reach: float = 0.5) -> tuple[Bar, ...]:
    """A bar per close, its high and low `reach` either side; one bar a day."""
    out = []
    for n, value in enumerate(closes):
        close, half = Decimal(str(value)), Decimal(str(reach))
        out.append(Bar(START + timedelta(n), close, close + half, close - half, close, 1000))
    return tuple(out)


def _trades(name: str, bars: Sequence[Bar]) -> list[tuple[int, Action]]:
    """The days, as positions in the series, on which one strategy buys or sells."""
    days = {bar.day: n for n, bar in enumerate(bars)}
    decided = [d for d in strategy.decide({"X": bars}) if d.strategy == name]
    assert len(decided) == len(bars), f"{name} left a day unanswered"
    return sorted((days[d.day], d.action) for d in decided if d.action is not Action.HOLD)


def test_the_five_are_the_operators_five() -> None:
    assert set(strategy.STRATEGIES) == {
        "rsi2_pullback",
        "bollinger_pullback",
        "breakout_20_10",
        "trend_50_200",
        "supertrend_10_3",
    }


def test_breakout_buys_a_new_20_day_high_and_sells_a_new_10_day_low() -> None:
    #: highs of 10.5 for twenty days; 10.4 does not clear them, 11 does; 9.4 is under 9.5
    bars = _bars([10] * 20 + [10.4, 11, 11, 9.4, 9.4])
    assert _trades("breakout_20_10", bars) == [(21, Action.BUY), (23, Action.SELL)]


def test_bollinger_buys_under_the_lower_band_and_sells_over_the_middle() -> None:
    #: day 20: mean 9.95, two deviations 0.436, so 9 is under 9.514; day 21: 9.5 < mean 9.925
    #: holds; day 22: 10.5 > mean 9.95 sells
    bars = _bars([10] * 20 + [9, 9.5, 10.5])
    assert _trades("bollinger_pullback", bars) == [(20, Action.BUY), (22, Action.SELL)]


def test_rsi2_buys_a_deep_pullback_above_the_200_day_and_sells_over_the_5_day() -> None:
    #: day 201: RSI(2) 9.1, not under 5; day 202: 3.2 buys; day 203: 285 < 5-day 290.8
    #: holds; day 204: 300 > 291 sells
    bars = _bars([100 + n for n in range(200)] + [300, 290, 280, 285, 300])
    assert _trades("rsi2_pullback", bars) == [(202, Action.BUY), (204, Action.SELL)]


def test_rsi2_never_buys_a_pullback_below_the_200_day() -> None:
    bars = _bars([400 - n for n in range(200)] + [190, 180, 170, 185, 200])
    assert _trades("rsi2_pullback", bars) == []


def test_trend_buys_the_50_day_crossing_over_the_200_day_and_sells_the_cross_back() -> None:
    #: day 200: 102 > 100.5 crosses; from day 250 at 50, the 50-day is 197-3j and the
    #: 200-day 124.75-j/4, so j=27 (day 277) is the first day under
    bars = _bars([100] * 200 + [200] * 50 + [50] * 40)
    assert _trades("trend_50_200", bars) == [(200, Action.BUY), (277, Action.SELL)]


def test_trend_does_not_buy_a_cross_it_never_saw() -> None:
    assert _trades("trend_50_200", _bars([100 + n for n in range(260)])) == []


def test_supertrend_buys_a_close_over_its_upper_band_and_sells_one_under_its_lower() -> None:
    #: ten days with a true range of 2: bands 94 and 106. Day 10 closes 110 > 106 and buys;
    #: its lower band becomes 110 - 3 x 2.9 = 101.3, and day 11's close of 100 sells
    bars = _bars([100] * 10 + [110, 100, 100], reach=1)
    assert _trades("supertrend_10_3", bars) == [(10, Action.BUY), (11, Action.SELL)]


def _walk(seed: int, days: int) -> tuple[Bar, ...]:
    """A random walk of trends and pullbacks, in pence, so that every strategy trades."""
    rng = random.Random(seed)  # noqa: S311 - a repeatable test walk, not a secret
    cents, drift, closes = 10_000, 0, []
    for n in range(days):
        if n % 150 == 0:
            drift = rng.choice((-40, 40))
        cents = max(1_000, cents + drift + rng.randint(-250, 250))
        closes.append(cents / 100)
    return _bars(closes, reach=1)


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_no_strategy_sees_a_bar_after_the_day_it_decides(seed: int) -> None:
    bars = {"A": _walk(seed, 1200), "B": _walk(seed + 10, 1100)}
    every = strategy.decide(bars)
    for name in strategy.STRATEGIES:
        for symbol in bars:
            acts = [d.action for d in every if (d.strategy, d.symbol) == (name, symbol)]
            moves = [a for a in acts if a is not Action.HOLD]
            assert Action.BUY in moves and Action.SELL in moves, f"{name} never traded {symbol}"
            assert moves == [Action.BUY, Action.SELL] * (len(moves) // 2) + [Action.BUY] * (
                len(moves) % 2
            ), f"{name} sold what it did not hold in {symbol}"
    for cut in (1, 9, 199, 230, 401, 777, 1050):
        blind = {s: b[:cut] for s, b in bars.items()}
        seen = {b.day for b in bars["A"][:cut]}
        assert set(strategy.decide(blind)) == {d for d in every if d.day in seen}


#: Every day each strategy moves on walk 1, alternately a buy and a sell. Found identical, on
#: four walks, by a second implementation written apart from the desk's from the same
#: textbook rules (13 November 2026), so a changed setting or formula moves these days.
GOLDEN = {
    "rsi2_pullback": (
        "541 544 553 555 580 583 609 613 617 625 820 821 904 906 913 920 975 986 1097 1099"
    ),
    "bollinger_pullback": (
        "37 74 131 169 209 232 244 292 298 311 616 677 713 723 904 927 943 959 975 1004 "
        "1027 1038 1097 1104 1122 1124"
    ),
    "breakout_20_10": (
        "90 112 181 200 364 373 418 428 453 499 523 540 559 579 596 616 683 692 751 904 "
        "1042 1091 1125"
    ),
    "trend_50_200": "482 657 788 995 1090",
    "supertrend_10_3": (
        "91 131 181 208 365 374 423 429 470 542 558 615 683 692 753 912 929 943 1014 1027 1041"
    ),
}


def test_each_strategy_moves_on_the_days_a_second_implementation_found() -> None:
    bars = _walk(1, 1200)
    for name, days in GOLDEN.items():
        assert [n for n, _ in _trades(name, bars)] == [int(n) for n in days.split()], name
