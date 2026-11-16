"""Known answer: DeMark's published TD Sequential fixes the entry and exit days of a series."""

from datetime import date, timedelta
from decimal import Decimal

from desk.eponymous_demark_sequential import decide
from desk.store import Bar
from desk.strategy import Action


def _trades(closes: list[int]) -> dict[int, Action]:
    bars = [
        Bar(
            date(2020, 1, 1) + timedelta(days=n),
            Decimal(c),
            Decimal(c + 1),
            Decimal(c - 1),
            Decimal(c),
            1,
        )
        for n, c in enumerate(closes)
    ]
    got = decide({"X": bars})
    return {n: d.action for n, d in enumerate(got) if d.action is not Action.HOLD}


def test_buys_the_thirteenth_countdown_bar_and_sells_the_ninth_sell_setup_bar() -> None:
    # Falling by 1 from 300: closes under the close four back from day 4, so the buy setup
    # completes on day 12; each of days 13..25 closes under the low two back: the 13th is
    # day 25, BUY. Rising by 1 from 276: above the close four back from day 28, nine in a
    # row to day 36, SELL. Every other day: nothing.
    assert _trades([*range(300, 274, -1), *range(276, 290)]) == {25: Action.BUY, 36: Action.SELL}


def test_waits_for_the_full_setup_and_countdown() -> None:
    assert _trades(list(range(300, 280, -1))) == {}  # setup done, countdown only at 8
    assert _trades(list(range(300, 292, -1))) == {}  # eight setup bars, no setup
