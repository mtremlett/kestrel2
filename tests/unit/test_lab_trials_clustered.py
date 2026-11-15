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
WINNER = _bell(9, 0.010)  #: a trial of forty trades with an edge, picked from a set of fifty
PICKED = trials.name(WINNER.key.cell)


def _strangers(seed: int, rows: int) -> Rows:
    """So many strategies with nothing in common: each day's return its own draw."""
    return np.random.default_rng(seed).normal(0.0005, 0.01, (rows, DAYS))


def _set(rows: Rows, names: tuple[str, ...] = ()) -> dict[str, list[float]]:
    """The rows as a set's returns, the first trials by the names given."""
    named = [*names, *(f"trial {n:02}" for n in range(len(names), len(rows)))]
    return {name: row.tolist() for name, row in zip(named, rows, strict=True)}


def _sharpes(rows: Rows) -> Rows:
    made: Rows = rows.mean(axis=1) / rows.std(axis=1, ddof=1)
    return made


def test_fifty_copies_are_one_trial_and_fifty_strangers_are_fifty() -> None:
    strangers = _strangers(1, 50)
    one = trials.clusters(_set(np.tile(strangers[0], (50, 1))), 0)
    assert one.trials == 1 and one.held == len(one.clusters[0]) == 50
    assert one.spread(40) == 0, "one look alone was picked from nothing: no bar to set"
    assert one.inside == pytest.approx([0], abs=1e-20), "and no copy stands above another"
    #: copies geared and blurred, each still 0.9 like every other, are one look all the same
    blur = np.random.default_rng(2).normal(0, 0.003, (50, DAYS))
    geared = np.linspace(0.5, 3, 50)[:, None] * (strangers[0] + blur)
    assert 0.85 < np.corrcoef(geared).min() < 0.95 and trials.clusters(_set(geared), 0).trials == 1
    fifty = trials.clusters(_set(strangers), 0)
    assert fifty.trials == fifty.held == 50 and fifty.days == DAYS and not any(fifty.inside)
    assert fifty.sharpes == pytest.approx(_sharpes(strangers).tolist())
    #: the spread is the variance of the looks' Sharpes, restated for the picked trial: the
    #: paper's yearly variance over its trades a year, the variance a day times the days a trade
    by_day = float(_sharpes(strangers).var(ddof=1))
    assert (fifty.spread(DAYS), fifty.spread(40)) == pytest.approx((by_day, by_day * DAYS / 40))
    #: five ideas tried ten ways each are five looks, in whatever order they are given
    ideas = _set(np.repeat(_strangers(3, 5), 10, axis=0) + blur)
    five = trials.clusters(ideas, 0)
    assert five.trials == 5 and five.held == 50 and {len(c) for c in five.clusters} == {10}
    assert five.clusters[0] == tuple(f"trial {n:02}" for n in range(10))
    assert trials.clusters(dict(reversed(ideas.items())), 0) == five


def test_the_bar_the_looks_set_is_the_luck_that_is_there() -> None:
    """Set after set with no edge in any trial: the best Sharpe among fifty strangers comes to
    the theorem's bar at the clustered count and spread; and the best of fifty trials 0.85
    alike, one look, stands above their middle by the bar of the pick inside the cluster."""
    best, bars, lifts, inside = [], [], [], []
    for seed in range(40):
        noise = _strangers(100 + seed, 51) - 0.0005
        looks = trials.clusters(_set(noise[:50]), 0)
        best.append(_sharpes(noise[:50]).max())
        bars.append(deflated.best_by_luck(looks.spread(DAYS), looks.trials))
        alike = np.sqrt(0.85) * noise[50] + np.sqrt(0.15) * noise[:50]
        look = trials.clusters(_set(alike), 0)
        assert (looks.trials, look.trials) == (50, 1)
        lifts.append(_sharpes(alike).max() - _sharpes(alike).mean())
        inside.append(deflated.best_by_luck(look.inside[0], 50))
    assert np.mean(best) == pytest.approx(np.mean(bars), rel=0.1)
    assert np.mean(lifts) == pytest.approx(np.mean(inside), rel=0.1)
    assert np.mean(inside) > np.mean(bars) / 3, "a third of the strangers' luck, not nothing"


