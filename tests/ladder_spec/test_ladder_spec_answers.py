"""The ladder's known answers, by its spec (the docstring of `lab/ladder.py`): a planted edge
PASSES; a walk with no memory, a line that climbs of itself and a rule of small wins with a
rare loss at the stop FAIL; and the two rates PASS is held to are measured and printed.

The check does not run this folder. The tests here are the spec's, written before the code,
and none is ever set aside to make it pass. Those of the planted edge, the hidden loss, the
folds and the shuffle fail until the ladder is built as written; those of nothing (the bell,
the drift and the two lopsided worlds) hold already, since the ladder as it stands passes
nothing at all, and are the controls that must go on holding once an edge can pass.
`python -m pytest tests/ladder_spec -s` prints the rates: ten minutes as the ladder stands,
and half an hour or so once every planted edge is shuffled a hundred times.
"""

from __future__ import annotations

import importlib
from datetime import date
from pathlib import Path
from statistics import fmean
from typing import Any

import pytest
from ladder_worlds import (
    BELL,
    DRIFT,
    EDGE,
    EIGHT,
    HIDDEN,
    LOPSIDED,
    LOSSES,
    POUNDS,
    RULE,
    SIXTEEN,
    SPARSE,
    judged,
    lopsided,
    world,
)

from desk.command import CAPITAL
from desk.orders import Settings
from desk.store import Bar
from lab import cell, deflated, ladder, rung
from lab.cell import Cell
from lab.rung import Answer

#: The two rates of the spec: of sets with no edge at most one in twenty is given a PASS,
#: and of trials with the planted edge four in five or more.
FALSE_PASS, POWER = 0.05, 0.8
#: The worlds each rate is measured on: eighty planted trials, and twenty sets of each kind
#: of nothing, sixteen trials a set. No set fooled of the eighty bounds the true rate under
#: one in twenty-seven, nineteen times in twenty.
EDGES, NOTHINGS = range(1, 6), range(1, 21)
#: The desk's first set was 110 trials: a lone trial is judged here as one of so many.
SET = 110
SOUR = (date(2023, 1, 1), date(2024, 1, 1))


def _answers(home: Path, kind: str, seed: int) -> list[str]:
    rows = judged(home / f"{kind}-{seed}", world(kind, seed))
    return [row.get("answer", "none") for row in rows]


def test_a_planted_edge_passes_and_the_power_is_recorded(tmp_path: Path) -> None:
    answers = [answer for seed in EDGES for answer in _answers(tmp_path, EDGE, seed)]
    power = answers.count("PASS") / len(answers)
    print(f"\nladder spec: POWER {power:.3f}, a planted edge given PASS on {len(answers)} trials")
    assert power >= POWER, f"{sorted(set(answers))}: a planted edge is not thrown away"


@pytest.mark.parametrize("kind", [BELL, DRIFT, LOPSIDED, HIDDEN])
def test_nothing_fails_and_the_false_pass_rate_is_recorded(tmp_path: Path, kind: str) -> None:
    sets = [_answers(tmp_path, kind, seed) for seed in NOTHINGS]
    cells = [answer for answers in sets for answer in answers]
    fooled = sum("PASS" in answers for answers in sets) / len(sets)
    print(
        f"\nladder spec: FALSE PASS {fooled:.3f} of {len(sets)} sets of {kind} with no edge, "
        f"{cells.count('PASS') / len(cells):.4f} of their {len(cells)} trials"
    )
    assert fooled <= FALSE_PASS, f"{kind}: more than one set in twenty handed over a winner"
    assert cells.count("FAIL") >= 0.9 * len(cells), f"{kind}: no edge is a FAIL, said as one"


def test_small_wins_and_a_rare_loss_at_the_stop_never_pass_on_few_trades() -> None:
    room, verdicts = Settings(CAPITAL), []
    for seed in range(400):
        bars = lopsided(seed, SPARSE)
        window = Cell(RULE, EIGHT[seed % len(EIGHT)], bars[0].day, ladder.END)
        verdicts.append(rung.judge(cell.run(window, bars), bars, room, {}))
    #: the world is what it says: thirty-odd trades a line, one in ten a loss at the stop,
    #: and nothing made of them all after the broker's costs
    gains = [float(priced.gain) for verdict in verdicts for priced in verdict.trades]
    assert all(rung.MIN_TRADES <= len(verdict.trades) < 40 for verdict in verdicts)
    assert abs(sum(gain < -0.05 for gain in gains) / len(gains) - LOSSES) < 0.01
    assert abs(fmean(gains)) < 0.001 < 0.1 < -min(gains) < 0.11
    #: a line in fifty has hidden every loss so far; with the rule's own stop planted (G2)
    #: none of them is believed, on the four rungs read from a trial's own trades
    first = sum(verdict.answer is Answer.PASS for verdict in verdicts)
    own = [deflated.judge([verdict], SET - 1)[0].least for verdict in verdicts]
    print(
        f"\nladder spec: RARE LARGE LOSS, of {len(own)} trials with no edge the first rung "
        f"passed {first} and its four rungs {own.count(Answer.PASS)}"
    )
    assert own.count(Answer.PASS) == 0, "a loss not yet seen was taken for an edge"


def test_the_folds_are_five_years_pooled_by_rule_and_judged_on_the_worst(tmp_path: Path) -> None:
    assert ladder.FOLDS >= 5, "walk-forward on five yearly folds or more (M6)"
    #: a rule's trades are pooled across its lines in each year, so the answer is one answer,
    #: with one reason, on every line of the rule; and an edge planted in every year passes
    fair = {tuple(row["rungs"]["folds"]) for row in judged(tmp_path / "fair", world(EDGE, 1))}
    assert len(fair) == 1 and next(iter(fair))[0] == "PASS"
    #: the same edge with one sour year in the five, where every breakout fell back: the
    #: whole history still earned, and the worst year is the one judged on and named
    for row in judged(tmp_path / "sour", world(EDGE, 1, SOUR)):
        answer, why = row["rungs"]["folds"]
        assert row["rungs"]["first"][0] == "PASS" and answer in ("FAIL", "DOUBT")
        assert "2023" in why and row["answer"] != "PASS"


def test_the_shuffle_tells_an_edge_in_the_order_of_days_from_a_rise_with_none() -> None:
    shuffle: Any = importlib.import_module("lab.shuffle")  #: the rung's door, as the spec names it
    room = Settings(CAPITAL)

    def share(bars: tuple[Bar, ...]) -> float:
        window = Cell(RULE, EIGHT[0], bars[0].day, ladder.END)
        return float(shuffle.share(window, bars, room, POUNDS))

    #: a planted edge is in the order of its days: no shuffle of them does as well, and the
    #: same trial is shuffled the same again
    assert shuffle.SHUFFLES == 100
    for bars in list(world(EDGE, 1).values())[2:4]:
        assert share(bars) == share(bars) == pytest.approx(1 / (shuffle.SHUFFLES + 1))
    #: a line that climbs of itself climbs as well in any order: its rule has timed nothing,
    #: and chance alone puts one such line in twenty among the best of its shuffles
    climbing = list(world(DRIFT, 1).values())[2:]
    timed = sum(share(bars) <= 0.05 for bars in climbing)
    assert len(climbing) == len(SIXTEEN) and timed <= 3, f"{timed} lines of no order passed"
