"""The fast grid engine against the desk's own: the same position after every bar, on the
golden series and on prices as long as the archive's, or a refusal, never a guess."""

from __future__ import annotations

import random
from collections import Counter
from collections.abc import Sequence
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal

import pytest
from test_strategy import GOLDEN, START, _bars, _jumpy, _walk

from desk import strategy
from desk.store import Bar
from desk.strategy import Action
from lab import grid

#: Either side of each rule's warm-up, and the middle of a walk.
CUTS = (0, 1, 2, 9, 10, 11, 19, 20, 21, 199, 200, 201, 777)
#: All the grid refuses on the golden series: a close exactly on a Supertrend band, which
#: the jumpy series were built to hold, from the cut that first shows it.
REFUSED = {("jumpy 10", "supertrend_10_3"): 5, ("jumpy 332", "supertrend_10_3"): 8}


def _desk(bars: Sequence[Bar]) -> dict[str, list[bool]]:
    """Each rule in the market or out of it after each bar, by the desk's own decisions."""
    states: dict[str, list[bool]] = {name: [] for name in strategy.STRATEGIES}
    for decision in strategy.decide({"X": bars}):
        was = states[decision.strategy][-1] if states[decision.strategy] else False
        now = {Action.BUY: True, Action.SELL: False}.get(decision.action, was)
        states[decision.strategy].append(now)
    return states


def _agree(bars: Sequence[Bar], label: str) -> Counter[str]:
    """The grid holds what the desk holds after every bar, on the series whole and cut
    short, wherever it answers. Returns how many of those each rule refused."""
    desk, refused = _desk(bars), Counter[str]()
    for cut in (*CUTS, len(bars)):
        prices = grid.prices(bars[:cut])
        for name, states in desk.items():
            try:
                found = grid.held(name, prices).tolist()
            except grid.TooClose:
                refused[name] += 1
                continue
            assert found == states[:cut], f"{name} on {label}, its first {cut} bars"
    return refused


def test_the_grid_holds_what_the_desk_holds_on_the_golden_series() -> None:
    refused: dict[tuple[str, str], int] = {}
    for series in GOLDEN:
        kind, seed = series.split()
        bars = _walk(int(seed), 1200) if kind == "walk" else _jumpy(int(seed))
        refused |= {(series, name): count for name, count in _agree(bars, series).items()}
    assert refused == REFUSED


def _archive(seed: int, days: int = 1500, calm: bool = False) -> tuple[Bar, ...]:
    """Prices as the free archive gives them: sixteen or seventeen digits.
    A calm one moves little, in a narrow range, between sudden jumps of up to a tenth."""
    rng = random.Random(seed)  # noqa: S311 - a repeatable test walk, not a secret
    close, drift, out = 100.0, 0.0, []
    for n in range(days):
        if n % 150 == 0 and not calm:
            drift = rng.choice((-0.002, 0.002))
        move = drift + rng.gauss(0, 0.004 if calm else 0.012)
        close *= 1 + move + (rng.uniform(-0.1, 0.1) if calm and rng.random() < 0.15 else 0)
        reach = 400 if calm else 50
        high, low = close * (1 + rng.random() / reach), close * (1 - rng.random() / reach)
        price, top, bottom = (Decimal(repr(value)) for value in (close, high, low))
        out.append(Bar(START + timedelta(n), price, top, bottom, price, 1000))
    return tuple(out)


def test_a_bar_that_would_enter_and_would_not_stay_turns_the_position_over() -> None:
    #: after a jump, the Supertrend's upper band can sit under its lower one: a close
    #: between them buys when out and sells when in. Seed 3 holds such a bar.
    assert not _agree(_archive(3, 400, calm=True), "calm 3")


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_it_holds_what_the_desk_holds_on_prices_as_long_as_the_archives(seed: int) -> None:
    bars = _archive(seed)
    assert not grid.prices(bars).whole, "these prices are too long to be whole numbers"
    assert not _agree(bars, f"archive {seed}")
    for name, states in _desk(bars).items():
        assert True in states and False in states[states.index(True) :], f"{name} never traded"


def test_a_tie_between_whole_prices_is_called_exactly() -> None:
    #: the desk's own hand-worked ties: a close exactly on its 200-day average, on its
    #: 20-day average, on a 20-day high and on a 10-day low
    on_average = [100] * 200 + [150, 200, 250, 300, 350, 410, 410, 410, 410, 110]
    for closes in (on_average, [10] * 20 + [9, 9.5, 10.5], [10] * 20 + [10.5, 11, 9.5, 9.4]):
        assert set(_agree(_bars(closes), str(closes[-4:]))) <= {"supertrend_10_3"}


