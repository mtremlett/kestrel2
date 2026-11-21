"""The market weather: trend labels worked by hand, blind to the future, and readable by the
regime replay."""

from __future__ import annotations

import random
from datetime import date, timedelta
from decimal import Decimal

import pytest
from test_lab_rung import FREE, line_of

from desk.store import Bar
from lab import regime, rung_regimes, weather
from lab.cell import Cell, Key, Trade
from lab.rung import Answer, Priced

START = date(2024, 1, 1)
KEY = Key(Cell("breakout_20_10", line_of("VUSA"), START, START), "tape", "data")


def _bars(*closes: int) -> list[Bar]:
    return [
        Bar(START + timedelta(days=n), Decimal(c), Decimal(c), Decimal(c), Decimal(c), 1)
        for n, c in enumerate(closes)
    ]


def test_labels_are_the_hand_worked_ones_and_future_blind(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(weather, "WINDOW", 3)
    closes = (10, 11, 12, 9, 9, 10, 20, 5)
    #: means of the last three closes: 11, 10.67, 10, 9.33, 13, 11.67; the close against it
    by_hand = ["warming", "warming", "up", "down", "down", "up", "up", "down"]
    labels = weather.trend(_bars(*closes))
    assert list(labels.values()) == by_hand
    for t in range(len(closes)):
        assert weather.trend(_bars(*closes[: t + 1])) == dict(list(labels.items())[: t + 1])
    assert list(labels)[0] == START and set(by_hand) == {"up", "down", "warming"}
    with pytest.raises(ValueError, match="oldest first"):
        weather.trend(_bars(1, 2, 3)[::-1])


def test_the_regime_replay_reads_the_label_as_one_plain_word() -> None:
    day = START
    label = weather.trend(_bars(*range(1, 250)))
    assert regime._named(label, day) == "warming"
    assert regime._named(label, START + timedelta(days=248)) == "up"


def _gains(rng: random.Random) -> list[Priced]:
    """Eighty trades of a steady gain: forty bought before START, forty from it."""
    out = []
    for n in range(80):
        bought = START - timedelta(40 - n) if n < 40 else START + timedelta(n)
        days = (bought, bought)
        out.append(
            Priced(
                Trade(*days),
                1,
                Decimal(1),
                1 + Decimal(str(rng.gauss(0.01, 0.01))),
                FREE,
                days,
                None,
            )
        )
    return out


def test_the_weather_cuts_trades_by_the_trend_state_they_were_bought_in() -> None:
    rng = random.Random(3)  # noqa: S311 - a repeatable test sample, not a secret
    priced = _gains(rng)
    labels = {p.trade.bought: ("up" if p.trade.bought < START else "down") for p in priced}
    both = rung_regimes.by_weather(KEY, priced, labels)
    assert (len(both.up.trades), len(both.down.trades)) == (40, 40) and both.up.key != both.down.key
    assert both.answer is min(both.up.answer, both.down.answer)
    warming = {day: "warming" for day in labels}
    assert rung_regimes.by_weather(KEY, priced, warming).answer is Answer.THIN
    with pytest.raises(KeyError):
        rung_regimes.by_weather(KEY, priced, {})


def test_volatility_labels_are_the_hand_worked_ones_and_future_blind(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(weather, "VOL_WINDOW", 2)
    monkeypatch.setattr(weather, "VOL_RANK", 2)
    closes = (100, 100, 100, 100, 110, 100, 100, 100)
    #: deviations of two returns from day 2: 0, 0, 5%, 9.5%, 4.5%, 0, each against the 2 before
    by_hand = ["warming"] * 4 + ["stormy", "stormy", "calm", "calm"]
    labels = weather.volatility(_bars(*closes))
    assert list(labels.values()) == by_hand
    for t in range(len(closes)):
        assert weather.volatility(_bars(*closes[: t + 1])) == dict(list(labels.items())[: t + 1])


def test_drawdown_labels_are_the_hand_worked_ones_and_future_blind(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(weather, "DD_WINDOW", 3)
    monkeypatch.setattr(weather, "DD_LIMIT", Decimal("0.1"))
    closes = (10, 12, 11, 10, 9, 12, 12, 10)
    #: each close against the high of the last three: 11/12, 10/12, 9/11, 12/12, 12/12, 10/12
    by_hand = ["warming"] * 2 + ["shallow", "deep", "deep", "shallow", "shallow", "deep"]
    labels = weather.drawdown(_bars(*closes))
    assert list(labels.values()) == by_hand
    for t in range(len(closes)):
        assert weather.drawdown(_bars(*closes[: t + 1])) == dict(list(labels.items())[: t + 1])


def test_breadth_is_the_share_of_lines_up_and_future_blind(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(weather, "WINDOW", 2)
    lines = {"a": (10, 12, 14, 8, 8), "b": (10, 9, 8, 9, 10), "c": (5, 6, 5, 4, 3)}
    #: up/down per line from day 1: a up up down down; b down down up up; c up down down down
    by_hand = ["warming", "broad", "narrow", "narrow", "narrow"]
    labels = weather.breadth({k: _bars(*v) for k, v in lines.items()})
    assert list(labels.values()) == by_hand
    for t in range(5):
        cut = {k: _bars(*v[: t + 1]) for k, v in lines.items()}
        assert weather.breadth(cut) == dict(list(labels.items())[: t + 1])


def test_a_joined_layer_moves_its_bad_days_out_of_up_and_stays_future_blind(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(weather, "WINDOW", 3)
    monkeypatch.setattr(weather, "VOL_WINDOW", 2)
    monkeypatch.setattr(weather, "VOL_RANK", 2)
    bars = _bars(100, 100, 100, 100, 110, 100, 100, 100, 101, 102)
    assert weather.named(bars) == weather.trend(bars)  # JOINED empty: today's names exactly
    monkeypatch.setattr(weather, "JOINED", ("volatility",))
    joined = weather.named(bars)
    stormy = [d for d, v in weather.volatility(bars).items() if v == weather.STORMY]
    assert stormy and all(weather.trend(bars)[d] == "up" for d in stormy[:1])
    assert all(joined[d] != "up" for d in stormy) and joined != weather.trend(bars)
    for t in range(len(bars)):
        assert weather.named(bars[: t + 1]) == dict(list(joined.items())[: t + 1])
