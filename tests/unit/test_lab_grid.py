"""The fast grid engine against the desk's own: the same position after every bar, on the
golden series and on prices as long as the archive's, or a refusal, never a guess."""

from __future__ import annotations

import random
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
#: What the grid refuses at full length on the golden series: a close exactly on a
#: Supertrend band, which the jumpy series were built to hold.
REFUSED = {("jumpy 10", "supertrend_10_3"), ("jumpy 332", "supertrend_10_3")}


def _desk(bars: Sequence[Bar]) -> dict[str, list[bool]]:
    """Each rule in the market or out of it after each bar, by the desk's own decisions."""
    states: dict[str, list[bool]] = {name: [] for name in strategy.STRATEGIES}
    for decision in strategy.decide({"X": bars}):
        was = states[decision.strategy][-1] if states[decision.strategy] else False
        now = {Action.BUY: True, Action.SELL: False}.get(decision.action, was)
        states[decision.strategy].append(now)
    return states


def _agree(bars: Sequence[Bar], label: str) -> set[str]:
    """The grid holds what the desk holds after every bar, on the series whole and cut
    short, wherever it answers. Returns the rules it refused on the series whole."""
    desk, refused = _desk(bars), set()
    for cut in (*CUTS, len(bars)):
        prices = grid.prices(bars[:cut])
        for name, states in desk.items():
            try:
                found = grid.held(name, prices).tolist()
            except grid.TooClose:
                refused |= {name} if cut == len(bars) else set()
                continue
            assert found == states[:cut], f"{name} on {label}, its first {cut} bars"
    return refused


def test_the_grid_holds_what_the_desk_holds_on_the_golden_series() -> None:
    refused = set()
    for series in GOLDEN:
        kind, seed = series.split()
        bars = _walk(int(seed), 1200) if kind == "walk" else _jumpy(int(seed))
        refused |= {(series, name) for name in _agree(bars, series)}
    assert refused == REFUSED


def _archive(seed: int, days: int = 1500) -> tuple[Bar, ...]:
    """Prices as the free archive gives them: sixteen or seventeen digits, no two alike."""
    rng = random.Random(seed)  # noqa: S311 - a repeatable test walk, not a secret
    close, drift, out = 100.0, 0.0, []
    for n in range(days):
        if n % 150 == 0:
            drift = rng.choice((-0.002, 0.002))
        close *= 1 + drift + rng.gauss(0, 0.012)
        high, low = close * (1 + rng.random() / 50), close * (1 - rng.random() / 50)
        price, top, bottom = (Decimal(repr(value)) for value in (close, high, low))
        out.append(Bar(START + timedelta(n), price, top, bottom, price, 1000))
    return tuple(out)


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_it_holds_what_the_desk_holds_on_prices_as_long_as_the_archives(seed: int) -> None:
    bars = _archive(seed)
    assert not grid.prices(bars).whole, "these prices are too long to be whole numbers"
    assert _agree(bars, f"archive {seed}") == set()
    for name, states in _desk(bars).items():
        assert True in states and False in states[states.index(True) :], f"{name} never traded"


def test_a_tie_between_whole_prices_is_called_exactly() -> None:
    #: the desk's own hand-worked ties: a close exactly on its 200-day average, on its
    #: 20-day average, on a 20-day high and on a 10-day low
    on_average = [100] * 200 + [150, 200, 250, 300, 350, 410, 410, 410, 410, 110]
    for closes in (on_average, [10] * 20 + [9, 9.5, 10.5], [10] * 20 + [10.5, 11, 9.5, 9.4]):
        assert _agree(_bars(closes), str(closes[-4:])) <= {"supertrend_10_3"}


def test_a_tie_floating_point_cannot_call_is_refused_never_guessed() -> None:
    #: day 11 closes exactly on the Supertrend's carried lower band (test_strategy)
    on_band = grid.prices(_bars([100] * 10 + [110, 101.3, 100], reach=1))
    with pytest.raises(grid.TooClose, match="too close"):
        grid.held("supertrend_10_3", on_band)
    #: the same flat days as above, at a price too long to be a whole number of anything
    long = Decimal("1.2345678901234567")
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
