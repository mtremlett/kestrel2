"""The ladder's block placebo (R-RUNNER-120), proven alone: a planted edge passes; 500 cells of
pure noise pass at about the stated rate; the power at three edges is recorded; and a broken
copy of the rung, its decision inverted, fails each of those proofs."""

from __future__ import annotations

import math
import random
from collections.abc import Callable, Sequence
from dataclasses import replace
from decimal import Decimal
from functools import cache
from pathlib import Path

import pytest
from test_lab_rung import VUSA, _bars

from desk.store import Bar
from lab import cell, rung_placebo, tape
from lab.cell import Cell, Record, Trade
from lab.rung_placebo import BLOCK, ME, PLACEBOS, Placebo

#: one rule that buys strength and one that buys weakness, a noise cell in two to each
RULES, NOISE = ("breakout_20_10", "bollinger_pullback"), 500
EDGE, CELLS = 0.012, 40
#: THE POWER CURVE, recorded: of CELLS three-year cells at each planted edge (a day's push,
#: on noise of 1% a day), those that pass
POWER = {0.004: 7, 0.008: 31, 0.012: 40}
Decide = Callable[[Placebo], bool]


def _line(seed: int, push: float, days: int) -> tuple[Bar, ...]:
    """Pure noise, 1% a day about a steady rise, from 100; `push`, the planted edge, is added
    to each day after a close over the 20 before it: a breakout, then a rise."""
    rng, closes = random.Random(seed), [100.0]  # noqa: S311 - a repeatable test walk, not a secret
    while len(closes) < days:
        up = len(closes) > 20 and closes[-1] > max(closes[-21:-1])
        closes.append(closes[-1] * (1 + rng.gauss(0.0005, 0.01) + push * up))
    return _bars(closes)


@cache
def _placebo(seed: int, push: float, days: int = 750, rule: str = RULES[0]) -> Placebo:
    bars = _line(seed, push, days)
    c = Cell(rule, VUSA, bars[0].day, bars[-1].day)
    return rung_placebo.judge(cell.run(c, bars), bars)


def _within(passed: int, cells: int, rate: float) -> bool:
    """Whether `passed` of `cells` lies in the central 99% of the binomial at `rate`."""
    chance = [math.comb(cells, k) * rate**k * (1 - rate) ** (cells - k) for k in range(passed + 1)]
    return sum(chance) > 0.005 and sum(chance[:-1]) < 0.995


def _edge(decide: Decide) -> bool:
    return decide(_placebo(1, EDGE))


def _noise(decide: Decide) -> bool:
    passed = sum(decide(_placebo(seed, 0, 400, RULES[seed % 2])) for seed in range(NOISE))
    return _within(passed, NOISE, float(rung_placebo.SHARE))


def _power(decide: Decide) -> bool:
    made = [sum(decide(_placebo(seed, push)) for seed in range(CELLS)) for push in POWER]
    return made == list(POWER.values()) == sorted(made)


@pytest.mark.parametrize("proof", [_edge, _noise, _power])
def test_the_rung_passes_each_proof_and_a_broken_copy_its_decision_inverted_passes_none(
    proof: Callable[[Decide], bool],
) -> None:
    assert proof(lambda made: made.passed), "the rung as it is built"
    assert not proof(lambda made: not made.passed), "the broken copy is caught"


def test_the_rule_is_read_from_its_tape_and_each_placebo_is_its_line_in_blocks_kept_as_a_tape(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    #: each day's volume is its number, so a made day tells which day of the line it is
    bars = tuple(replace(bar, volume=n) for n, bar in enumerate(_line(1, EDGE, 750)))
    real, shown = cell.run, []

    def run(c: Cell, history: Sequence[Bar]) -> Record:
        shown.append(history)
        return real(c, history)

    monkeypatch.setattr(cell, "run", run)
    c = Cell(RULES[0], VUSA, bars[0].day, bars[-1].day)
    with tape.on(tmp_path):
        first = rung_placebo.judge(held := cell.run(c, bars), bars)
        again = rung_placebo.judge(cell.run(c, bars), bars)
    assert len(shown) == 1 + first.run, "the rule and each placebo simulated once, then read"
    assert again == first and first.passed and held.key != first.key == held.key.rung(ME)
    assert "lab/rung.py" not in cell.reached(cell.ROOT, ME), "new costs leave a placebo kept"
    days, odd = range(len(bars)), (len(bars) - 1) % BLOCK
    line = [float(bar.close) for bar in bars]
    for history in shown[1:]:
        took, closes = [bar.volume for bar in history], [float(bar.close) for bar in history]
        assert [bar.day for bar in history] == [
            bar.day for bar in bars
        ], "the dates keep their place"
        assert took[: odd + 1] == [*days[: odd + 1]] and sorted(took) == [*days] != took
        inside = [n for n in days[odd + 2 :] if (n - odd - 1) % BLOCK]
        assert all(took[n] == took[n - 1] + 1 for n in inside), "each block whole, in its order"
        moved = [line[day] / line[day - 1] for day in took[1:]]
        assert [closes[n] / closes[n - 1] for n in days[1:]] == pytest.approx(moved, abs=1e-5)
    with pytest.raises(ValueError, match="did not make the tape"):
        rung_placebo.judge(held, bars[:-1])


def test_a_tape_that_could_not_pass_is_not_judged_and_noise_is_stopped_once_it_cannot() -> None:
    bars = _line(3, 0, 750)
    whole, short = (Cell(RULES[0], VUSA, bars[0].day, bars[end].day) for end in (-1, 39))
    none = rung_placebo.judge(Record(cell.key(whole, bars), len(bars), ()), bars)
    assert (none.blocks, none.run, none.share, none.passed) == (74, 0, None, False), "no trade"
    few = Record(cell.key(short, bars), 40, (Trade(bars[25].day, bars[30].day),))
    assert rung_placebo.judge(few, bars).share is None, "3 blocks have 6 orders: none is rare"
    noise = [_placebo(seed, 0, 400, RULES[seed % 2]) for seed in range(NOISE)]
    stopped = [made for made in noise if not made.passed]
    assert all(made.share == Decimal(2) / (PLACEBOS + 1) for made in stopped), "one as good ends it"
    assert sum(made.run for made in stopped) < 5 * len(stopped), "and most meet it early"
