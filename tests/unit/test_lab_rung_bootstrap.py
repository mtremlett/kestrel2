"""The ladder's block bootstrap rung (R-RUNNER-121), proven alone: a planted edge passes, five
hundred cells of noise pass at about the stated rate and no more, the power at three sizes of
edge is recorded, a broken copy is caught, and the rung reads the cell's tape, keyed by it."""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from decimal import Decimal
from pathlib import Path

import numpy as np
import pytest
from numpy.lib.stride_tricks import sliding_window_view
from test_lab_rung import AAPL, VUSA, _walk

from desk.store import Bar
from lab import cell, rung_bootstrap, tape
from lab.cell import Cell, Record
from lab.rung import Answer
from lab.rung_bootstrap import RATE, share

DAYS, CELLS = 1500, 500  #: six years of days to a cell, and the cells of noise
Rung = Callable[[Sequence[float], int], bool]  #: a cell's days and its seed: passed, or not
#: THE POWER CURVE, recorded: the part passed of 3,000 cells whose mean was planted 1, 2.5 and
#: 4 of its own standard errors above nothing (0.174, 0.719, 0.978); of 3,000 of plain noise
#: 0.024 passed, of noise in runs of five days 0.032, and by single days 0.22 of those
POWER = {1.0: 0.17, 2.5: 0.72, 4.0: 0.98}


def _real(days: Sequence[float], seed: int) -> bool:
    return share(days, seed) <= RATE


def _inverted(days: Sequence[float], seed: int) -> bool:
    return not _real(days, seed)


def _single(days: Sequence[float], seed: int) -> bool:
    """Blocks of one day: the Monte Carlo rung's single draws, which this rung must not be."""
    return share(days, seed, block=1) <= RATE


def _cells(seed: int, edge: float = 0, run: int = 1, count: int = CELLS) -> list[list[float]]:
    """`count` cells of DAYS days of noise, each day the sum of `run` shocks in a row, so the
    days come in runs; the mean is planted `edge` of its own standard errors above nothing."""
    shocks = np.random.default_rng(seed).standard_normal((count, DAYS + run - 1))
    days = sliding_window_view(shocks, run, axis=1).sum(axis=2) + edge * run / math.sqrt(DAYS)
    made: list[list[float]] = days.tolist()
    return made


def _passed(rung: Rung, cells: list[list[float]]) -> int:
    return sum(rung(days, seed) for seed, days in enumerate(cells))


def _about(count: int, rate: float) -> tuple[int, int]:
    """The binomial interval: the fewest and the most of `count` that pass at `rate`, 95 times
    in 100."""
    part = [math.comb(count, k) * rate**k * (1 - rate) ** (count - k) for k in range(count + 1)]
    low = next(k for k in range(count + 1) if sum(part[: k + 1]) > 0.025)
    return low, next(k for k in range(count, -1, -1) if sum(part[k:]) > 0.025)


def _proof(rung: Rung) -> None:
    """The rung's proof alone, which no broken copy of it gets through."""
    assert _passed(rung, _cells(1, edge=6, count=20)) == 20, "a planted edge passes"
    runs, twice = _passed(rung, _cells(3, run=5, count=200)), _about(200, 2 * RATE)[1]
    assert runs <= twice, "noise in runs passes at under twice the stated rate"
    low, high = _about(CELLS, RATE)
    assert low <= _passed(rung, _cells(2)) <= high, "noise passes at about the stated rate"


def test_a_planted_edge_passes_and_five_hundred_noise_cells_pass_at_about_the_stated_rate() -> None:
    assert _about(CELLS, RATE) == (6, 20), "of 500 cells at 1 in 40"
    _proof(_real)


@pytest.mark.parametrize(("broken", "caught"), [(_inverted, "planted edge"), (_single, "in runs")])
def test_a_broken_copy_of_the_rung_is_caught(
    broken: Rung, caught: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(rung_bootstrap, "DRAWS", 500)  #: enough to catch it, and short
    with pytest.raises(AssertionError, match=caught):
        _proof(broken)


def test_a_block_that_runs_off_the_end_goes_on_from_the_start() -> None:
    #: blocks of two of these days make 2, -2, -2 and, round the end, 2: so a history of two
    #: blocks makes nothing or loses three times in four (were the end to stop it, 15 in 16)
    assert share([3, -1, -1, -1], seed=1, block=2) == pytest.approx(0.75, abs=0.03)


def test_the_power_at_three_sizes_of_edge_is_the_curve_recorded() -> None:
    for edge, part in POWER.items():
        low, high = _about(200, part)
        assert low <= _passed(_real, _cells(4, edge, count=200)) <= high, f"an edge of {edge}"


def test_the_rung_reads_the_cells_tape_and_is_keyed_by_the_tape_this_code_and_the_rates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    edge, noise = _walk(1, 0.012, 0.012, days=3100), _walk(2, 0, 0, days=3100)
    c = Cell("breakout_20_10", VUSA, edge[0].day, edge[-1].day)
    made = tape.kept(tmp_path, cell.run)(c, edge)

    def never(c: Cell, _bars: Sequence[Bar]) -> Record:
        raise AssertionError(f"{c}: simulated again")

    won = rung_bootstrap.judge(tape.kept(tmp_path, never)(c, edge), edge, {})
    assert won.answer is Answer.PASS and won.share is not None and won.share <= RATE
    none = cell.run(Cell(c.strategy, VUSA, noise[0].day, noise[-1].day), noise)
    lost = rung_bootstrap.judge(none, noise, {})
    assert lost.answer is Answer.FAIL and lost.share is not None and RATE < lost.share < 1
    assert lost == rung_bootstrap.judge(none, noise, {}), "a cell judged again is drawn the same"
    young = cell.run(Cell(c.strategy, VUSA, c.start, edge[400].day), edge)
    assert rung_bootstrap.judge(young, edge, {}) == rung_bootstrap.Redrawn(0, None, Answer.THIN)
    key, rate = rung_bootstrap.key, {edge[5].day: Decimal("0.8")}
    dollars = Record(cell.key(Cell(c.strategy, AAPL, c.start, c.end), edge), 0, ())
    keys = [key(made, {}), key(young, {}), key(dollars, {}), key(dollars, rate)]
    assert key(made, rate) == keys[0] and len(set(keys)) == 4, "a pound line reads no rate"
    monkeypatch.setitem(cell.RUNGS, rung_bootstrap.ME, "this module edited")
    keys += [key(made, {})]
    monkeypatch.setattr(tape, "rule_code", lambda _: "the rule edited")
    assert len({*keys, key(made, {})}) == 6, "this module's code and the tape's parts are in it"
    monkeypatch.setattr(rung_bootstrap, "BLOCK", 400)
    thin = rung_bootstrap.judge(made, edge, {})
    assert (thin.days, thin.share, thin.answer) == (won.days, None, Answer.THIN), "too few blocks"
