"""One clustered set of trials: the looks a set truly took, and the spread of their Sharpes
(Lopez de Prado and Lewis, "Detection of false investment strategies using unsupervised
learning methods", 2019)."""

from __future__ import annotations

from datetime import timedelta
from inspect import Parameter, signature
from pathlib import Path

import numpy as np
import pytest
from numpy.typing import NDArray
from test_lab_deflated import _bell

from lab import deflated, luck, trials
from lab.cell import Cell

DAYS = 500
Rows = NDArray[np.float64]
WINNER = _bell(9, 0.010)  #: a trial of forty trades with an edge, picked from a set of fifty
PICKED, _C = trials.name(WINNER.key.cell), WINNER.key.cell
#: the set's other trials: the same rule on the same line over windows of their own
CELLS = tuple(Cell(_C.strategy, _C.line, _C.start, _C.start + timedelta(n)) for n in range(60))
NAMES = tuple(trials.name(cell) for cell in CELLS)


def _strangers(seed: int, rows: int, days: int = DAYS) -> Rows:
    """So many strategies with nothing in common: each day's return its own draw."""
    return np.random.default_rng(seed).normal(0.0005, 0.01, (rows, days))


def _set(rows: Rows, picked: int | None = None) -> dict[str, list[float]]:
    """The rows as a set's returns by trial, the winner's name on the row picked."""
    names = [PICKED if n == picked else NAMES[n] for n in range(len(rows))]
    return {name: row.tolist() for name, row in zip(names, rows, strict=True)}


def _sharpes(rows: Rows) -> Rows:
    made: Rows = rows.mean(axis=1) / rows.std(axis=1, ddof=1)
    return made


def _weighed(rows: Rows) -> float:
    """A cluster's Sharpe by hand: its trials weighed by one over their variance (the paper's)."""
    made = (1 / rows.var(axis=1, ddof=1)) @ rows
    return float(made.mean() / made.std(ddof=1))


def test_fifty_copies_are_one_trial_and_fifty_strangers_are_fifty() -> None:
    strangers = _strangers(1, 50)
    one = trials.clusters(_set(np.tile(strangers[0], (50, 1))), 0)
    assert one.trials == 1 and one.held == len(one.clusters[0]) == 50
    assert one.spread(40) == 0, "one look alone was picked from nothing: no bar to set"
    #: copies geared and blurred, each still 0.9 like every other, are one look all the same
    blur = np.random.default_rng(2).normal(0, 0.003, (50, DAYS))
    geared = np.linspace(0.5, 3, 50)[:, None] * (strangers[0] + blur)
    assert 0.85 < np.corrcoef(geared).min() < 0.95 and trials.clusters(_set(geared), 0).trials == 1
    fifty = trials.clusters(_set(strangers), 0)
    assert fifty.trials == fifty.held == 50 and fifty.days == DAYS
    assert fifty.sharpes == pytest.approx(_sharpes(strangers).tolist())
    #: the spread is the variance of the looks' Sharpes, restated for the picked trial: the
    #: paper's yearly variance over its trades a year, the variance a day times the days a trade
    by_day = float(_sharpes(strangers).var(ddof=1))
    assert (fifty.spread(DAYS), fifty.spread(40)) == pytest.approx((by_day, by_day * DAYS / 40))
    #: five ideas tried ten ways each are five looks, in whatever order they are given
    ideas = _set(np.repeat(_strangers(3, 5), 10, axis=0) + blur)
    five = trials.clusters(ideas, 0)
    assert five.trials == 5 and five.held == 50 and five.clusters[0] == NAMES[:10]
    assert {len(cluster) for cluster in five.clusters} == {10}
    assert trials.clusters(dict(reversed(ideas.items())), 0) == five


def _passes(rows: Rows) -> tuple[bool, bool]:
    """Whether a set's best trial, by its Sharpe on forty trades of five days, passes the
    deflated Sharpe against the clustered set's bar; and against the looks' alone, its stand
    above its own cluster left out."""
    gains = rows.reshape(len(rows), 40, 5).sum(axis=2)
    pick = int(_sharpes(gains).argmax())
    looks = trials.clusters(_set(rows), 0)
    between = deflated.best_by_luck(looks.spread(40), looks.trials)
    won = gains[pick] - gains[pick].mean()
    second, third, fourth = (float(np.mean(won**power)) for power in (2, 3, 4))
    one, shape = float(_sharpes(gains)[pick]), (third / second**1.5, fourth / second**2)
    bars = (between + looks.above(CELLS[pick], one, 40), between)
    passed, bare = (deflated.deflate(one, bar, 40, *shape) >= deflated.PASS for bar in bars)
    return passed, bare


