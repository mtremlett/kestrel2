"""Known answer: Mansfield's rule fixes the entry and exit days of a made-up series."""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from desk.eponymous_mansfield_rs_momentum import decide
from desk.store import Bar
from desk.strategy import Action


def _bars(closes: list[int]) -> list[Bar]:
    return [
        Bar(date(2020, 1, 1) + timedelta(days=n), Decimal(c), Decimal(c), Decimal(c), Decimal(c), 1)
        for n, c in enumerate(closes)
    ]


def _trades(stock: list[int], index: list[int]) -> dict[int, Action]:
    out = decide({"SPY": _bars(index), "X": _bars(stock)})
    return {n: d.action for n, d in enumerate(out) if d.action is not Action.HOLD}


def test_buys_when_the_ratio_crosses_above_its_year_average_and_sells_below_it() -> None:
    # 260 flat days: RS is exactly zero (not above it). 101 lifts the ratio over its average: BUY;
    # 99 puts it under (the average is then 100): SELL.
    assert _trades([100] * 260 + [101, 99], [100] * 262) == {260: Action.BUY, 261: Action.SELL}


def test_a_stock_trailing_the_index_is_not_bought_and_no_index_raises() -> None:
    # the stock rises, the index rises faster: the ratio only falls
    assert _trades([*range(100, 400)], [*range(100, 700, 2)]) == {}
    with pytest.raises(ValueError, match="SPY"):
        decide({"X": _bars([100])})