def test_a_tie_floating_point_cannot_call_is_refused_never_guessed() -> None:
    #: Wilder's smoothing is never exact. The Supertrend: the last day closes on its carried
    #: lower band (test_strategy); on its upper band of 106; a hundred thousand millionth
    #: over it; and day 9 closes on its own day's upper band, which decides its carrying
    flat = _bars([100] * 12, reach=1)
    own = (*flat[:9], replace(flat[9], close=Decimal(106)), *flat[10:])
    ends = ([110, 101.3], [106], [106.000000001])
    for bars in (*(_bars([100] * 10 + end, reach=1) for end in ends), own):
        with pytest.raises(grid.TooClose, match="too close"):
            grid.held("supertrend_10_3", grid.prices(bars))
    #: the RSI: a rise of 2 then a fall of 19 leave the loss exactly 19 times the gain
    with pytest.raises(grid.TooClose, match="too close"):
        grid.held("rsi2_pullback", grid.prices(_bars([100] * 200 + [102, 83])))
    #: and the blind review's find: days that move a thousand-millionth of the price, where
    #: a change is mostly rounding. The desk is out after the last; the grid had said in
    rng, step, tiny = random.Random(7), 100 * 10**15 + 12345, []  # noqa: S311 - as above
    for _ in range(230):
        step += rng.randint(2 * 10**8, 4 * 10**8) | 1
        tiny.append(Decimal(step).scaleb(-15))
    tiny.append(Decimal("100.000062510057111"))
    bars = tuple(Bar(START + timedelta(n), c, c + 1, c - 1, c, 1) for n, c in enumerate(tiny))
    assert _desk(bars)["rsi2_pullback"][-1] is False
    with pytest.raises(grid.TooClose, match="too close"):
        grid.held("rsi2_pullback", grid.prices(bars))
    #: flat days on their 20-day average, at prices whose sums are past what is held exactly
    long = Decimal("1.0000000000001")
    flat = tuple(
        replace(bar, high=bar.high * long, low=bar.low * long, close=bar.close * long)
        for bar in _bars([10] * 20 + [9, 9.5, 10.5])
    )
    with pytest.raises(grid.TooClose, match="too close"):
        grid.held("bollinger_pullback", grid.prices(flat))
    #: two prices that floating point reads as one
    near = _bars([1, 1])
    near = (near[0], replace(near[1], close=Decimal("1.00000000000000000001")))
    with pytest.raises(grid.TooClose, match="tell apart"):
        grid.prices(near)
    #: prices so long that the desk's own 28 digits cannot add them exactly: far apart, or
    #: (the second blind review's) small whole numbers of a step of 2**-60
    fine = Decimal(5**60).scaleb(-60)
    for long in (Decimal("1E+27"), fine):
        with pytest.raises(grid.TooClose, match="too long"):
            grid.prices((near[0], replace(near[1], close=long)))
    #: and its other find: closes far outside their days' ranges, so that the Supertrend's
    #: lower band is the small difference of two large numbers. The desk stays in on the
    #: last day, a close of 500000004 over a band of 500000000.04; the grid had said out
    days = "6,6,5 8,4,62 6,4,61 9,5,27 8,2,36 2,1,79 8,4,90 9,2,39 1,1,87 7,5,71"
    rows = [[int(n) for n in day.split(",")] for day in days.split()]
    wild = [[10**16 + h * 10**6, 10**16 + lo * 10**6, 10**9 + c] for h, lo, c in rows]
    wild += [[10**16 + 3 * 10**7, 10**16 - 3 * 10**7, 5 * 10**16]]
    wild += [[10**16 + 5 * 10**7, 10**16 - 5 * 10**7, 10**9 + 7]]
    wild += [[47018568603106392, 47018568603106392, 10**9]]
    wild += [[47018568703106392, 47018568503106392, 500000004]]
    bars = tuple(
        Bar(START + timedelta(n), Decimal(c), Decimal(h), Decimal(lo), Decimal(c), 1)
        for n, (h, lo, c) in enumerate(wild)
    )
    assert _desk(bars)["supertrend_10_3"][-1] is True
    with pytest.raises(grid.TooClose, match="too close"):
        grid.held("supertrend_10_3", grid.prices(bars))
