"""The ladder's sets trade a line only on the days it was a member of its list."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from desk.lines import LINES, Line
from lab import ladder, ladder_sets, members
from lab.ladder import END, START
from lab.members import Change, Record

STAYS, LEFT, JOINED = (Line(s, "US", "USD", 1) for s in ("STAY", "LEFT", "NEW"))
RECORD = Record(
    (STAYS, JOINED),
    (Change(date(2018, 3, 1), "NEW", True), Change(date(2015, 6, 1), "LEFT", False)),
)
LONDON = next(line for line in LINES if line.venue == "LSE")


def test_a_line_is_traded_only_while_a_member_and_a_london_line_says_it_is_not_corrected() -> None:
    cells, notes = ladder_sets.survivors(
        ["breakout_20_10"], [STAYS, LEFT, JOINED, LONDON], {"X": RECORD}
    )
    spans = {c.line.symbol: (c.start, c.end) for c in cells}
    assert spans["LEFT"] == (START, date(2015, 5, 31))  #: out on the day it left
    assert spans["NEW"] == (date(2018, 3, 1), END)
    assert spans["STAY"] == (START, END)
    assert spans[LONDON.symbol] == (START, END)
    assert notes == (f"{LONDON.symbol} (LSE): survivorship: not corrected",)


def test_the_real_lists_trade_a_leaver_only_up_to_its_leaving() -> None:
    gone = next(c for c in members.RECORDS["SP500"].changes if not c.joined)
    line = Line(gone.symbol, "US", "USD", 1)
    (cell,), _ = ladder_sets.survivors(["breakout_20_10"], [line], members.RECORDS)
    assert cell.end < gone.day


def _door(home: Path, answers: list[str], monkeypatch: pytest.MonkeyPatch) -> int:
    """The command on a set whose cells each hold one folds answer."""
    rows = [
        {"cell": ["r", f"L{i}"], "rungs": {"folds": [a, "no years"]}} for i, a in enumerate(answers)
    ]
    (home / "ladder").mkdir(parents=True)
    (home / "ladder" / "EPON.jsonl").write_text("".join(json.dumps(r) + chr(10) for r in rows))
    monkeypatch.setattr(ladder_sets, "main", lambda *_: 0)
    return ladder.door({"KESTREL2_DATA": str(home)}, [])


def test_a_set_whose_cells_all_fault_ends_red_naming_the_rung_and_real_fails_end_green(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    assert _door(tmp_path / "a", ["FAULT"] * 3, monkeypatch) == 1
    assert "FAULT: 3 of 3 cells at rung folds: no years" in capsys.readouterr().out
    assert _door(tmp_path / "b", ["FAIL"] * 3, monkeypatch) == 0
    assert "FAULT" not in capsys.readouterr().out
