"""The fifth rung, two regime windows judged apart (R-RUNNER-122), proven alone: a planted edge
passes, noise at about the stated rate, a power curve is recorded, a broken copy is caught."""

from __future__ import annotations

import random
from collections.abc import Sequence
from datetime import date, timedelta
from decimal import Decimal

import pytest
from test_lab_rung import FREE, POUND, TEN_K, _walk, line_of

from desk.store import Bar
from lab import cell, rung, rung_regimes
from lab.cell import Cell, Key, Trade
from lab.rung import Answer, Priced
from lab.rung_regimes import Regimes

DAY = date(2020, 1, 1)
KEY = Key(Cell("breakout_20_10", line_of("VUSA"), DAY, DAY), "tape", "data")
CUT = DAY + timedelta(1000)
PER_WINDOW, SD = 40, 0.01  #: trades in each window, and the spread of one trade's return
#: P(t >= 2) of forty gains of no mean: the stated rate of one window clearing the bar by chance
CHANCE = 0.0264


def _cell(bars: Sequence[Bar]) -> Regimes:
    window = Cell("breakout_20_10", line_of("VUSA"), bars[0].day, bars[-1].day)
    return rung_regimes.judge(cell.run(window, bars), bars, TEN_K, POUND)


def _priced(rng: random.Random, edge: float, first: int, second: int) -> list[Priced]:
    """Trades of mean `edge` standard deviations: `first` bought before the cut, `second` after."""
    out = []
    for n in range(first + second):
        bought = CUT - timedelta(1 + n) if n < first else CUT + timedelta(n)
        gain = Decimal(str(rng.gauss(edge * SD, SD)))
        days = (bought, bought)
        out.append(Priced(Trade(*days), 1, Decimal(1), 1 + gain, FREE, days))
    return out


def _rate(edge: float, cells: int, seed: int = 1) -> float:
    rng = random.Random(seed)  # noqa: S311 - a repeatable test sample, not a secret
    passes = [
        rung_regimes.apart(KEY, _priced(rng, edge, PER_WINDOW, PER_WINDOW), CUT).passed
        for _ in range(cells)
    ]
    return sum(passes) / cells


def _proven() -> None:
    """The rung's proof alone; any broken copy of the rung makes it fail."""
    for seed in range(3):
        edge = _cell(_walk(seed, 0.008, days=10_000))
        assert edge.passed and edge.first.passed and edge.second.passed, (seed, edge.answer)
        assert edge.key == cell.key(edge.first.key.cell, _walk(seed, 0.008, days=10_000)).rung(
            rung_regimes.__name__
        )
        #: an edge in one window alone is a stretch's luck: it does not pass
        one = _cell(_walk(seed, 0.008, 0, days=5000))
        assert one.first.passed and not one.second.passed and not one.passed, seed
    rng = random.Random(7)  # noqa: S311 - a repeatable test sample, not a secret
    noise = [rung_regimes.apart(KEY, _priced(rng, 0, 40, 40), CUT) for _ in range(500)]
    windows = sum(r.first.passed + r.second.passed for r in noise)
    both = sum(r.passed for r in noise)
    #: a 99.9% interval about 1000 windows at the stated rate, and about 500 cells at its square
    sigma = (1000 * CHANCE * (1 - CHANCE)) ** 0.5
    assert abs(windows - 1000 * CHANCE) <= 3.3 * sigma, windows
    assert both <= 3, both  #: expected 500 * 0.0264 ** 2 = 0.35
    curve = [_rate(e, 100) for e in (0, 0.25, 0.5, 1.0)]
    #: recorded: 0.00, 0.08, 0.77, 1.00 at 0, 0.25, 0.5 and 1 spreads of edge
    assert curve[0] <= 0.05 and curve[-1] >= 0.95 and curve == sorted(curve), curve


def test_the_rung_is_proven_alone() -> None:
    _proven()


def test_a_broken_copy_of_the_rung_is_caught(monkeypatch: pytest.MonkeyPatch) -> None:
    #: either window enough, and the decision inverted: each fails the proof
    for broken in (max, lambda a, b: Answer.FAIL if min(a, b) is Answer.PASS else Answer.PASS):
        monkeypatch.setattr(rung_regimes, "decide", broken)
        with pytest.raises(AssertionError):
            _proven()


def test_a_window_too_thin_holds_the_whole_at_thin_and_a_cut_is_two_windows() -> None:
    rng = random.Random(3)  # noqa: S311 - a repeatable test sample, not a secret
    thin = rung_regimes.apart(KEY, _priced(rng, 1.0, 40, 10), CUT)
    assert thin.first.passed and thin.second.answer is Answer.THIN and thin.answer is Answer.THIN
    assert thin.first.key != thin.second.key != thin.key
    assert len(thin.first.trades) == 40 and len(thin.second.trades) == 10
    assert rung.MIN_TRADES <= PER_WINDOW
    short = _walk(0, 0)[:1]
    with pytest.raises(ValueError, match="two windows"):
        _cell(short)