def test_the_bar_the_looks_set_is_the_luck_that_is_there() -> None:
    """Sets with no edge in any trial. Among fifty strangers the best Sharpe comes to the
    theorem's bar at the clustered count and spread. And the best of fifty trials 0.85 alike,
    one look, passes at about the rung's stated one in ten, where judged without its stand
    above its cluster it would pass one time in three."""
    best, bars = [], []
    for seed in range(40):
        noise = _strangers(100 + seed, 50) - 0.0005
        looks = trials.clusters(_set(noise), 0)
        best.append(_sharpes(noise).max())
        bars.append(deflated.best_by_luck(looks.spread(DAYS), looks.trials))
    assert np.mean(best) == pytest.approx(np.mean(bars), rel=0.1)
    passed, bare = 0, 0
    for seed in range(200):
        one, *rest = _strangers(1000 + seed, 51, 200) - 0.0005
        alike = np.sqrt(0.85) * one + np.sqrt(0.15) * np.array(rest)
        with_it, without = _passes(alike)
        passed, bare = passed + with_it, bare + without
    assert 9 <= passed <= 32, "of 200 sets at one in ten: 20, give or take"
    assert bare > 50, "the pick inside the cluster, uncounted, is a bar of nothing"


def test_a_cluster_is_alike_in_every_pair_and_weighs_its_steadier_trials_more() -> None:
    a, far, e = _strangers(4, 3)
    c = 0.65 * a + np.sqrt(1 - 0.65**2) * far  #: 0.65 like a: under LINK, another look
    rows = np.array([a, a + c, c, -a, e])  #: b is 0.9 like a and like c: a chain would join them
    found = trials.clusters(_set(rows), 0)
    together = np.corrcoef(rows)
    assert together[0, 1] > together[2, 1] > trials.LINK == 0.75 > together[0, 2] > 0.6
    assert (together[0, 2] + together[1, 2]) / 2 > trials.LINK, "alike on average is not enough"
    #: b joins the one it is most like; c, unlike a, is left a look of its own; and a rule
    #: run the other way round is a second look, as likely to be the lucky best as the first
    assert found.clusters == (NAMES[:2], NAMES[2:3], NAMES[3:4], NAMES[4:5]) and found.trials == 4
    #: a cluster's returns: each of its trials weighed by one over its variance (the paper's)
    by_hand = [_weighed(rows[:2]), *_sharpes(rows[2:]).tolist()]
    plain = rows[:2].mean(axis=0)
    assert found.sharpes == pytest.approx(by_hand, rel=1e-9)
    assert abs(plain.mean() / plain.std(ddof=1) - by_hand[0]) > 1e-4, "equal weights differ"
    assert found.spread(DAYS) == pytest.approx(np.var(by_hand, ddof=1), rel=1e-9)


