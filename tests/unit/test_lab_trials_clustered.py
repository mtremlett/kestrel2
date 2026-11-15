"""One clustered set of trials: the looks a set truly took, and the spread of their Sharpes
(Lopez de Prado and Lewis, "Detection of false investment strategies using unsupervised
learning methods", 2019)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from numpy.typing import NDArray
from test_lab_deflated import _bell

from lab import deflated, luck, trials

DAYS = 500
Rows = NDArray[np.float64]


def _strangers(seed: int, rows: int) -> Rows:
    """So many strategies with nothing in common: each day's return its own draw."""
    return np.random.default_rng(seed).normal(0.0005, 0.01, (rows, DAYS))


def _set(rows: Rows, names: str = "") -> dict[str, list[float]]:
    return {names[n] if names else f"trial {n:02}": row.tolist() for n, row in enumerate(rows)}


def _sharpes(rows: Rows) -> Rows:
    made: Rows = rows.mean(axis=1) / rows.std(axis=1, ddof=1)
    return made


def test_fifty_copies_are_one_trial_and_fifty_strangers_are_fifty() -> None:
    strangers = _strangers(1, 50)
    one = trials.clusters(_set(np.tile(strangers[0], (50, 1))), 0)
    assert one.trials == 1 and len(one.clusters[0]) == 50
    assert one.spread(40) == 0, "one look alone was picked from nothing: no bar to set"
    #: copies geared and blurred, each still 0.9 like every other, are one look all the same
    blur = np.random.default_rng(2).normal(0, 0.003, (50, DAYS))
    geared = np.linspace(0.5, 3, 50)[:, None] * (strangers[0] + blur)
    assert 0.85 < np.corrcoef(geared).min() < 0.95 and trials.clusters(_set(geared), 0).trials == 1
    fifty = trials.clusters(_set(strangers), 0)
    assert fifty.trials == 50 and fifty.days == DAYS
    assert fifty.sharpes == pytest.approx(_sharpes(strangers).tolist())
    #: the spread is the variance of the looks' Sharpes, and the paper's yearly variance over
    #: the picked trial's trades a year: the variance a day times the days a trade
    by_day = float(_sharpes(strangers).var(ddof=1))
    assert fifty.spread(DAYS) == pytest.approx(by_day)
    assert fifty.spread(40) == pytest.approx(by_day * DAYS / 40)
    #: five ideas tried ten ways each are five looks, whatever order they are given in
    ideas = np.repeat(_strangers(3, 5), 10, axis=0) + blur
    five = trials.clusters(_set(ideas[::-1]), 0)
    assert five.trials == 5 and {len(cluster) for cluster in five.clusters} == {10}
    assert five.clusters[0] == tuple(f"trial {n:02}" for n in range(10))
    #: and the bar they set is the luck that is there: the best Sharpe among strangers with
    #: no edge, set after set, comes to the theorem's bar at the clustered count and spread
    best, bars = [], []
    for seed in range(40):
        noise = _strangers(100 + seed, 50) - 0.0005
        looks = trials.clusters(_set(noise), 0)
        best.append(_sharpes(noise).max())
        bars.append(deflated.best_by_luck(looks.spread(DAYS), looks.trials))
    assert np.mean(best) == pytest.approx(np.mean(bars), rel=0.05)


def test_a_cluster_is_alike_in_every_pair_and_weighs_its_steadier_trials_more() -> None:
    a, far, e = _strangers(4, 3)
    c = 0.5 * a + np.sqrt(0.75) * far  #: half like a: under LINK, another look
    rows = np.array([a, a + c, c, -a, e])  #: b is 0.87 like a and like c, which a chain would join
    found = trials.clusters(_set(rows, "abcde"), 0)
    together = np.corrcoef(rows)
    assert together[0, 1] > together[2, 1] > trials.LINK == 0.75 > together[0, 2]
    #: b joins the one it is most like; c, unlike a, is left a look of its own; and a rule
    #: run the other way round is a second look, as likely to be the lucky best as the first
    assert found.clusters == (("a", "b"), ("c",), ("d",), ("e",)) and found.trials == 4
    #: a cluster's returns: each of its trials weighed by one over its variance (the paper's)
    weights = 1 / rows[:2].var(axis=1, ddof=1)
    made = weights @ rows[:2] / weights.sum()
    plain = rows[:2].mean(axis=0)
    by_hand = [made.mean() / made.std(ddof=1), *_sharpes(rows[2:]).tolist()]
    assert found.sharpes == pytest.approx(by_hand, rel=1e-9)
    assert abs(plain.mean() / plain.std(ddof=1) - by_hand[0]) > 1e-4, "equal weights differ"
    assert found.spread(DAYS) == pytest.approx(np.var(by_hand, ddof=1), rel=1e-9)


