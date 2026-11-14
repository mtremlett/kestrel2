"""The transfer study: settings fitted on one line are scored on the others, a lone peak is
never chosen, and the command keeps its work and ends with one line of counts."""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from test_lab_plateau import FAIL, PASS, PEAK, SEVEN, _square, _verdict
from test_lab_sweep import BAE, _keep

from desk.lines import Line
from lab import cell, transfer
from lab.plateau import Setting
from lab.rung import Answer, Verdict
from lab.transfer import Space

VUSA, VUAG, ISF, LONE = (Line(s, "LSE", "GBP", 1) for s in ("VUSA", "VUAG", "ISF", "EQQQ"))
SPACE = {"r": Space((SEVEN, SEVEN), str)}


class _AnyRule:
    def __contains__(self, name: str) -> bool:
        return True


@pytest.fixture(autouse=True)
def _a_rule_at_every_setting(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cell, "STRATEGIES", _AnyRule())


def _judge(edges: dict[Line, Callable[[Setting], str]]) -> transfer.Judge:
    """Each line's surface of the rule `r` over the grid: its own edge at each setting."""
    sets = {str(s): s for s in SPACE["r"].settings()}

    def judge(line: Line, names: Sequence[str]) -> dict[str, Verdict | str]:
        return {n: _verdict(edges[line](sets[n]), n, line.symbol) for n in names}

    return judge


def test_a_setting_fitted_on_one_line_is_scored_on_the_others_and_a_lone_peak_is_not_chosen() -> (
    None
):
    edges = {
        VUSA: _square,  # a plateau, and a lone peak that scores best
        VUAG: lambda _: PASS,  # earns anywhere
        ISF: lambda _: FAIL,  # earns nowhere
        LONE: lambda s: PEAK if s == (60, 60) else FAIL,  # a peak alone
    }
    done = transfer.study((VUSA, VUAG, ISF, LONE), SPACE, _judge(edges))
    fits = {fit.line: fit for fit in done.fits}
    assert fits[VUSA].setting == (30, 30) and fits[VUSA].promoted
    peak, centre = (done.scores["r", s, VUSA][1] or 0 for s in ((60, 60), (30, 30)))
    assert peak > centre
    assert fits[LONE].setting == (60, 60) and not fits[LONE].promoted
    assert transfer.transfers(done, fits[LONE]) == {}, "a peak is shown and never transferred"
    got = transfer.transfers(done, fits[VUSA])
    assert {line: a for line, (a, _t) in got.items()} == {
        VUAG: Answer.PASS,
        ISF: Answer.FAIL,
        LONE: Answer.FAIL,
    }, "scored where it was not fitted, and nowhere it was"
    counts = transfer.report(done)["counts"]
    assert counts["fitted"] == 4 and counts["promoted"] == 2  # VUAG's flat plateau too
    assert transfer.LABEL in transfer.markdown(transfer.report(done))


def test_the_command_judges_every_rule_on_every_line_keeps_its_work_and_ends_in_counts(
    tmp_path: Path, capsys: object
) -> None:
    _keep(tmp_path / "store", BAE)
    env, say = {"KESTREL2_DATA": str(tmp_path)}, dict[date, Decimal]
    assert transfer.main([str(tmp_path / "store")], env, say) == 0
    first = capsys.readouterr().out  # type: ignore[attr-defined]
    out = tmp_path / transfer.FOLDER
    done = json.loads((out / "grid-transfer.json").read_text(encoding="utf-8"))
    assert done["label"] == "PRE-REVIEW" and done["counts"]["lines"] == 1
    assert done["counts"]["judged"] + done["counts"]["failed"] == done["counts"]["rules"] * 1
    assert first.count("\n") == 1 and "PRE-REVIEW" in first
    kept = (out / "grid-transfer" / "LSE" / "BA.jsonl").read_bytes()
    assert transfer.main([str(tmp_path / "store")], env, say) == 0
    assert capsys.readouterr().out == first  # type: ignore[attr-defined]
    assert (out / "grid-transfer" / "LSE" / "BA.jsonl").read_bytes() == kept, "not run twice"
