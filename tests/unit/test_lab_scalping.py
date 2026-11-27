"""The momentum burst on one-minute bars: one LSE session worked by hand (a time exit, a stop
exit, the session-end exit) and the rule future-blind."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import lab.scalping as scalping
from desk import bars, intraday, orders, venues
from desk.lines import LINES
from desk.orders import Leg, Settings
from desk.rollup import Candle
from desk.spans import Timed
from desk.strategy import Action
from lab import ladder, rung
from lab.scalping import MomentumBurst, VwapReversion, edge_needed, round_trip_cost, trades_of

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


def test_a_round_trip_costs_two_legs_and_a_trade_gaining_less_shows_a_loss() -> None:
    isf, day = next(x for x in LINES if x.symbol == "ISF"), date(2026, 11, 16)
    settings, price = Settings(Decimal(10000)), Decimal(100)
    rule = MomentumBurst()
    bars = _session()
    trades = trades_of(rule, isf, bars, {}, settings)
    n = trades[0].shares
    cost = orders.charges(isf, Leg.BUY, n, price, Decimal(1)) + orders.charges(
        isf, Leg.SALE, n, price, Decimal(1)
    )
    assert round_trip_cost(isf, price, day, {}, settings) == cost.total / (n * price)
    assert trades[0].gross == 0 and trades[0].gain < 0  # gaining nothing is a loss after cost
    assert trades[0].gain == (trades[0].gross - trades[0].costs.total) / trades[0].paid
    assert edge_needed(Decimal("0.01"), trades[:1]) is None
    se = rung.mean_and_error([p.gain for p in trades])
    assert se is not None and edge_needed(Decimal("0.01"), trades) == Decimal("0.01") + 2 * se[1]


def test_the_set_runs_two_rules_on_two_lines_with_their_answers_and_costs(tmp_path: Path) -> None:
    one, two = LINES[0], LINES[1]
    with bars.writing(tmp_path / bars.LIVE) as opened:
        for line in (one, two):
            opened.timed(
                line,
                "1m",
                [Timed("1m", c.start, c.open, c.high, c.low, c.close, 1) for c in _session()],
            )
    said = scalping.judge_set(tmp_path, {})
    assert said.startswith("SET SCALP: 2 rules, 0 passed")
    table = (tmp_path / "ladder" / "sets" / "SCALP.md").read_text(encoding="utf-8")
    assert f"\nrungs built: {ladder.rungs_built()[0]} of {ladder.rungs_built()[1]}\n" in table
    assert "PRE-REVIEW" in table and "Each is judged against 4 trials." in table
    rows = [r for r in table.splitlines() if r.startswith("| ") and "(LSE)" in r]
    assert len(rows) == 4 and all(len(r.split("|")) == 8 for r in rows)
    assert (
        sum(f"| {r} | {x.symbol} (LSE) |" in table for r in scalping.RULES for x in (one, two)) == 4
    )
    assert (table.count("THIN"), table.count("FAULT")) == (
        2,
        2,
    )  # the burst trades, too few; VWAP none
    assert table.count("%") == 4  # a cost and an edge for each burst line, trades being three
