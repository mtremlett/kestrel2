"""The five frozen strategies: each buys and sells on the day its published rule says, worked
out by hand below, and none of them can see a bar after the day it decides. Each declares
what it is before it is tested, and none can sell a line it does not hold."""

from __future__ import annotations

import random
from collections.abc import Sequence
from dataclasses import fields, replace
from datetime import date, timedelta
from decimal import ROUND_FLOOR, Context, Decimal, InvalidOperation, localcontext
from typing import Any

import pytest

from desk import strategy
from desk.lines import LINES
from desk.store import Bar
from desk.strategy import Action, Field, Timeframe

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


def test_the_five_are_the_operators_five_each_on_daily_bars_and_all_twenty_lines() -> None:
    assert set(strategy.STRATEGIES) == {
        "rsi2_pullback",
        "bollinger_pullback",
        "breakout_20_10",
        "trend_50_200",
        "supertrend_10_3",
    }
    #: STR-03: the desk trades every rule on every line, so each is to be judged on them all
    declared = [rule.declared for rule in strategy.STRATEGIES.values()]
    assert all(d.bar is Timeframe.DAILY and d.universe == LINES for d in declared)


class _Untouchable(Decimal):
    def __bool__(self) -> bool:
        raise InvalidOperation("read as true or false")


def test_each_rule_reads_the_data_it_declares_and_no_other(monkeypatch: pytest.MonkeyPatch) -> None:
    #: a number that cannot be added, compared or tested without an error is put in place of a
    #: number of every bar: in place of all a rule does not declare, it decides as before, so on
    #: this walk it used none of them; in place of any one it declares, it cannot decide at all
    bars, every = _walk(1, 1200), strategy.decide({"A": _walk(1, 1200)})
    poison: Any = _Untouchable("sNaN")
    assert {f.value for f in Field} == {f.name for f in fields(Bar)} - {"day"}
    for name, rule in strategy.STRATEGIES.items():
        monkeypatch.setattr(strategy, "STRATEGIES", {name: rule})
        unread = {f.value: poison for f in Field if f not in rule.declared.reads}
        blind = strategy.decide({"A": [replace(bar, **unread) for bar in bars]})
        assert blind == tuple(d for d in every if d.strategy == name)
        for field in rule.declared.reads:
            with pytest.raises(InvalidOperation):
                strategy.decide({"A": [replace(bar, **{field.value: poison}) for bar in bars]})
        monkeypatch.undo()


def test_a_declaration_that_makes_no_sense_cannot_be_made() -> None:
    good = strategy.STRATEGIES["rsi2_pullback"].declared
    assert replace(good, hold=1).hold == 1, "one session is a holding period"
    bad: dict[str, tuple[Any, ...]] = {
        "hold": (0, -5),
        "universe": ((), LINES[:1] * 2),
        "reads": (frozenset(),),
    }
    for name, values in bad.items():
        for value in values:
            with pytest.raises(ValueError, match=name.replace("hold", "holding period")):
                replace(good, **{name: value})


class _Fickle:
    """A rule that answers by the toss of a coin, whatever it holds, and not always in the
    words a rule is allowed."""

    def __init__(self) -> None:
        self._coin = random.Random(7)  # noqa: S311 - a repeatable test coin, not a secret

    def step(self, _bar: Bar, _holding: bool) -> Any:
        return self._coin.choice((True, False, None, 0, 1))


