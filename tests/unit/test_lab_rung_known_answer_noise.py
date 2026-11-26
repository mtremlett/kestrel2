"""The rest of the answer key (PLUMB LINE v2, step 2): noise through the whole ladder goes forward
at most 2% of the time; planted edges at a true t of 1, 2, 3 and 4 pass the first rung at their
stated rates, rising with t; a line delisted part way is judged with the rest, never dropped.
Every rung is the real one: no rung's own result is stubbed. The planted rules and the walks are
the kit's (`test_lab_rung_known_answer.py`)."""

from __future__ import annotations

import json
import math
import random
from collections.abc import Iterator, Mapping, Sequence
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from statistics import NormalDist, fmean
from typing import Any

import pytest
from test_lab_ladder import SPY, _door
from test_lab_rung import _walk
from test_lab_rung_known_answer import DAYS, SIXTEEN, US, plant

from desk.command import CAPITAL
from desk.lines import Line
from desk.orders import Settings
from desk.store import Bar
from lab import cell, ladder, rung
from lab.cell import Cell
from lab.verdict_parts import goes

#: Sets of the breakout on sixteen walks of noise, each set its own register of 16 trials. The
#: plan asks 1,000 cells; there is no nightly tier, so the unit shard holds 160 (about three
#: minutes). At a true false pass of 2%, 160 cells show over 3 a third of the time; at 5%, nine
#: times in ten: this catches a ladder that lets noise through, not the 2% edge itself. The
#: 1,000 were run once, outside the tree, on 26 Nov (`docs/DECISIONS.md`).
SETS = 10
FALSE_PASS = 0.02
#: The planted edge's line (the kit's `_paid`): 2,399 churner trades under 5.5% of noise a
#: trade, whose mean after costs at no tilt is B and whose spread is SD, measured on 16 seeds
#: of no tilt (26 Nov); the tilt for a true t is the one whose mean after costs is t standard
#: errors above nothing. The test checks the measure: each group's mean t lies near its own.
TRADES, B, SD = 2399, -0.00158, 0.0541
SEEDS = 20  #: lines a true t
#: The first rung passes at t 2 or over on its 30 trades: a true t of T passes as often as a
#: standard normal lies above 2 - T, stated before any run, to within NEAR.
STATED = {t: 1 - NormalDist().cdf(float(rung.T_PASS) - t) for t in (1, 2, 3, 4)}
NEAR = 0.25
CUT = date(2023, 6, 30)  #: the delisted line's last bar


@pytest.fixture(scope="module")
def _planted() -> Iterator[None]:
    with pytest.MonkeyPatch.context() as patch:
        plant(patch)
        yield


def _set(home: Path, walks: Mapping[Line, Sequence[Bar]]) -> list[dict[str, Any]]:
    """The breakout through the real ladder on the walks, beside SPY: each line's row."""
    spy = _walk(99, 0, 0, days=DAYS // 2)
    pounds = {bar.day: Decimal("0.8") for bar in spy}
    todo = [Cell("breakout_20_10", line, ladder.START, ladder.END) for line in walks]
    ladder.run(home, _door(dict(walks) | {SPY: spy}), pounds, todo)
    lines = (home / "ladder" / "set1.jsonl").read_text().splitlines()
    return [json.loads(line) for line in lines]


def _noise(n: int) -> dict[Line, Sequence[Bar]]:
    return {
        line: _walk(1000 + 16 * n + k, 0, 0, days=DAYS // 2)[-2400:]
        for k, line in enumerate(SIXTEEN)
    }


def test_noise_through_the_whole_ladder_goes_forward_at_most_two_in_a_hundred(
    tmp_path: Path,
) -> None:
    rows = [row for n in range(SETS) for row in _set(tmp_path / str(n), _noise(n))]
    assert len(rows) == 16 * SETS and not [r for r in rows if "rungs" not in r], "every cell judged"
    went = sum(map(goes, rows))
    assert went <= FALSE_PASS * len(rows), f"{went} of {len(rows)} noise cells went forward"


def _edge(seed: int, t: int) -> tuple[Bar, ...]:
    """The kit's paid line with its tilt set for a true t: the churner is paid the tilt on
    every trade, under 5.5% of noise a bar, pulled back towards 100."""
    tilt = t * SD / math.sqrt(TRADES) - B
    rng, opens = random.Random(seed), [100.0]  # noqa: S311 - a repeatable test walk
    while len(opens) < 4801:
        sign = 1 if len(opens) % 2 == 0 else -1
        pull = 0.05 * math.log(opens[-1] / 100)
        opens.append(opens[-1] * (1 + sign * tilt + rng.gauss(0, 0.055) - pull))
    out = []
    for k in range(4800):
        o, c = Decimal(f"{opens[k]:.2f}"), Decimal(f"{opens[k + 1]:.2f}")
        high, low = max(o, c) * Decimal("1.005"), min(o, c) * Decimal("0.995")
        out.append(Bar(date(2013, 12, 1) + timedelta(k), o, high, low, c, 1))
    return tuple(out)


@pytest.mark.usefixtures("_planted")
def test_planted_edges_pass_the_first_rung_at_their_stated_rates_rising_with_t() -> None:
    passed, means = {}, {}
    for t in STATED:
        judged = []
        for seed in range(100 * t, 100 * t + SEEDS):
            bars = _edge(seed, t)
            c = Cell("churner", US[0], bars[0].day, bars[-1].day)
            pounds = {bar.day: Decimal("0.8") for bar in bars}
            judged.append(rung.judge(cell.run(c, bars), bars, Settings(CAPITAL), pounds))
        passed[t] = sum(v.passed for v in judged) / SEEDS
        means[t] = fmean(float(v.t or 0) for v in judged)
    assert all(abs(means[t] - t) < 0.5 for t in STATED), f"not the t planted: {means}"
    assert all(abs(passed[t] - STATED[t]) <= NEAR for t in STATED), (passed, STATED)
    assert [passed[t] for t in sorted(passed)] == sorted(passed.values()), passed


def test_a_line_delisted_part_way_is_judged_with_the_rest_never_dropped(tmp_path: Path) -> None:
    #: survivorship: AMD stops at CUT; its row is judged on what it had, with an answer, and
    #: the rule's last fold (2025) is pooled over the fifteen lines still trading then
    walks = _noise(SETS) | {US[-1]: [bar for bar in _noise(SETS)[US[-1]] if bar.day <= CUT]}
    rows = {row["cell"][1]: row for row in _set(tmp_path, walks)}
    assert set(rows) == {line.symbol for line in SIXTEEN}
    gone = rows[US[-1].symbol]
    assert "error" not in gone and gone["answer"] == "FAIL" and not goes(gone), gone
    assert "2025: 82 trades pooled over 15 lines" in gone["rungs"]["folds"][1]
