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
            Priced(Trade(*days), 1, Decimal(1), 1 + Decimal(str(rng.gauss(0.01, 0.01))), FREE, days)
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
