"""The opening range breakout on five-minute bars: two LSE sessions with a hand-worked list of
actions, and the rule future-blind (decisions on the first k bars are the first k decisions)."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from desk import intraday, venues
from desk.rollup import Candle
from desk.strategy import Action
from lab.intraday import OpeningRangeBreakout


def _session(
    day: date, closes: dict[int, float], rng: tuple[float, float], base: float
) -> list[Candle]:
    """The 102 bars of an LSE day: six bars spanning `rng`, then flat bars at `base` but for the
    closes given by bar number."""
    start, made = venues.hours("LSE", day).open, []
    for n in range(102):
        c = Decimal(str(closes.get(n, base)))
        high, low = (Decimal(str(rng[0])), Decimal(str(rng[1]))) if n < 6 else (c, c)
        made.append(
            Candle(start + timedelta(minutes=5 * n), c, max(high, c), min(low, c), c, 1, "x")
        )
    return made


FIRST = _session(date(2026, 11, 16), {6: 102, 8: 98, 9: 98, 10: 102}, (101, 99), 100)
SECOND = _session(date(2026, 11, 17), {7: 100, 8: 113, 20: 109}, (112, 110), 111)
BARS = FIRST + SECOND


def _run(bars: list[Candle]) -> list[Action]:
    return [d.action for d in intraday.run("orb", OpeningRangeBreakout(), "LSE", "X", bars)]


def test_the_breakout_is_bought_the_fall_sold_and_each_session_starts_fresh() -> None:
    got = {n: a for n, a in enumerate(_run(BARS)) if a is not Action.HOLD}
    assert got == {
        6: Action.BUY,  # a close of 102 over the range's high of 101
        8: Action.SELL,  # 98 under the low of 99
        10: Action.BUY,  # back over the high
        101: Action.SELL,  # flat 100 is inside the range, held to the session's last bar
        102 + 8: Action.BUY,  # 113 over the new range's high of 112; 100 at bar 7 bought nothing
        102 + 20: Action.SELL,  # 109 under the new low of 110
    }
    held = _session(date(2026, 11, 16), dict.fromkeys(range(6, 102), 102), (101, 99), 100)
    assert _run(held)[-1] is Action.SELL  # a position is closed at the session's last bar


def test_decisions_on_the_first_k_bars_are_the_first_k_decisions() -> None:
    every = _run(BARS)
    for k in (1, 6, 7, 9, 11, 102, 105, 110, 150, 204):
        assert _run(BARS[:k]) == every[:k]
