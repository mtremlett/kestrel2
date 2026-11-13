"""The ladder's luck rung: every trial counted, and a winner believed only when its chance,
multiplied by the number of trials it was picked from, is still small."""

from __future__ import annotations

import random
from datetime import date
from decimal import Decimal

import pytest

from lab import luck, rung
from lab.cell import Cell, Key, Trade
from lab.rung import Priced, Verdict

DAY = date(2020, 1, 1)


def _verdict(seed: int, edge: float, trades: int = 40) -> Verdict:
    """A trial of so many trades, each gain drawn around the edge with a spread of 2%, judged
    by the first rung's own rule."""
    rng = random.Random(seed)  # noqa: S311 - a repeatable test draw, not a secret
    back = [Decimal(f"{100 * (1 + rng.gauss(edge, 0.02)):.4f}") for _ in range(trades)]
    priced = tuple(Priced(Trade(DAY, DAY), 1, Decimal(100), b, b - 100) for b in back)
    return rung.verdict(Key(Cell("breakout_20_10", "VUSA", DAY, DAY), "code", str(seed)), priced)


def test_the_chance_is_students_published_one() -> None:
    #: the textbook table's own rows: 2.5% beyond 2.2281 at 10 degrees of freedom, and so on
    table = [(2.2281389, 10, 0.025), (2.0452296, 29, 0.025), (4.0321430, 5, 0.005)]
    for t, freedom, chance in [*table, (3.6459586, 30, 0.0005), (1.0, 1, 0.25), (0.0, 7, 0.5)]:
        assert luck.tail(t, freedom) == pytest.approx(chance, rel=1e-6), (t, freedom)
        assert luck.tail(-t, freedom) == pytest.approx(1 - chance, rel=1e-6), "a loss is no edge"
    assert luck.tail(6.0, 5000) == pytest.approx(1.05e-9, rel=0.01), "long histories and far tails"


def test_a_winner_is_corrected_for_every_trial_it_was_picked_from() -> None:
    winner = _verdict(9, 0.008)
    assert winner.passed and winner.t is not None and Decimal("2.6") < winner.t < Decimal("2.7")
    (alone,) = luck.correct([winner], 0)
    assert alone.passed and alone.trials == 1 and alone.verdict is winner
    assert alone.chance == alone.corrected == luck.tail(float(winner.t), 39) < 0.006
    #: the same winner picked from eight trials stands, and from nine does not: 5% is the line
    eight, nine = luck.correct([winner], 7)[0], luck.correct([winner], 8)[0]
    assert (eight.trials, eight.passed, nine.trials, nine.passed) == (8, True, 9, False)
    assert eight.corrected == 8 * alone.chance <= luck.FAMILY < 9 * alone.chance == nine.corrected
    #: a trial counts whatever became of it: a loser, one trade only, a cell that never ran
    loser, single = _verdict(1, -0.01), _verdict(2, 0.5, trades=1)
    judged = luck.correct([loser, winner, single], 6)
    assert [j.trials for j in judged] == [9, 9, 9] and not any(j.passed for j in judged)
    assert judged[1] == nine and judged[0].corrected == judged[2].chance == 1.0
    assert single.t is None and judged[0].chance > 0.99
    with pytest.raises(ValueError, match="-1 trials"):
        luck.correct([winner], -1)


def test_no_correction_makes_a_winner_of_a_trial_the_first_rung_failed() -> None:
    few = _verdict(0, 0.03, trades=29)  #: far too strong to be chance, and one trade too few
    assert few.t is not None and few.t > 6 and not few.passed
    (judged,) = luck.correct([few], 0)
    assert judged.corrected < 1e-6 and not judged.passed


def test_among_noise_chance_winners_do_not_survive_and_a_real_edge_does() -> None:
    families = [[_verdict(100 * f + n, 0) for n in range(40)] for f in range(40)]
    assert sum(any(v.passed for v in family) for family in families) > 20, "the first rung alone"
    fooled = sum(any(j.passed for j in luck.correct(family, 0)) for family in families)
    assert fooled <= 2, "5% of forty sets of forty trials with no edge in any of them"
    real = _verdict(7, 0.015)
    found = [luck.correct([*family, real], 0)[-1] for family in families]
    assert all(j.passed and j.trials == 41 for j in found), "a real edge is not thrown out"
