"""Periods and regimes: a strategy replayed in each, one that earns in one regime alone kept
for that regime, and a paper trade outside it tagged."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, timedelta
from decimal import Decimal

import pytest
from test_lab_folds import _verdict, _window
from test_lab_rung import POUND, SHAPE, TEN_K, _bars, _walk

from desk.store import Bar
from lab import cell, folds, luck, regime, rung, trials
from lab.regime import Replay, Replayed, Tag

EDGE, TURN = 0.012, 500  #: the weather turns every 500 days


def _weather(bars: Sequence[Bar], *names: str) -> dict[date, str]:
    """Each stretch of TURN days under the next name, by turns."""
    return {bar.day: names[n // TURN % len(names)] for n, bar in enumerate(bars)}


def _judge(bars: Sequence[Bar], weather: dict[date, str], periods: int = 2) -> Replayed:
    return regime.judge(_window(bars), bars, TEN_K, POUND, weather, periods)


def test_a_rule_that_earns_in_one_regime_alone_is_kept_for_it_and_tagged_outside_it() -> None:
    for seed in range(2):
        #: a breakout that rises in fair weather and falls back in foul, two turns in three
        bars = _walk(seed, *[0.008, -EDGE, -EDGE] * 8, days=TURN)
        weather = _weather(bars, "fair", "foul", "foul")
        found = _judge(bars, weather)
        fair, foul = found.regimes
        assert (fair.name, fair.bars, foul.name, foul.bars) == ("fair", 4000, "foul", 8000)
        assert not found.whole.passed, "on all its history together it is nothing"
        assert fair.verdict.passed and not foul.verdict.passed and found.home == ("fair",)
        assert found.passed, "never failed for working in only one"
        #: every trade is replayed in the regime it was bought in, and in no other
        both = sorted(fair.verdict.trades + foul.verdict.trades, key=lambda p: p.trade.bought)
        assert tuple(both) == found.whole.trades
        assert {weather[p.trade.bought] for p in fair.verdict.trades} == {"fair"}
        assert len({v.key for v in found.trials}) == 3, "each replay a result of its own"
        told = _judge(bars, weather | {bars[TURN].day: "fair"}).regimes[1]
        assert told.verdict.trades == foul.verdict.trades, "no trade bought that day"
        assert told.verdict.key != foul.verdict.key, "and still another regime's days"
        #: three looks at one rule, each a trial the luck rung counts; the edge survives them
        assert found.trials == (found.whole, fair.verdict, foul.verdict)
        assert [c.passed for c in luck.correct(found.trials, 0)] == [False, True, False], seed
        whole = trials.name(_window(bars))  #: and each has a name of its own in the register
        assert found.names == (whole, f"{whole}, in fair", f"{whole}, in foul")
        #: on paper a trade bought in foul weather is tagged, and it is not refused
        assert found.tag(weather, bars[0].day) == Tag(bars[0].day, "fair", False)
        assert found.tag(weather, bars[TURN].day) == Tag(bars[TURN].day, "foul", True)
        assert found.tag({bars[0].day: "fog"}, bars[0].day).outside, "weather never replayed"
        with pytest.raises(ValueError, match="no regime"):
            found.tag(weather, bars[-1].day + timedelta(1))
        #: the weather after the window's end is not read: a later label changes nothing
        #: and a window is its own days: none before its start, none after its end
        inner = cell.Cell("breakout_20_10", "VUSA", bars[TURN].day, bars[3999].day)
        later = {bar.day: "fog" for bar in bars[4000:]}
        seen = regime.judge(inner, bars, TEN_K, POUND, weather | later, 2)
        days = {bar.day: weather[bar.day] for bar in bars[TURN:4000]}
        assert seen == regime.judge(inner, bars, TEN_K, POUND, days, 2)
        assert [(r.name, r.bars) for r in seen.regimes] == [("fair", 1000), ("foul", 2500)]
    bars = _walk(0, 0, 0)
    weather = _weather(bars, "fair", "foul")
    dead = _judge(bars, weather)  #: no edge in any weather: no home, and every trade tagged
    assert not dead.passed and dead.home == () and dead.tag(weather, bars[0].day).outside


def test_the_periods_are_the_folds_own_parts_each_replayed_alone() -> None:
    bars = _walk(0, EDGE, EDGE, 0)
    found, cut = (
        _judge(bars, _weather(bars, "fair", "foul"), 3),
        folds.judge(_window(bars), bars, TEN_K, POUND, 2),
    )
    first, second, third = found.periods  #: oldest first, the window in three equal parts
    assert (first.verdict, second.verdict) == (cut.folds[0].inside, cut.folds[0].outside)
    assert third.verdict == cut.folds[1].outside and [p.bars for p in found.periods] == [5000] * 3
    assert second.name == f"{bars[5000].day} to {bars[9999].day}"
    #: shown side by side: it earned in two periods and not in the last
    assert [p.verdict.passed for p in found.periods] == [True, True, False]
    assert all(p.verdict not in found.trials for p in found.periods), "shown, never picked from"


def test_a_rule_that_passed_only_on_all_weather_together_has_no_home() -> None:
    many = _verdict(*["0.08", "-0.02", "0.03"] * 10)
    thin, none, lost = _verdict("0.03", "0.02", "0.04"), _verdict(), _verdict("-0.03", "-0.01")
    assert many.passed and not (thin.passed or none.passed or lost.passed)
    replays = (Replay("calm", 9, thin), Replay("fog", 9, none), Replay("storm", 9, lost))
    wide = Replayed(many, (), replays)  #: thirty trades in all, too few in any one regime
    day = date(2020, 1, 2)
    assert wide.passed and wide.home == () and wide.tag({day: "calm"}, day).outside
    assert wide.trials == (many, thin, none, lost), "a regime with no trade is a look too"
    narrow = Replayed(thin, (), (Replay("calm", 9, many), *replays[1:]))
    assert narrow.passed and narrow.home == ("calm",), "a regime it passed in is its home"
    assert [narrow.tag({day: name}, day).outside for name in ("calm", "storm")] == [False, True]
    assert not Replayed(thin, (), replays).passed


def test_a_replay_that_could_show_nothing_is_refused_as_a_fault_in_the_test() -> None:
    bars = _bars(SHAPE)
    weather = _weather(bars, "wet") | {bars[3].day: "dry"}
    found = _judge(bars, weather)  #: by name, whichever came first
    assert [(r.name, r.bars, len(r.verdict.trades)) for r in found.regimes] == [
        ("dry", 1, 0),
        ("wet", 24, 1),
    ]
    assert found.whole == rung.judge(cell.run(_window(bars), bars), bars, TEN_K, POUND)
    assert len(_judge(bars, weather, 25).periods) == 25, "a bar a period is the limit"
    spy = cell.Cell("breakout_20_10", "SPY", bars[0].day, bars[-1].day)
    usd = regime.judge(spy, bars, TEN_K, Decimal("0.8"), weather, 2)  #: priced in dollars
    paid = {v.trades[0].paid for v in (usd.whole, usd.periods[1].verdict, usd.regimes[1].verdict)}
    assert paid == {Decimal("2055.976608")}, "the first rung's own figure, in every replay"
    with pytest.raises(ValueError, match="two regimes or more"):
        _judge(bars, _weather(bars, "wet"))
    for periods in (1, 26):
        with pytest.raises(ValueError, match=f"25 bars in {periods} periods replay nothing"):
            _judge(bars, weather, periods)
    for bad in ({}, {bars[5].day: ""}, {bars[5].day: "wet "}, {bars[5].day: "wet dry"}):
        gap = {day: name for day, name in weather.items() if day != bars[5].day} | bad
        with pytest.raises(ValueError, match=f"{bars[5].day} has no regime"):
            _judge(bars, gap)
