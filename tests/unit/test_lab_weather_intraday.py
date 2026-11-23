"""The intraday weather: trend labels worked by hand, per session, blind to the future."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest

from desk.rollup import Candle
from desk.store import Bar
from lab import weather
from lab import weather_intraday as wi


def _bars(*sessions: tuple[int, ...]) -> list[Candle]:
    out = []
    for d, closes in enumerate(sessions):
        t0 = datetime(2024, 1, 2 + d, 14, 30, tzinfo=UTC)
        for n, c in enumerate(closes):
            px = Decimal(c)
            out.append(Candle(t0 + timedelta(minutes=5 * n), px, px, px, px, 1, "ibkr"))
    return out


def test_labels_are_hand_worked_per_session_and_future_blind(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(wi, "WINDOW", 3)
    bars = _bars((10, 12, 14, 13, 9), (20, 10, 30, 30))
    got = list(wi.trend(bars).values())
    # session 1: means 12, 13, 12 -> up, down, down; session 2 restarts: warming twice,
    # then 30 vs mean 20 up, 30 vs mean 23.3 up
    assert got == ["warming", "warming", "up", "down", "down", "warming", "warming", "up", "up"]
    for k in range(len(bars)):
        assert list(wi.trend(bars[: k + 1]).values()) == got[: k + 1]
    with pytest.raises(ValueError):
        wi.trend(bars[::-1])


def _ohlc(*rows: tuple[int, int, int], day: int = 2) -> list[Candle]:
    t0 = datetime(2024, 1, day, 14, 30, tzinfo=UTC)
    return [
        Candle(
            t0 + timedelta(minutes=10 * n), Decimal(c), Decimal(h), Decimal(lo), Decimal(c), 1, "x"
        )
        for n, (h, lo, c) in enumerate(rows)
    ]


def test_opening_range_and_expansion_hand_worked_and_future_blind(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(wi, "MIN_BARS", 2)
    # range of the first 30 min (3 bars): high 12, low 8; later closes 13, 10, 7
    bars = _ohlc((10, 9, 9), (12, 10, 11), (11, 8, 9), (17, 12, 13), (11, 9, 10), (8, 6, 7))
    bars += _ohlc((5, 4, 4), (5, 4, 5), (5, 4, 5), (5, 4, 5), (9, 4, 5), (5, 4, 5), day=3)
    inside = list(wi.opening_range(bars).values())
    assert (
        inside == ["forming"] * 3 + ["above", "inside", "below"] + ["forming"] * 3 + ["inside"] * 3
    )
    # ranges 1,2,3,5,2,2: 3 vs mean 1.5 narrow, 5 vs mean 2 wide, then narrow; day 2 restarts:
    # 1,1,1,1,5,1: warming x2, narrow x2, 5 vs mean 1 wide, 1 vs mean 1.8 narrow
    wide = list(wi.expansion(bars).values())
    assert wide == ["warming", "warming", "narrow", "wide", "narrow", "narrow"] + [
        "warming", "warming", "narrow", "narrow", "wide", "narrow",
    ]  # fmt: skip
    for fn, got in ((wi.opening_range, inside), (wi.expansion, wide)):
        for k in range(len(bars)):
            assert list(fn(bars[: k + 1]).values()) == got[: k + 1]
        with pytest.raises(ValueError):
            fn(bars[::-1])


def test_volatility_thirds_hand_worked_and_future_blind(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(wi, "MIN_SESSIONS", 2)
    big, flat, mid = (100, 200, 100, 200), (100, 100, 100, 100), (100, 150, 100, 150)
    # a bar's volatility needs 2 returns (bars 3, 4); sessions: big .75/.707, flat 0, mid .42/.39
    bars = _bars(big, flat, flat, big, mid)
    got = list(wi.volatility(bars).values())
    w = ["warming"] * 2
    # sessions 1-2 hold under 2 earlier; 3: 0 under [.75, 0]; 4: .75 over [.75, 0, 0] (2 of 3
    # below); 5: .42 and .39 between 0 and .75
    assert got == w * 4 + w + ["quiet"] * 2 + w + ["wild"] * 2 + w + ["normal"] * 2
    for k in range(len(bars)):
        assert list(wi.volatility(bars[: k + 1]).values()) == got[: k + 1]
    with pytest.raises(ValueError):
        wi.volatility(bars[::-1])


def _day(day: date, px: Decimal | int) -> Bar:
    return Bar(day, Decimal(px), Decimal(px), Decimal(px), Decimal(px), 1)


def _planted() -> tuple[list[Bar], list[Candle], dict[datetime, str]]:
    """Daily closes that alternate up/down by day; 12 sessions of 10 bars each, a bar rising
    1% after a `good` bar and falling 1% after a `bad` one, whatever the day's label."""
    daily = [_day(date(2024, 1, 1 + i), 10 + 10 * (i % 2)) for i in range(24)]
    bars, labels = [], {}
    for d in range(12):
        px = Decimal(100)
        for n in range(10):
            t = datetime(2024, 1, 10 + d, 14, 30, tzinfo=UTC) + timedelta(minutes=5 * n)
            bars.append(Candle(t, px, px, px, px, 1, "x"))
            labels[t] = "good" if n % 2 == 0 else "bad"
            px *= Decimal("1.01") if n % 2 == 0 else Decimal("0.99")
    return daily, bars, labels


def test_a_layer_wins_only_where_it_adds_to_the_daily_label(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(weather, "WINDOW", 2)
    daily, bars, labels = _planted()
    won = wi.against_prior(labels, "good", daily, bars, folds=2, trials=4)
    assert won.wins and won.trials == 4 and won.trend == 0 and won.layer > Decimal("0.01")
    # labelled by session instead of by bar, the layer says nothing of what follows
    by_day = {t: "good" if t.day % 2 else "bad" for t in labels}
    lost = wi.against_prior(by_day, "good", daily, bars, 2, 4)
    assert abs(lost.layer) < Decimal("1e-9") and lost.layer - lost.trend < Decimal("1e-9")
    with pytest.raises(ValueError):
        wi.against_prior(labels, "absent", daily, bars, 2, 4)


def test_the_prior_never_reads_the_sessions_own_daily_bar(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(weather, "WINDOW", 2)
    daily, bars, _ = _planted()
    first = bars[:10]  # the session of 10 January, whose own daily bar is the 10th
    wild = [_day(b.day, b.close * 100) if b.day.day == 10 else b for b in daily]
    assert (
        wi.prior(wild, first)
        == wi.prior(daily, first)
        == dict.fromkeys(
            (b.start for b in first),
            "down",  # 9 January closed at 10, under its mean of 15
        )
    )
    assert {wi.prior(daily[:1], first)[first[0].start]} == {"warming"}
    assert [e.layer for e in wi.contest(daily, bars, 2)][:2] == ["trend", "opening range"]
