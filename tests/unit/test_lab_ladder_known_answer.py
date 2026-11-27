"""The known-answer kit: planted noise is refused and a planted edge heard through the whole ladder
on fixture data (L15b), and a planted edge goes forward.

The breakout's planted rise is heard but cannot go forward, and lengthening its walks will not do
it (probed 27 Nov on the whole 6,200 days): about 60 trades a line clear the trade counts, but the
planted rise follows any trend, so fit FAILS (moves 0.91 with supertrend_10_3), liquidity FAILS
(the walk's volume is 1) and up days stay THIN; and the 16 lines then take over ten minutes.

So the edge that goes forward is one only its rule hears, on bars with a real volume, on few
lines: a crowd. A line's days come in spells, a crowded spell trading twice its usual volume and
rising, a quiet one giving the rise back, so the line goes nowhere; a rule in while the day was
crowded is paid, and no rule reading prices alone hears it (fit about 0.5). It is judged on all
17 years: an edge under the yearly Sharpe flag of 2 (about 1.2 to 1.5 here) needs them for its
two regime windows to pass apart; on 2,400 days it was too thin to (t 1.1 to 2.9). The spells
last eight days, so a bar late should still be paid (E13's rung). Its noise is the same crowds
over lines that do not move with them, refused by the first rung after costs."""

from __future__ import annotations

import json
import math
import random
from collections.abc import Mapping, Sequence
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from typing import Any, ClassVar

import pytest
from test_lab_ladder import SPY, _door, _set
from test_lab_rung import _bars, _walk

from desk.lines import LINES, Line
from desk.store import Bar
from desk.strategy import Declared, Field, Rule, Timeframe
from lab import ladder, rulebook, tape, verdict
from lab.cell import Cell
from lab.published_case import FIRST, Case, Published
from lab.published_epon import EPONYMOUS_PUBLISHED
from lab.verdict_parts import goes

NAMES = "3LGO 2MU SMGB IITU VHYG 5QQQ ISF VUSA SGLN VUAG EQQQ IB1T AAPL TSLA NVDA AMD".split()
SIXTEEN = [next(line for line in LINES if line.symbol == name) for name in NAMES]
US = SIXTEEN[-4:]  #: the crowd's lines, beside SPY
DAYS = 6200  #: 2010 to the end of 2026, the crowd judged on all of it: under the yearly flag
QUIET, CROWDED = 1_000_000, 2_000_000  #: a day's volume, in shares
STAY = {False: 0.9375, True: 0.875}  #: a spell's chance of going on a day: quiet 16 days, crowded 8
RISE = 0.004  #: a crowded day's rise; a quiet day gives back half of it, so the line goes nowhere
SWING = 0.015  #: the day's noise


class Crowd:
    """In the market while the day traded more than its usual volume, out after a quiet one."""

    declared: ClassVar[Declared] = Declared(Timeframe.DAILY, None, LINES, frozenset({Field.VOLUME}))

    def step(self, bar: Bar, holding: bool) -> bool:  # noqa: ARG002 - the Rule interface
        return bar.volume > (QUIET + CROWDED) // 2


def _crowds(seed: int, rise: float) -> tuple[Bar, ...]:
    """A line of crowded and quiet spells, each crowded day rising `rise` and each quiet day
    giving back half of it, under SWING of noise pulled gently back towards 100."""
    rng, closes, crowded = random.Random(seed), [100.0], [False]  # noqa: S311 - a test walk
    while len(closes) < DAYS:
        stays = rng.random() < STAY[crowded[-1]]
        crowded.append(crowded[-1] if stays else not crowded[-1])
        drift = rise if crowded[-1] else -rise / 2
        pull = 0.005 * math.log(closes[-1] / 100)
        closes.append(closes[-1] * (1 + drift + rng.gauss(0, SWING) - pull))
    bars = zip(_bars(closes), crowded, strict=True)
    return tuple(replace(bar, volume=CROWDED if c else QUIET) for bar, c in bars)


def _plant(patch: pytest.MonkeyPatch) -> None:
    """The crowd in the book, with its own known answer, so the ladder's door lets it in."""
    real_rules = rulebook.rules

    def rules(folder: Path | None = None) -> dict[str, type[Rule]]:
        return {**real_rules(folder), "crowd": Crowd}

    patch.setattr(rulebook, "rules", rules)
    days = [QUIET, CROWDED, CROWDED, QUIET, CROWDED, QUIET]
    rows = tuple(
        Bar(FIRST.replace(day=n + 1), Decimal(10), Decimal(11), Decimal(9), Decimal(10), v)
        for n, v in enumerate(days)
    )
    crowds = Case("in after bars 1 and 4, out after 3 and 5", (), ((1, 3), (4, 5)), rows=rows)
    patch.setitem(EPONYMOUS_PUBLISHED, "crowd", Published("the kit's crowd", (crowds,)))
    real = tape.code_of_rule  #: the test module is not under the code's root: keyed by name
    patch.setattr(tape, "code_of_rule", lambda s: "planted" if s == "crowd" else real(s))


def _run(home: Path, walks: Mapping[Line, Sequence[Bar]], todo: Sequence[Cell]) -> list[Any]:
    spy = _walk(99, 0, 0, days=3100)
    pounds = {bar.day: Decimal("0.8") for bar in spy}
    ladder.run(home, _door(dict(walks) | {SPY: spy}), pounds, todo)
    path = home / "ladder" / "set1.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines()]


def _answers(home: Path, drift: float) -> list[dict[str, Any]]:
    walks = {line: _walk(n, drift, drift, days=3100)[-2400:] for n, line in enumerate(SIXTEEN, 1)}
    return _run(home, walks, _set(*SIXTEEN))


def _crowded(home: Path, rise: float) -> list[dict[str, Any]]:
    walks = {line: _crowds(n, rise) for n, line in enumerate(US, 1)}
    return _run(home, walks, [Cell("crowd", line, ladder.START, ladder.END) for line in walks])


def test_a_planted_edge_goes_forward_and_planted_noise_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(verdict, "EASED", False)
    edge, noise = _answers(tmp_path / "edge", 0.012), _answers(tmp_path / "noise", 0)
    assert {row["answer"] for row in noise} == {"FAIL"} and not any(r["every"] for r in noise)
    assert "error" not in {k for row in edge + noise for k in row}
    #: the edge is heard, the noise is not: most edge lines are THIN alone (too few trades to be
    #: judged, the rule's lines pooled PASS the folds); plateau (L17) is judged, NOT APPLICABLE
    #: to the breakout, which carries no settings; reproduce is judged on determinism.
    said = [row["answer"] for row in edge]
    assert said.count("THIN") > len(said) // 2 and not any(r["every"] for r in edge)
    assert {row["rungs"]["folds"][0] for row in edge} == {"PASS"}
    assert edge[0]["unrun"] == {}  #: no author's figure: judged on determinism
    assert {row["rungs"]["plateau"][0] for row in edge} == {"PASS"}


def test_a_planted_edge_reads_pass_through_the_whole_ladder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """L15b's gate: the crowd goes forward on every line, every rung run and passed; the same
    crowds over lines that do not move with them are refused on every line."""
    monkeypatch.setattr(verdict, "EASED", False)
    _plant(monkeypatch)
    edge, noise = _crowded(tmp_path / "edge", RISE), _crowded(tmp_path / "noise", 0)
    held = {
        row["cell"][1]: {k: v for k, v in row["rungs"].items() if v[0] != "PASS"} for row in edge
    }
    assert all(map(goes, edge)) and len(edge) == len(US), held
    assert {row["answer"] for row in noise} == {"FAIL"} and not any(map(goes, noise))
