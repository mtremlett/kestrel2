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
from itertools import pairwise
from pathlib import Path

import pytest
from test_lab_rung import VUSA, _bars

from desk.store import Bar
from lab import cell, rung_placebo, tape
from lab.cell import Cell, Record, Trade
from lab.rung_placebo import BLOCK, ME, PLACEBOS, Placebo

#: one rule that buys strength and one that buys weakness, a noise cell in two to each; and a
#: cell in two starts WARM days into its line, which lie flat before the window's rise
RULES, NOISE, WARM = ("breakout_20_10", "bollinger_pullback"), 500, 150
EDGE, CELLS = 0.012, 40
#: THE POWER CURVE, recorded: of CELLS three-year cells at each planted edge (a day's push,
#: on noise of 1% a day), those that pass
POWER = {0.004: 7, 0.008: 31, 0.012: 40}
Decide = Callable[[Placebo], bool]


def _line(seed: int, push: float, days: int, warm: int = 0) -> tuple[Bar, ...]:
    """Pure noise, 1% a day, from 100: `warm` days flat, then `days` about a steady rise; `push`,
    the planted edge, is added to each day after a close over the 20 before it: a breakout."""
    rng, closes = random.Random(seed), [100.0]  # noqa: S311 - a repeatable test walk, not a secret
    while len(closes) < warm + days:
        up = len(closes) > 20 and closes[-1] > max(closes[-21:-1])
        rise = 0.0005 * (len(closes) >= warm)
        closes.append(closes[-1] * (1 + rng.gauss(rise, 0.01) + push * up))
    return _bars(closes)


@cache
def _placebo(
    seed: int, push: float, days: int = 750, rule: str = RULES[0], warm: int = 0
) -> Placebo:
    bars = _line(seed, push, days, warm)
    c = Cell(rule, VUSA, bars[warm].day, bars[-1].day)
    return rung_placebo.judge(cell.run(c, bars), bars)


def _noise_cell(seed: int) -> Placebo:
    return _placebo(seed, 0, 400, RULES[seed % 2], WARM * (seed % 4 > 1))


def _within(passed: int, cells: int, rate: float) -> bool:
    """Whether `passed` of `cells` lies in the central 99% of the binomial at `rate`."""
    chance = [math.comb(cells, k) * rate**k * (1 - rate) ** (cells - k) for k in range(passed + 1)]
    return sum(chance) > 0.005 and sum(chance[:-1]) < 0.995


def _edge(decide: Decide) -> bool:
    return decide(_placebo(1, EDGE))


def _noise(decide: Decide) -> bool:
    passed = sum(decide(_noise_cell(seed)) for seed in range(NOISE))
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