def test_a_cluster_is_alike_in_every_pair_and_weighs_its_steadier_trials_more() -> None:
    a, far, e = _strangers(4, 3)
    c = 0.65 * a + np.sqrt(1 - 0.65**2) * far  #: 0.65 like a: under LINK, another look
    rows = np.array([a, a + c, c, -a, e])  #: b is 0.9 like a and like c: a chain would join them
    found = trials.clusters(_set(rows, tuple("abcde")), 0)
    together = np.corrcoef(rows)
    assert together[0, 1] > together[2, 1] > trials.LINK == 0.75 > together[0, 2] > 0.6
    assert (together[0, 2] + together[1, 2]) / 2 > trials.LINK, "alike on average is not enough"
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
    #: and inside the cluster, the variance of its own two trials' Sharpes; none for one alone
    assert found.inside == pytest.approx([np.var(_sharpes(rows[:2]), ddof=1), 0, 0, 0], rel=1e-9)


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
        trials.clustered(register, "which rule earns", given | {"stranger": given["trial 00"]})
    #: more than one trial and no spread measured among them: nothing to deflate by
    alone = trials.clusters({"only": given["trial 00"]}, 1)
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
    trades, cell = len(WINNER.gains), WINNER.key.cell
    corrected = luck.correct([WINNER], 49)  #: the luck rung still counts all fifty
    (alone,) = deflated.judge([WINNER], 0)
    (separate,) = deflated.read(corrected, None)
    assert separate.bar == deflated.best_by_luck(1 / (trades - 1), 50)
    strangers = _strangers(1, 50)
    blur = np.random.default_rng(2).normal(0, 0.003, (50, DAYS))
    copies = trials.clusters(_set(np.tile(strangers[0], (50, 1)), (PICKED,)), 0)
    ideas = np.repeat(_strangers(3, 5), 10, axis=0) + blur  #: the picked among the first ten
    five = trials.clusters(_set(ideas, (PICKED,)), 0)
    fifty = trials.clusters(_set(strangers, (PICKED,)), 0)
    among_copies, among_five, among_fifty = (
        deflated.read(corrected, looks)[0] for looks in (copies, five, fifty)
    )
    #: picked from fifty copies it is judged as picked from one; the luck rung's count stands
    assert among_copies.bar == pytest.approx(0, abs=1e-9)
    assert among_copies.deflated == pytest.approx(alone.deflated, abs=1e-9)
    assert among_copies.luck == corrected[0] and among_copies.luck.trials == 50
    #: from five ideas tried ten ways: the luck among five looks at their measured spread,
    #: and the luck of the pick among its own idea's ten, at the spread measured among those
    spread, size = five.beside(cell, trades)
    assert size == 10 and spread == pytest.approx(_sharpes(ideas[:10]).var(ddof=1) * DAYS / trades)
    assert among_five.bar == deflated.best_by_luck(five.spread(trades), 5) + deflated.best_by_luck(
        spread, 10
    )
    #: from fifty strangers: their measured spread at its own trades, no pick inside a cluster
    assert fifty.beside(cell, trades) == (0, 1)
    assert among_fifty.bar == deflated.best_by_luck(fifty.spread(trades), 50)
    assert among_fifty.deflated < deflated.PASS < among_copies.deflated
    assert (among_copies.least.name, among_fifty.least.name) == ("PASS", "DOUBT")
    #: which, for strangers of plain noise, is about the bar fifty separate looks are given
    assert among_fifty.bar == pytest.approx(separate.bar or 0, rel=0.15)
    #: a set that is not the verdict's own is refused: another count, or the trial not in it
    with pytest.raises(ValueError, match=r"corrected for \[49\] trials.*set of 50: not the one"):
        deflated.read(luck.correct([WINNER], 48), fifty)
    with pytest.raises(ValueError, match="VUSA.*not a trial this set was clustered from"):
        deflated.read(corrected, trials.clusters(_set(strangers), 0))
    #: a trial with no Sharpe has none against any set
    assert deflated.read(luck.correct([_bell(9, 0, 1)], 49), fifty)[0].bar is None