def test_every_trial_counts_and_a_set_that_cannot_be_clustered_is_refused(tmp_path: Path) -> None:
    given = _set(_strangers(5, 5))
    five = trials.clusters(given, 0)
    #: trials that left no returns (a cell that failed, a rule that never traded) are each a
    #: look of their own, counted aloud; the spread is measured on the clusters that have one
    seven = trials.clusters(given, 2)
    assert (five.trials, seven.trials) == (5, 7) and seven.spread(40) == five.spread(40)
    #: the register's door: every trial it holds on the question and the returns leave out
    register = tmp_path / "trials.jsonl"
    trials.start(register)
    trials.ask(register, "which rule earns")
    trials.enter(register, "which rule earns", [*given, "dropped", "failed"])
    assert trials.clustered(register, "which rule earns", given) == seven
    with pytest.raises(ValueError, match="never entered as trials.*'stranger'"):
        trials.clustered(register, "which rule earns", given | {"stranger": given["trial 00"]})
    #: more than one trial and no spread measured among them: nothing to deflate by
    alone = trials.clusters({"only": given["trial 00"]}, 1)
    assert alone.trials == 2
    with pytest.raises(ValueError, match="2 trials.*no spread measured"):
        alone.spread(40)
    flat, short = [0.0] * DAYS, {name: row[: trials.FEWEST - 1] for name, row in given.items()}
    odd = [0.01, float("nan")] * (DAYS // 2)
    refused = {
        "same days for every trial": [({}, 0), (given, -1), (short, 0)],
        "same days for every trial, 60 or more": [(given | {"cut": flat[:-1]}, 0)],
        r"\['flat'\]: returns that never moved": [(given | {"flat": flat}, 0)],
        r"\['odd'\]: returns that never moved, or are no number": [(given | {"odd": odd}, 0)],
    }
    for said, cases in refused.items():
        for returns, unjudged in cases:
            with pytest.raises(ValueError, match=said):
                trials.clusters(returns, unjudged)
    assert trials.clusters({n: r[: trials.FEWEST] for n, r in given.items()}, 0).trials == 5


def test_the_deflated_bar_is_set_by_the_clustered_set() -> None:
    winner = _bell(9, 0.010)
    trades = len(winner.gains)
    corrected = luck.correct([winner], 49)  #: the luck rung still counts all fifty
    (alone,) = deflated.judge([winner], 0)
    (unclustered,) = deflated.read(corrected)
    assert unclustered.bar == deflated.best_by_luck(1 / (trades - 1), 50)
    strangers = _strangers(1, 50)
    copies = trials.clusters(_set(np.tile(strangers[0], (50, 1))), 0)
    fifty = trials.clusters(_set(strangers), 0)
    (among_copies,) = deflated.read(corrected, copies)
    (among_strangers,) = deflated.read(corrected, fifty)
    #: picked from fifty copies it is judged as picked from one; the luck rung's count stands
    assert (among_copies.bar, among_copies.deflated) == (0, alone.deflated)
    assert among_copies.luck == corrected[0] and among_copies.luck.trials == 50
    #: picked from fifty strangers, against their measured spread at its own trades
    assert among_strangers.bar == deflated.best_by_luck(fifty.spread(trades), 50)
    assert among_strangers.deflated < deflated.PASS < among_copies.deflated
    assert (among_copies.least.name, among_strangers.least.name) == ("PASS", "DOUBT")
    #: which, for strangers of plain noise, is about the bar fifty separate looks are given
    assert among_strangers.bar == pytest.approx(unclustered.bar or 0, rel=0.15)
    #: a trial with no Sharpe has none against any set
    assert deflated.read(luck.correct([_bell(9, 0, 1)], 49), fifty)[0].bar is None
