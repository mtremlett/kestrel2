"""The known-answer kit: planted noise is refused and a planted edge heard through the whole ladder
on fixture data (L15b); it goes forward only once `reproduce` is judged on a rule with no figure."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from test_lab_ladder import SPY, _door, _set
from test_lab_rung import _walk

from desk.lines import LINES
from lab import ladder, verdict

NAMES = "3LGO 2MU SMGB IITU VHYG 5QQQ ISF VUSA SGLN VUAG EQQQ IB1T AAPL TSLA NVDA AMD".split()
SIXTEEN = [next(line for line in LINES if line.symbol == name) for name in NAMES]


def _answers(home: Path, drift: float) -> list[dict[str, Any]]:
    walks = {line: _walk(n, drift, drift, days=3100)[-2400:] for n, line in enumerate(SIXTEEN, 1)}
    spy = _walk(99, 0, 0, days=3100)
    pounds = {bar.day: Decimal("0.8") for bar in spy}
    ladder.run(home, _door(walks | {SPY: spy}), pounds, _set(*SIXTEEN))
    path = home / "ladder" / "set1.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines()]


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