def test_every_trial_counts_and_a_set_that_cannot_be_clustered_is_refused(tmp_path: Path) -> None:
    given = _set(_strangers(5, 5))
    five = trials.clusters(given, 0)
    #: trials that left no returns (a cell that failed, a rule that never traded) are each a
    #: look of their own, counted aloud; the spread is measured on the clusters that have one
    seven = trials.clusters(given, 2)
    assert (five.trials, seven.trials, seven.held) == (5, 7, 7)
    assert seven.spread(40) == five.spread(40)
    #: the register's door: every trial it holds on the question and the returns leave out
    register = tmp_path / "trials.jsonl"
    trials.start(register)
    trials.ask(register, "which rule earns")
    trials.enter(register, "which rule earns", [*given, "dropped", "failed"])
    assert trials.clustered(register, "which rule earns", given) == seven
    with pytest.raises(ValueError, match="never entered as trials.*'stranger'"):
        trials.clustered(register, "which rule earns", given | {"stranger": given[NAMES[0]]})
    #: more than one trial and no spread measured among them: nothing to deflate by
    alone = trials.clusters({"only": given[NAMES[0]]}, 1)
    assert alone.trials == 2
    with pytest.raises(ValueError, match="2 trials.*no spread measured"):
        alone.spread(40)
    short = {name: row[: trials.FEWEST - 1] for name, row in given.items()}
    never = "returns that never moved, or are no number"
    refused: dict[str, list[tuple[dict[str, list[float]], int]]] = {
        "same days for every trial": [({}, 0), (given, -1), (short, 0)],
        "same days for every trial, 60 or more": [(given | {"cut": [0.0] * (DAYS - 1)}, 0)],
        rf"\['odd'\]: {never}": [
            (given | {"odd": [0.0] * DAYS}, 0),
            (given | {"odd": [0.001] * DAYS}, 0),  #: a rule in cash at a steady rate: no look
            (given | {"odd": [0.01, float("nan")] * (DAYS // 2)}, 0),
            (given | {"odd": [0.01, float("inf")] * (DAYS // 2)}, 0),
        ],
    }
    for said, cases in refused.items():
        for returns, unjudged in cases:
            with pytest.raises(ValueError, match=said):
                trials.clusters(returns, unjudged)
    assert trials.clusters({n: r[: trials.FEWEST] for n, r in given.items()}, 0).trials == 5


def test_the_deflated_bar_is_set_by_the_clustered_set() -> None:
    trades = len(WINNER.gains)
    corrected = luck.correct([WINNER], 49)  #: the luck rung still counts all fifty
    (alone,) = deflated.judge([WINNER], 0)
    (separate,) = deflated.read(corrected, None)
    assert separate.bar == deflated.best_by_luck(1 / (trades - 1), 50)
    strangers = _strangers(1, 50)
    ideas = np.repeat(_strangers(3, 5), 10, axis=0)
    ideas += np.random.default_rng(2).normal(0, 0.003, (50, DAYS))
    best = 20 + int(_sharpes(ideas[20:30]).argmax())  #: the winner the best of the third idea
    #: fifty copies of the winner itself: days whose Sharpe, restated to a trade, is its own
    pace = (DAYS / trades) ** 0.5
    itself = (
        strangers[0] - strangers[0].mean() + (alone.sharpe or 0) / pace * strangers[0].std(ddof=1)
    )
    copies = trials.clusters(_set(np.tile(itself, (50, 1)), 7), 0)
    five, fifty = trials.clusters(_set(ideas, best), 0), trials.clusters(_set(strangers, 7), 0)
    among_copies, among_five, among_fifty = (
        deflated.read(corrected, looks)[0] for looks in (copies, five, fifty)
    )
    #: picked from fifty copies it is judged as picked from one; the luck rung's count stands
    assert among_copies.bar == pytest.approx(0, abs=1e-9)
    assert among_copies.deflated == pytest.approx(alone.deflated, abs=1e-9)
    assert among_copies.luck == corrected[0] and among_copies.luck.trials == 50
    #: from five ideas tried ten ways: the luck among five looks at their measured spread, and
    #: all that the Sharpe it is judged on stands above its idea's, restated to a trade: so it
    #: is judged no better than its cluster, the third, however its own trades fell
    judged, between = alone.sharpe or 0, deflated.best_by_luck(five.spread(trades), 5)
    cluster = _weighed(ideas[20:30]) * pace
    assert judged - cluster > 0.1
    assert five.above(WINNER.key.cell, judged, trades) == pytest.approx(judged - cluster, rel=1e-9)
    assert among_five.bar == pytest.approx(between + judged - cluster, rel=1e-9)
    assert judged - (among_five.bar or 0) == pytest.approx(cluster - between, rel=1e-9)
    #: a trial under its cluster's Sharpe is given nothing back for it
    assert five.above(WINNER.key.cell, cluster - 0.1, trades) == 0
    #: from fifty strangers: their measured spread at its own trades, and no cluster to stand in
    plain = deflated.best_by_luck(fifty.spread(trades), 50)
    assert among_fifty.bar == plain and fifty.above(WINNER.key.cell, 9.0, trades) == 0
    assert among_fifty.deflated < deflated.PASS < among_copies.deflated
    assert (among_copies.least.name, among_fifty.least.name) == ("PASS", "DOUBT")
    #: which, for strangers of plain noise, is about the bar fifty separate looks are given
    assert plain == pytest.approx(separate.bar or 0, rel=0.15)
    #: a set that is not the verdict's own is refused: another count, or the trial not in it
    with pytest.raises(ValueError, match=r"corrected for \[49\] trials.*set of 50: not the one"):
        deflated.read(luck.correct([WINNER], 48), fifty)
    with pytest.raises(ValueError, match="VUSA.*not a trial this set was clustered from"):
        deflated.read(corrected, trials.clusters(_set(strangers), 0))
    #: whether the set is clustered is said by the caller, never left out (LAD-09)
    assert signature(deflated.read).parameters["looks"].default is Parameter.empty
    #: a trial with no Sharpe has none against any set
    assert deflated.read(luck.correct([_bell(9, 0, 1)], 49), fifty)[0].bar is None
