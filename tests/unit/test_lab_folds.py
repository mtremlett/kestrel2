"""The ladder's folds rung: each fold judged beside the history before it, verdict on the worst."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

import pytest
from test_lab_luck import DAY
from test_lab_rung import FREE, POUND, SHAPE, TEN_K, _bars, _walk

from desk.store import Bar
from lab import cell, folds, luck, rung
from lab.cell import Cell, Key, Trade
from lab.folds import Fold, Folded
from lab.rung import Answer, Priced, Verdict

EDGE = 0.012


def _window(bars: Sequence[Bar]) -> Cell:
    return Cell("breakout_20_10", "VUSA", bars[0].day, bars[-1].day)


def _judge(bars: Sequence[Bar], count: int = 2) -> Folded:
    return folds.judge(_window(bars), bars, TEN_K, POUND, count)


def _verdict(*gains: str) -> Verdict:
    days = (DAY, DAY)
    made = tuple(
        Priced(
            Trade(*days),
            1,
            Decimal(1),
            1 + Decimal(g),
            FREE,
            days,
            sum(map(Decimal, gains), Decimal(0)) / len(gains),
        )
        for g in gains
    )
    return rung.verdict(Key(Cell("breakout_20_10", "VUSA", DAY, DAY), "code", "data"), made)


def _t(verdict: Verdict) -> Decimal:
    assert verdict.t is not None
    return verdict.t


def test_a_window_is_cut_into_equal_parts_and_a_trade_across_a_boundary_is_in_neither() -> None:
    bars = _bars(SHAPE)  #: 25 bars: bought on bar 20's close, sold on bar 23's, filled on bar 24
    days = [bar.day for bar in bars]  #: cut in five parts of five, each beside all before it
    want = [(days[0], days[5 * n - 1], days[5 * n], days[5 * n + 4]) for n in range(1, 5)]
    assert [(i.start, i.end, o.start, o.end) for i, o in folds.cut(_window(bars), bars, 4)] == want
    inner = Cell("breakout_20_10", "VUSA", days[2], days[12])  #: its own bars, parts a bar apart
    ends = [(i.end, o.start, o.end) for i, o in folds.cut(inner, bars, 2)]
    assert ends == [(days[4], days[5], days[8]), (days[8], days[9], days[12])]
    for count, bad in [(0, bars), (25, bars), (1, bars[:1])]:
        with pytest.raises(ValueError, match="cannot be cut"):
            folds.cut(_window(bad), bad, count)
    assert len(folds.cut(_window(bars), bars, 24)) == 24, "a bar a part is the limit"
    (trade,) = rung.judge(cell.run(_window(bars), bars), bars, TEN_K, POUND).trades
    (last,) = _judge(bars, 1).folds  #: bars 12 to 24 hold the whole trade
    assert last.outside.trades == (trade,) and last.inside.trades == ()
    split = _judge(bars, 7)  #: the last fold begins on bar 21, the trade already bought
    assert [f.outside.key.cell.start for f in split.folds][-2:] == [bars[18].day, bars[21].day]
    assert all(fold.inside.trades == fold.outside.trades == () for fold in split.folds)


def test_an_edge_passes_every_fold_a_dead_one_is_caught_and_each_fold_is_a_luck_trial() -> None:
    for seed in range(3):
        alive, none = _judge(_walk(seed, EDGE, EDGE, EDGE)), _judge(_walk(seed, 0, 0, 0))
        assert alive.passed and all(f.inside.passed and f.outside.passed for f in alive.folds)
        assert all(len(f.outside.trades) >= rung.MIN_TRADES for f in alive.folds), seed
        assert not none.passed and not any(f.outside.passed for f in none.folds), seed
        bars = _walk(seed, EDGE, EDGE, 0)  #: no edge in the last third; the first rung still passes
        assert rung.judge(cell.run(_window(bars), bars), bars, TEN_K, POUND).passed, seed
        died = _judge(bars)
        assert not died.passed and died.worst is died.folds[1], seed
        #: side by side: strong on all it had seen, nothing on what it had not
        assert died.worst.inside.passed and _t(died.worst.inside) > 5 > 1 > _t(died.worst.outside)
        #: nothing after a fold's end is read: its two verdicts are the living edge's own
        assert died.folds[0] == alive.folds[0] and died.worst.inside == alive.folds[1].inside
        gap = _judge(_walk(seed, EDGE, 0, EDGE))  #: one bad fold in the middle fails it
        assert not gap.passed and gap.worst is gap.folds[0] and gap.folds[1].outside.passed
        assert gap.folds[1].inside.passed, "and its in-sample alone would not have said so"
        #: each fold is a luck trial, four here, and the living edge's folds all survive luck
        assert alive.trials == tuple(f.outside for f in alive.folds) and len(alive.trials) == 2
        judged = luck.correct([*alive.trials, *died.trials], 0)
        assert [(j.trials, j.passed) for j in judged] == [(4, True)] * 3 + [(4, False)], seed


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
    many = _verdict(*["0.08", "-0.02", "0.03"] * 10)  #: a failed fold is worst, whatever its t
    assert many.passed and not good.passed and _t(good) > _t(many) > 3
    thin = Folded((Fold(many, many), Fold(many, good), Fold(many, many)))
    assert thin.worst.outside is good and not thin.passed
    assert Folded((Fold(many, good), Fold(many, poor))).worst.outside is poor
    assert Folded((Fold(lost, many), Fold(one, many))).passed, "every fold passed"
    #: failing fairly: a thin fold is not enough evidence, never a fail; a fold that failed
    #: on enough trades is worse; and a fold with no trades at all is a fault in the test
    failed, empty = _verdict(*["0.01", "-0.02", "0.01"] * 10), _verdict()
    assert (thin.answer, failed.answer, empty.answer) == (Answer.THIN, Answer.FAIL, Answer.FAULT)
    fair = Folded((Fold(many, good), Fold(many, failed), Fold(many, lost)))
    assert fair.worst.outside is failed and fair.answer is Answer.FAIL and _t(lost) < _t(failed)
    faulty = Folded((Fold(many, failed), Fold(many, empty), Fold(empty, many)))
    assert faulty.worst.outside is empty and faulty.answer is Answer.FAULT and not faulty.passed
