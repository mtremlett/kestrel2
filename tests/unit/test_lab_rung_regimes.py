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


def _declared(bars: Sequence[Bar]) -> Answer:
    """The answer of the rung as the ladder reads it (`RUNG`), over the window's calendar middle."""
    window = Cell("breakout_20_10", line_of("VUSA"), bars[0].day, bars[-1].day)
    return rung_regimes.RUNG.judge(rung.judge(cell.run(window, bars), bars, TEN_K, POUND))[0]


def _priced(rng: random.Random, edge: float, first: int, second: int) -> list[Priced]:
    """Trades of mean `edge` standard deviations: `first` bought before the cut, `second` after."""
    out = []
    for n in range(first + second):
        bought = CUT - timedelta(1 + n) if n < first else CUT + timedelta(n)
        gain = Decimal(str(rng.gauss(edge * SD, SD)))
        days = (bought, bought)
        out.append(Priced(Trade(*days), 1, Decimal(1), 1 + gain, FREE, days, None))
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
        assert _declared(_walk(seed, 0.008, days=10_000)) is Answer.PASS, seed
        assert edge.key == cell.key(edge.first.key.cell, _walk(seed, 0.008, days=10_000)).rung(
            rung_regimes.__name__
        )
        #: an edge in one window alone is a stretch's luck: it does not pass
        one = _cell(_walk(seed, 0.008, 0, days=5000))
        assert one.first.passed and not one.second.passed and not one.passed, seed
        assert _declared(_walk(seed, 0.008, 0, days=5000)) is not Answer.PASS, seed
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


def test_known_answer_thirty_trades_a_window_worked_by_hand() -> None:
    #: first window: 15 gains of +2% and 15 of 0, mean 1%, spread 1% * sqrt(30/29), so t = sqrt(29)
    #: = 5.385: PASS. second window: 15 of +1% and 15 of -1%, mean 0, t = 0: short of T_PASS, so
    #: DOUBT on the three bands (L19). A trade bought on the cut day itself is the second window's:
    #: the whole is the least, DOUBT; a second window that LOST (the first's gains negated) FAILS
    def priced(gains: list[str], start: date) -> list[Priced]:
        days = [(start + timedelta(n),) * 2 for n in range(len(gains))]
        return [
            Priced(Trade(*d), 1, Decimal(1), 1 + Decimal(g), FREE, d, None)
            for g, d in zip(gains, days, strict=True)
        ]

    won = priced(["0.02", "0"] * 15, CUT - timedelta(60))
    flat = priced(["0.01", "-0.01"] * 15, CUT)
    done = rung_regimes.apart(KEY, [*won, *flat], CUT)
    assert (len(done.first.trades), len(done.second.trades)) == (30, 30)
    assert abs(done.first.t - Decimal(29).sqrt()) < Decimal("1e-9") and done.second.t == 0  # type: ignore[operator]
    assert (done.first.answer, done.second.answer, done.answer) == (
        Answer.PASS,
        Answer.FAIL,
        Answer.DOUBT,
    )
    lost = priced(["-0.02", "0"] * 15, CUT)
    assert rung_regimes.apart(KEY, [*won, *lost], CUT).answer is Answer.FAIL


def test_power_case_a_real_edge_over_sixty_trades_is_never_failed_by_its_halves() -> None:
    #: a t=3 edge over 60 trades is about 2.1 standard errors a half of 30: a coin toss to pass
    #: both, so a half short of T_PASS is DOUBT (soft, MAX_WEAK), and only a half that lost fails
    rng = random.Random(11)  # noqa: S311 - a repeatable test sample, not a secret
    edge = 3 / 60**0.5
    said = [rung_regimes.apart(KEY, _priced(rng, edge, 30, 30), CUT).answer for _ in range(300)]
    #: recorded: about a third PASS, the rest DOUBT, no FAIL
    assert said.count(Answer.FAIL) <= 3 and 0.15 <= said.count(Answer.PASS) / 300 <= 0.6, said