@pytest.mark.parametrize("warm", [0, 305])
def test_the_rule_is_read_from_its_tape_and_each_placebo_is_its_window_in_blocks_kept_as_a_tape(
    warm: int, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    #: each day's volume is its number, so a made day tells which day of the line it is
    bars = tuple(replace(bar, volume=n) for n, bar in enumerate(_line(1, EDGE, 750)))
    real, shown = cell.run, []

    def run(c: Cell, history: Sequence[Bar]) -> Record:
        shown.append(history)
        return real(c, history)

    monkeypatch.setattr(cell, "run", run)
    c = Cell(RULES[0], VUSA, bars[warm].day, bars[-1].day)
    with tape.on(tmp_path):
        first = rung_placebo.judge(held := cell.run(c, bars), bars)
        again = rung_placebo.judge(cell.run(c, bars), bars)
    assert len(shown) == 1 + first.run, "the rule and each placebo simulated once, then read"
    assert again == first and first.passed and held.key != first.key == held.key.rung(ME)
    assert "lab/rung.py" not in cell.reached(cell.ROOT, ME), "new costs leave a placebo kept"
    days = range(len(bars))
    stay = max(warm, 1) + (len(bars) - max(warm, 1)) % BLOCK  #: before the window, and its odd days
    for history in shown[1:]:
        took = [bar.volume for bar in history]
        assert [bar.day for bar in history] == [
            bar.day for bar in bars
        ], "the dates keep their place"
        assert took[:stay] == [*days[:stay]] and sorted(took) == [*days] != took
        inside = [n for n in days[stay + 1 :] if (n - stay) % BLOCK]
        assert all(took[n] == took[n - 1] + 1 for n in inside), "each block whole, in its order"
        places = {bar.high.as_tuple().exponent for bar in history[1:]}
        assert places == {-5}, "rounded as the line's own prices are: its highs have five places"
        for price in ("open", "high", "low", "close"):
            made = [float(getattr(b, price) / last.close) for last, b in pairwise(history)]
            line = [float(getattr(bars[n], price) / bars[n - 1].close) for n in took[1:]]
            assert made == pytest.approx(line, abs=1e-5), "each day whole, from the close before"
    with pytest.raises(ValueError, match="did not make the tape"):
        rung_placebo.judge(held, bars[:-1])


def test_a_tape_that_could_not_pass_is_not_judged_and_riding_a_rising_window_makes_nothing() -> (
    None
):
    bars = _line(3, 0, 750)
    whole, short = (Cell(RULES[0], VUSA, bars[0].day, bars[end].day) for end in (-1, 59))
    none = rung_placebo.judge(Record(cell.key(whole, bars), len(bars), ()), bars)
    assert (none.blocks, none.run, none.share, none.passed) == (74, 0, None, False), "no trade"
    few = Record(cell.key(short, bars), 60, (Trade(bars[25].day, bars[30].day),))
    assert rung_placebo.judge(few, bars).share is None, "5 blocks have 120 orders: too few"
    stopped = [made for made in map(_noise_cell, range(NOISE)) if not made.passed]
    assert all(made.share == Decimal(2) / (PLACEBOS + 1) for made in stopped), "one as good ends it"
    assert sum(made.run for made in stopped) < 5 * len(stopped), "and most meet it early"
    #: 50 flat days, then a window that rises 1% a day, bought on its first day and never sold
    rising = _bars([100.0] * 50 + [100 * 1.01**n for n in range(1, 101)])
    window = Cell(RULES[0], VUSA, rising[50].day, rising[-1].day)
    rode = Record(cell.key(window, rising), 100, (Trade(rising[50].day, None),))
    made = rung_placebo.judge(rode, rising).made
    assert made is not None and abs(made) < Decimal("0.001"), "the window's own rise, no more"


def test_what_is_ranked_is_the_tapes_own_trade_and_a_price_rounding_to_nothing_is_refused() -> None:
    bars = _line(3, 0, 750)
    c = Cell(RULES[0], VUSA, bars[0].day, bars[-1].day)
    #: decided on bars 100 and 110: in at the open of 101, out at the open of 111, ten days held
    one = Record(cell.key(c, bars), len(bars), (Trade(bars[100].day, bars[110].day),))
    ride = (bars[-1].close / bars[0].close).ln() / (len(bars) - 1)
    assert rung_placebo.judge(one, bars).made == (bars[111].open / bars[101].open).ln() - 10 * ride
    #: a penny line quoted to two places: five fortnights that each end ten times higher, then
    #: one that opens at a 200,000th and stays; anywhere but last it falls under half a penny
    closes = [0.05] + [0.05 * 10 ** (n // 10) for n in range(1, 51)] + [0.03] * 10
    penny = tuple(replace(b, open=b.close, high=b.close, low=b.close) for b in _bars(closes))
    c = Cell(RULES[0], VUSA, penny[0].day, penny[-1].day)
    with pytest.raises(ValueError, match="rounds to nothing"):
        rung_placebo.judge(
            Record(cell.key(c, penny), len(penny), (Trade(penny[1].day, None),)), penny
        )


def test_known_answer_a_flat_line_and_a_planted_edge_worked_by_hand() -> None:
    #: a line that never moves: every placebo is the line itself, so the first draw does as well
    #: as the rule (0 = 0): the share is (1 + 1) / 20, over SHARE, after one placebo, and a fail
    flat = _bars([100.0] * 150)
    c = Cell(RULES[0], VUSA, flat[0].day, flat[-1].day)
    still = rung_placebo.judge(Record(cell.key(c, flat), 150, (Trade(flat[20].day, None),)), flat)
    assert (still.blocks, still.run, still.made, still.share) == (
        14,
        1,
        Decimal(0),
        Decimal(2) / 20,
    )
    assert not still.passed
    #: the planted edge beats all 19 placebos, itself the only one as good: 1 / 20 = SHARE: a pass
    edge = _placebo(1, EDGE)
    assert (edge.run, edge.share, edge.passed) == (PLACEBOS, Decimal(1) / 20, True)
