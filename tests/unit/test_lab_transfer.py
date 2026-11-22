"""The transfer study: settings fitted on one line at a plateau's centre, scored on the others."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from test_lab_plateau import FAIL, FIVE, PASS, PEAK, _a_rule_at_every_setting, _verdict
from test_lab_sweep import BAE, _keep

from desk import strategy
from desk.lines import STAMP_DUTY, Line
from lab import history_bars, transfer
from lab.rung import Answer, Verdict

pytestmark = pytest.mark.usefixtures(_a_rule_at_every_setting.__name__)
A, B, C = "VUSA", "ISF", "SPY"
#: A shows a plateau at 30 to 50, with a peak alone at 10; B only a lone peak at 30.
EDGE = {(A, 10): PEAK, (A, 30): PASS, (A, 40): PASS, (A, 50): PASS, (B, 30): PEAK}


def _score(name: str, line: Line) -> Verdict | None:
    return _verdict(
        EDGE.get((line.symbol, int(name) if name.isdigit() else 0), FAIL), name, line.symbol
    )


def test_a_setting_is_fitted_at_a_plateaus_centre_and_scored_on_the_others_never_a_lone_peak() -> (
    None
):
    lines = [Line(s, "LSE", "GBP", 1) for s in (A, B, C)]
    family = transfer.Family("r", (FIVE,), lambda s: str(s[0]))
    done = transfer.study([family], lines, _score)
    assert (done.fits, done.bare) == (
        1,
        2,
    ), "only A shows a plateau; B's peak and C's nothing fit none"
    assert {(r.fitted, r.setting, r.line) for r in done.rows} == {
        (f"{A} on LSE", (40,), f"{B} on LSE"),
        (f"{A} on LSE", (40,), f"{C} on LSE"),
    }, "A's centre went to the others, not its peak (10) and not to A itself"
    assert all(r.t == _verdict(FAIL).t for r in done.rows) and {r.answer for r in done.rows} == {
        "FAIL"
    }
    peak = _score("30", lines[1])
    assert (
        peak and peak.passed and (30,) not in {r.setting for r in done.rows}
    ), "B's peak passes alone"


def test_a_rule_with_only_its_published_setting_is_scored_as_published_on_every_line() -> None:
    lines = [Line(s, "LSE", "GBP", 1) for s in (A, B)]
    done = transfer.study(transfer.families(), lines, _score)
    assert len(done.rows) == len(strategy.STRATEGIES) * 2 and {r.fitted for r in done.rows} == {
        None
    }
    assert transfer.counts(done, 2).startswith("grid transfer study PRE-REVIEW: 2 lines, 10 scores")


def test_the_command_writes_the_labelled_page_and_data_and_a_second_run_gives_the_same(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    homes: list[Path] = []

    def pounds(home: Path) -> dict[date, Decimal]:
        homes.append(home)
        return {}

    monkeypatch.setattr(history_bars, "pounds", pounds)
    other = Line("VOD", "LSE", "GBP", 1, STAMP_DUTY)
    for line, lift in ((BAE, 0), (other, 5)):
        _keep(tmp_path / "store", line, lift)
    argv = [str(tmp_path / "store"), str(tmp_path / "kept"), str(tmp_path)]
    transfer.main(argv)
    assert homes == [tmp_path.resolve()]  # the pound from the one door, the data folder
    first = (tmp_path / transfer.FOLDER / "grid-transfer.json").read_text(encoding="utf-8")
    transfer.main(argv)
    sets = tmp_path / transfer.FOLDER
    assert (sets / "grid-transfer.json").read_text(encoding="utf-8") == first
    assert transfer.LABEL in (sets / "grid-transfer.md").read_text(encoding="utf-8")
    assert len(json.loads(first)["rows"]) == len(strategy.STRATEGIES) * 2
    assert (
        capsys.readouterr()
        .out.splitlines()[-1]
        .startswith("grid transfer study PRE-REVIEW: 2 lines")
    )


def test_a_line_the_sizing_refuses_is_a_row_answered_refused_naming_why() -> None:
    why = "one share of AZO costs 2900 pounds, more than the room of 2000"
    lines = [Line(s, "LSE", "GBP", 1) for s in (A, B)]

    def score(name: str, line: Line) -> Verdict | None:
        found = _score(name, line)
        return (
            found and replace(found, answer=Answer.FAULT, refusal=why)
            if line.symbol == B
            else found
        )

    done = transfer.study(transfer.families(), lines, score)
    refused = [r for r in done.rows if r.answer == "REFUSED"]
    assert {r.line for r in refused} == {f"{B} on LSE"} and all(r.refusal == why for r in refused)
    assert {r.answer for r in done.rows if r.line == f"{A} on LSE"} == {"FAIL"}
    page, data = transfer.report(done, 2)
    assert f"REFUSED: {why}" in page and "REFUSED 5" in transfer.counts(done, 2)
    assert {r["refusal"] for r in data["rows"]} == {None, why}
