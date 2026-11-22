"""The momentum burst on one-minute bars: one LSE session worked by hand (a time exit, a stop
exit, the session-end exit) and the rule future-blind."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from desk import intraday, venues
from desk.rollup import Candle
from desk.strategy import Action
from lab.scalping import MomentumBurst, VwapReversion

#: closes by bar number; bars hold 101 but for the bursts at 5, 20 and 505 (held to the end)
CLOSES = {n: 100 for n in range(5)} | {
    5: 101,
    20: 103,
    21: 102,
    505: 105,
    506: 105,
    507: 105,
    508: 105,
    509: 105,
}


def _session() -> list[Candle]:
    """The 510 bars of an LSE day, each a tenth either side of its close, but bar 5 (100 to 101)."""
    start, made = venues.hours("LSE", date(2026, 11, 16)).open, []
    for n in range(510):
        c = Decimal(CLOSES.get(n, 101 if n > 5 else 100))
        high, low = (c, Decimal(100)) if n == 5 else (c + Decimal("0.1"), c - Decimal("0.1"))
        made.append(Candle(start + timedelta(minutes=n), c, high, low, c, 1, "x"))
    return made


def _actions(bars: list[Candle]) -> list[Action]:
    return [d.action for d in intraday.run("burst", MomentumBurst(), "LSE", "X", bars)]


def test_the_burst_is_bought_and_sold_on_time_on_a_stop_and_at_the_close() -> None:
    got = _actions(_session())
    marks = {n: a for n, a in enumerate(got) if a is not Action.HOLD}
    assert marks == {
        5: Action.BUY,  # rose 1 over 3 bars of average range 0.47, above twice it
        15: Action.SELL,  # tenth bar held
        20: Action.BUY,  # rose 2 on range 0.2
        21: Action.SELL,  # close 102 under the entry bar's low 102.9
        505: Action.BUY,
        509: Action.SELL,  # the session's last bar
    }


def test_decisions_on_the_first_bars_equal_the_first_of_all() -> None:
    bars = _session()
    everything = _actions(bars)
    for k in (4, 5, 6, 15, 21, 506, 509):
        assert _actions(bars[:k]) == everything[:k]


def _flat(given: dict[int, tuple[int, int]]) -> list[Candle]:
    """510 bars at 98 of volume 1, but those given by number as (price, volume)."""
    start, made = venues.hours("LSE", date(2026, 11, 16)).open, []
    for n in range(510):
        price, volume = given.get(n, (98, 1))
        p = Decimal(price)
        made.append(Candle(start + timedelta(minutes=n), p, p, p, p, volume, "x"))
    return made


VWAP_BARS = _flat(
    {0: (100, 1), 1: (100, 1), 2: (96, 2), 3: (97, 0), **{n: (96, 0) for n in range(505, 509)}}
)


def test_the_vwap_is_worked_by_hand_and_the_reversion_acts_on_it() -> None:
    rule = VwapReversion()
    seen = [(rule.step(b, False), rule.vwap) for b in VWAP_BARS[:4]]
    assert [v for _, v in seen] == [100, 100, 98, 98]  # (100+100+96*2)/4; no volume adds none
    got = [d.action for d in intraday.run("vwap", VwapReversion(), "LSE", "X", VWAP_BARS)]
    assert {n: a for n, a in enumerate(got) if a is not Action.HOLD} == {
        2: Action.BUY,  # 96 under 98 less a hundredth (97.02)
        4: Action.SELL,  # back at 98
        505: Action.BUY,
        509: Action.SELL,  # the session's last bar
    }
    for k in (2, 3, 4, 505, 509):
        again = intraday.run("vwap", VwapReversion(), "LSE", "X", VWAP_BARS[:k])
        assert [d.action for d in again] == got[:k]
