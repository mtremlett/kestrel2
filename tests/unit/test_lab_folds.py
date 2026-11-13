"""The ladder's folds rung: a history cut into folds, each judged after costs beside the
history before it, and the verdict given on the worst; an edge that died is caught."""

from __future__ import annotations

import math
import random
from collections.abc import Sequence
from datetime import date
from decimal import Decimal

import pytest
from test_lab_rung import POUND, SHAPE, TEN_K, _bars

from desk.store import Bar
from lab import cell, folds, luck, rung
from lab.cell import Cell, Key, Trade
from lab.folds import Fold, Folded
from lab.rung import Priced, Verdict

EDGE, PART = 0.012, 4000


def _walk(seed: int, pushes: Sequence[float]) -> tuple[Bar, ...]:
    """The first rung's test walk, PART days for each push: the planted edge of each part of
    the history. Walks of one seed are the same bar for bar until their pushes differ."""
    rng, closes = random.Random(seed), [10.0]  # noqa: S311 - a repeatable test walk, not a secret
    while len(closes) < PART * len(pushes):
        up = len(closes) > 20 and closes[-1] > max(closes[-21:-1])
        pull = 0.005 * math.log(closes[-1] / 10)
        push = pushes[len(closes) // PART] if up else 0
        closes.append(closes[-1] * (1 + rng.gauss(0, 0.01) + push - pull))
    return _bars(closes)


def _window(bars: Sequence[Bar]) -> Cell:
    return Cell("breakout_20_10", "VUSA", bars[0].day, bars[-1].day)


def _judge(bars: Sequence[Bar], count: int = 2) -> Folded:
    return folds.judge(_window(bars), bars, TEN_K, POUND, count)


def _verdict(*gains: str) -> Verdict:
    day = date(2020, 1, 1)
    priced = tuple(
        Priced(Trade(day, day), 1, Decimal(1), 1 + Decimal(g), Decimal(g)) for g in gains
    )
    return rung.verdict(Key(Cell("breakout_20_10", "VUSA", day, day), "code", "data"), priced)


def _t(verdict: Verdict) -> Decimal:
    assert verdict.t is not None
    return verdict.t


def test_the_window_is_cut_into_equal_parts_and_a_fold_never_meets_its_in_sample() -> None:
    bars = _bars(SHAPE)  #: 25 bars
    days = [bar.day for bar in bars]
    pairs = folds.cut(_window(bars), bars, 4)
    assert [(i.start, i.end, o.start, o.end) for i, o in pairs] == [
        (days[0], days[5 * n - 1], days[5 * n], days[5 * n + 4]) for n in range(1, 5)
    ], "five parts of five bars: each fold beside everything before it"
    #: a window inside the bars is cut on its own bars, and parts differ by a bar at most
    inner = Cell("breakout_20_10", "VUSA", days[2], days[12])
    assert [(i.end, o.start, o.end) for i, o in folds.cut(inner, bars, 2)] == [
        (days[4], days[5], days[8]),
        (days[8], days[9], days[12]),
    ]
    for count, bad in [(0, bars), (25, bars), (1, bars[:1])]:
        with pytest.raises(ValueError, match="cannot be cut"):
            folds.cut(_window(bad), bad, count)
    assert len(folds.cut(_window(bars), bars, 24)) == 24, "a bar a part is the limit"


def test_a_trade_held_across_a_boundary_belongs_to_neither_side() -> None:
    bars = _bars(SHAPE)  #: bought on bar 20's close, sold on bar 23's, that sale filled on bar 24
    whole = rung.judge(cell.run(_window(bars), bars), bars, TEN_K, POUND)
    assert len(whole.trades) == 1
    (last,) = _judge(bars, 1).folds  #: bars 12 to 24 hold the whole trade
    assert last.outside.trades == whole.trades and last.inside.trades == ()
    split = _judge(bars, 7)  #: the last fold begins on bar 21, the trade already bought
    assert [fold.outside.key.cell.start for fold in split.folds][-2:] == [
        bars[18].day,
        bars[21].day,
    ]
    assert all(fold.inside.trades == fold.outside.trades == () for fold in split.folds)


def test_a_planted_edge_passes_every_fold_and_one_that_died_is_caught() -> None:
    for seed in range(3):
        alive, none = _judge(_walk(seed, [EDGE] * 3)), _judge(_walk(seed, [0, 0, 0]))
        assert alive.passed and all(f.inside.passed and f.outside.passed for f in alive.folds)
        assert all(len(f.outside.trades) >= rung.MIN_TRADES for f in alive.folds), seed
        assert not none.passed and not any(f.outside.passed for f in none.folds), seed
        #: the edge gone in the last third: the first rung, on the whole history, still passes it
        bars = _walk(seed, [EDGE, EDGE, 0])
        assert rung.judge(cell.run(_window(bars), bars), bars, TEN_K, POUND).passed, seed
        died = _judge(bars)
        assert not died.passed and died.worst is died.folds[1], seed
        #: side by side: strong on all it had seen, nothing on what it had not
        assert died.worst.inside.passed and _t(died.worst.inside) > 5 > 1 > _t(died.worst.outside)
        #: nothing after a fold's end is read: its two verdicts are the living edge's own
        assert died.folds[0] == alive.folds[0] and died.worst.inside == alive.folds[1].inside
        #: one bad fold in the middle fails it, however good the folds around it
        gap = _judge(_walk(seed, [EDGE, 0, EDGE]))
        assert not gap.passed and gap.worst is gap.folds[0] and gap.folds[1].outside.passed
        assert gap.folds[1].inside.passed, "and its in-sample alone would not have said so"


def test_the_worst_fold_is_the_fewest_standard_errors_up_and_too_few_trades_is_lowest() -> None:
    good, poor = _verdict("0.03", "0.02", "0.04"), _verdict("0.02", "-0.02", "0.01")
    lost, one = _verdict("-0.03", "-0.01", "-0.04"), _verdict("0.5")
    assert one.t is None and _t(lost) < 0 < _t(poor) < _t(good)
    assert Folded((Fold(lost, good), Fold(good, poor))).worst.outside is poor, "out-of-sample only"
    assert Folded((Fold(good, poor), Fold(good, lost), Fold(good, good))).worst.outside is lost
    assert Folded((Fold(good, lost), Fold(good, one), Fold(good, one))).worst.outside is one
    first, second = Fold(good, poor), Fold(lost, poor)
    assert Folded((first, second)).worst is first, "of two equally bad, the older"
    with pytest.raises(ValueError, match="no folds"):
        Folded(())


def test_every_fold_is_a_trial_the_luck_rung_counts() -> None:
    alive, died = _judge(_walk(0, [EDGE] * 3)), _judge(_walk(0, [EDGE, EDGE, 0]))
    assert alive.trials == tuple(fold.outside for fold in alive.folds) and len(alive.trials) == 2
    judged = luck.correct([*alive.trials, *died.trials], 0)
    assert [j.trials for j in judged] == [4] * 4, "two strategies of two folds are four trials"
    assert [j.passed for j in judged] == [True, True, True, False]
    worst = judged[alive.folds.index(alive.worst)]
    assert worst.verdict is alive.worst.outside and worst.passed, "its worst fold survives luck"
