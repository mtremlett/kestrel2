"""The ladder's sets trade a line only on the days it was a member of its list."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from desk.lines import LINES, Line
from lab import ladder, ladder_sets, members, verdict
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


def test_a_basket_row_carries_the_market_its_lines_venue_is_set_beside(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from test_lab_ladder import EDGE, ISF, VUSA, _door

    from lab import basket, rung_retail, trials
    from lab.cell import Cell

    monkeypatch.setattr(trials, "family", lambda *_: 1)
    seen: list[rung_retail.Against | None] = []
    row = basket.row

    def spy(*a: Any) -> Any:
        seen.append(a[5])
        return row(*a)

    monkeypatch.setattr(basket, "row", spy)
    todo = [Cell("breakout_20_10", VUSA, START, END)]
    door = _door({VUSA: EDGE, ISF: EDGE})
    ladder_sets.baskets(tmp_path, door, {}, todo, ["breakout_20_10"], ladder_sets.EPON)
    (against,) = seen
    assert against is not None
    assert (against.line, against.bars, against.rates) == (ISF, EDGE, {})


def test_a_set_of_three_rules_writes_three_rows_and_the_cells_file(tmp_path: Path) -> None:
    rules = ["a", "b", "c"]
    rows = [
        {
            "cell": [r, f"L{i}", "US"],
            "trials": 3,
            "rungs": {"folds": ["PASS", "ok"], "cost": ["FAIL", "dear"]},
        }
        for r in rules
        for i in range(2)
    ]
    table = verdict.write_table(tmp_path, "T", "q?", rows, rules, 3, (2, 5))
    ladder_sets.condense(table, rows, rules, ("X: not corrected",))
    text = table.read_text(encoding="utf-8")
    assert (
        sum(ln.startswith("| ") for ln in text.splitlines()) == 4
    )  #: the header and one row for each of 3 rules
    assert "| a | cost | FAIL: dear | 2 of 2 | L0 | no |" in text
    assert "- X: not corrected" in text
    assert len(json.loads(table.with_suffix(".cells.json").read_text())) == 6