def test_no_rule_can_sell_a_line_it_does_not_hold(monkeypatch: pytest.MonkeyPatch) -> None:
    #: STR-06. Whatever a rule answers, out of a line it can only buy: over a whole history a
    #: sale follows its own buy, and today the one sale there can be is of the line the book
    #: holds, by the rule it holds it for
    monkeypatch.setattr(strategy, "STRATEGIES", {"fickle": _Fickle, "twin": _Fickle})
    bars, said = {"A": _walk(1, 300), "B": _walk(2, 300)}, set()
    acts = [d.action for d in strategy.decide({"A": bars["A"]}) if d.strategy == "fickle"]
    acts = [action for action in acts if action is not Action.HOLD]
    assert len(acts) > 100, "the coin never turned"
    assert acts == [Action.BUY, Action.SELL] * (len(acts) // 2) + [Action.BUY] * (len(acts) % 2)
    for cut in range(250, 300):
        today = strategy.today({s: b[:cut] for s, b in bars.items()}, {"A": "fickle"})
        said |= {(d.strategy, d.symbol, d.action) for d in today if d.action is not Action.HOLD}
    buys = {(*pair, Action.BUY) for pair in (("twin", "A"), ("fickle", "B"), ("twin", "B"))}
    assert said == {("fickle", "A", Action.SELL)} | buys


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
    #: its lower band becomes 110 - 3 x 2.9 = 101.3. Day 11 closes on it exactly and holds;
    #: the band is carried, as the close before was above it, and day 12's 100 sells
    bars = _bars([100] * 10 + [110, 101.3, 100], reach=1)
    assert _trades("supertrend_10_3", bars) == [(10, Action.BUY), (12, Action.SELL)]


def test_rsi2_does_not_buy_a_close_exactly_on_its_200_day_average() -> None:
    #: a climb, then a fall of 300 to 110: RSI(2) 2.2, but the 200 days to day 209 sum to
    #: 22,000, so the average is 110 too, and "above" is not met
    bars = _bars([100] * 200 + [150, 200, 250, 300, 350, 410, 410, 410, 410, 110])
    assert _trades("rsi2_pullback", bars) == []


def test_today_decides_each_lines_last_bar_holding_what_the_book_holds_for_each_rule() -> None:
    #: the breakout's own idea holds both from day 21; the book holds only the second for it
    up, down = _bars([10] * 20 + [10.4, 11, 12]), _bars([10] * 20 + [10.4, 11, 9.4])
    today = strategy.today({"U": up, "D": down}, {"D": "breakout_20_10"})
    assert (
        sorted((d.symbol, d.day) for d in today)
        == [("D", down[-1].day)] * 5 + [("U", up[-1].day)] * 5
    )
    acts = {(d.symbol, d.strategy): d.action for d in today}
    assert acts["U", "breakout_20_10"] is Action.BUY, "a rule the book holds nothing for"
    assert acts["D", "breakout_20_10"] is Action.SELL
    (flat,) = (d for d in strategy.today({"D": down}, {}) if d.strategy == "breakout_20_10")
    assert flat.action is Action.HOLD, "a rule sold what the book does not hold for it"


def test_the_callers_arithmetic_cannot_move_a_decision() -> None:
    bars = {"A": _walk(5, 1200)}
    with localcontext(Context(prec=3, rounding=ROUND_FLOOR)):
        coarse = strategy.decide(bars)
    assert coarse == strategy.decide(bars)


def _walk(seed: int, days: int) -> tuple[Bar, ...]:
    """A random walk of trends and pullbacks, so that every strategy trades. Prices sit on
    a 25p tick, so a close often equals a band or an old high exactly; each day's open,
    high and low fall unevenly about its close, so a rule reading the wrong one is seen."""
    rng = random.Random(seed)  # noqa: S311 - a repeatable test walk, not a secret
    ticks, drift, out = 400, 0, []
    for n in range(days):
        if n % 150 == 0:
            drift = rng.choice((-2, 2))
        ticks = max(40, ticks + drift + rng.randint(-10, 10))
        up, down = rng.randint(0, 8), rng.randint(0, 8)
        close, high, low = (Decimal(t) / 4 for t in (ticks, ticks + up, ticks - down))
        open_ = Decimal(ticks + rng.randint(-down, up)) / 4
        out.append(Bar(START + timedelta(n), open_, high, low, close, 1000))
    return tuple(out)


def _jumpy(seed: int, days: int = 80) -> tuple[Bar, ...]:
    """A short walk in whole pounds with jumps, so a close can land on a band exactly."""
    rng = random.Random(seed)  # noqa: S311 - a repeatable test walk, not a secret
    close, out = 100, []
    for n in range(days):
        close = max(10, close + rng.randint(-6, 6))
        high, low = close + rng.randint(0, 3), close - rng.randint(0, 3)
        price, top, bottom = Decimal(close), Decimal(high), Decimal(low)
        out.append(Bar(START + timedelta(n), price, top, bottom, price, 1000))
    return tuple(out)


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_no_strategy_sees_a_bar_after_the_day_it_decides(seed: int) -> None:
    bars = {"A": _walk(seed, 1200), "B": _walk(seed + 20, 1100)}
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


#: Every day each strategy moves on these series, alternately a buy and a sell. Found
#: identical, on sixty walks and these, by a second implementation written apart from the
#: desk's from the same textbook rules (13 November 2026). Walks 5, 9, 29 and 36 and the
#: two jumpy series are each the first found to show a wrong rule the others missed: a
#: window a day off, Wilder's seed, the band's price or carry, or a tie broken wrongly.
GOLDEN = {
    "walk 1": {
        "rsi2_pullback": "455 458 480 484 505 507 886 889 914 921 937 942 966 970",
        "bollinger_pullback": (
            "21 127 129 149 202 208 478 494 502 588 592 682 699 757 917 931 936 956 965 977 "
            "985 1018 1052 1087 1095 1111"
        ),
        "breakout_20_10": "152 201 228 423 430 454 765 888 892 914 1023 1028 1115",
        "trend_50_200": "222 527 822 997",
        "supertrend_10_3": "152 201 211 454 765 914 1020 1028",
    },
    "walk 5": {
        "rsi2_pullback": "604 605 608 611 633 641 647 650 659 661 925 931 1000 1001",
        "bollinger_pullback": (
            "165 223 229 325 331 365 371 410 434 456 512 524 624 676 683 691 702 758 780 800 "
            "929 932"
        ),
        "breakout_20_10": "21 166 472 511 537 608 910 999 1011",
        "trend_50_200": "544 685 925",
        "supertrend_10_3": "21 166 472 513 527 608 764 780 909",
    },
    "walk 9": {
        "rsi2_pullback": (
            "209 221 479 480 612 614 630 634 655 657 662 675 967 969 1074 1081 1170 1174"
        ),
        "bollinger_pullback": (
            "44 50 176 237 239 304 310 337 382 391 409 416 425 454 612 700 719 787 789 818 "
            "968 970 1171 1178"
        ),
        "breakout_20_10": "20 119 127 161 340 350 460 607 859 967 975 1172 1184",
        "trend_50_200": "498 685 941",
        "supertrend_10_3": "20 44 52 164 457 612 707 720 907 1079 1091 1171 1179",
    },
    "walk 29": {
        "rsi2_pullback": "446 448 608 615 643 649 666 677 1090 1099",
        "bollinger_pullback": (
            "19 60 71 177 333 349 608 628 642 715 726 789 793 814 995 1004 1090 1110"
        ),
        "breakout_20_10": "317 446 455 608 952 995 1047 1058 1071 1094",
        "trend_50_200": "329 373 433 693 984 1041 1052 1064 1071 1136",
        "supertrend_10_3": "317 446 453 608 952 1092",
    },
    "walk 36": {
        "rsi2_pullback": (
            "199 212 408 412 420 422 449 457 721 722 728 729 766 769 773 780 822 826 1097 "
            "1099 1155 1158"
        ),
        "bollinger_pullback": "170 303 449 516 568 575 597 603 766 793 811 943 949 952",
        "breakout_20_10": (
            "21 89 100 130 140 170 309 337 355 411 426 449 605 766 1013 1023 1069 1095 1107 "
            "1155 1160"
        ),
        "trend_50_200": "397 487 671 846 1080",
        "supertrend_10_3": (
            "17 28 35 90 98 170 305 339 355 421 425 450 517 526 577 765 1016 1098 1105 1156 " "1159"
        ),
    },
    "jumpy 10": {
        "supertrend_10_3": "54",
    },
    "jumpy 332": {
        "supertrend_10_3": "14 35 46 64 72",
    },
}


def test_each_strategy_moves_on_the_days_a_second_implementation_found() -> None:
    for series, expected in GOLDEN.items():
        kind, seed = series.split()
        bars = _walk(int(seed), 1200) if kind == "walk" else _jumpy(int(seed))
        for name, days in expected.items():
            found = [n for n, _ in _trades(name, bars)]
            assert found == [int(n) for n in days.split()], f"{name} on {series}"
            limit = strategy.STRATEGIES[name].declared.hold
            ends = [*found[1::2], len(bars) - 1]  #: one still held is held to the last bar
            held = [sold - bought for bought, sold in zip(found[::2], ends, strict=False)]
            assert limit is None or max(held) <= limit, f"{name} outstays {limit} on {series}"
