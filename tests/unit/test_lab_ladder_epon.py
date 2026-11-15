"""The ladder's set EPON: each eponymous rule reproduced and judged on every line the store holds,
and a results table written with every column, labelled PRE-REVIEW."""

from __future__ import annotations

import importlib
import json
import sys
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest
from test_lab_ladder import EDGE, ISF, NOISE, VUSA, _door
from test_lab_reproduce import AT_CLOSE, _figure
from test_lab_reproduce import _bars as _author

import desk
from desk import strategy
from desk.lines import LINES
from lab import grid, ladder, ladder_sets, published, reproduce
from lab.cell import Cell
from lab.published_epon import EPONYMOUS_PUBLISHED
from lab.reproduce import Fill

SGLN = next(line for line in LINES if line.symbol == "SGLN")  #: the planted author's market
RULES = ("planted_breakout", "planted_trend")  #: two rules planted, each an old one by a new name


def test_the_set_reproduces_each_rule_judges_it_on_every_line_and_writes_the_table(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for new, old in zip(RULES, ("breakout_20_10", "trend_50_200"), strict=True):
        monkeypatch.setitem(strategy.STRATEGIES, new, strategy.STRATEGIES[old])
        monkeypatch.setitem(grid.RULES, new, grid.RULES[old])
        monkeypatch.setitem(published.PUBLISHED, new, published.PUBLISHED[old])
    figure = replace(_figure(Fill.CLOSE, *AT_CLOSE), strategy=RULES[0], line=SGLN)
    monkeypatch.setattr(reproduce, "FIGURES", (figure,))  #: the first rule has one, the second none
    book = {VUSA: EDGE, ISF: NOISE, SGLN: _author()}
    clock = lambda: datetime(2026, 11, 14, tzinfo=UTC)  # noqa: E731
    said = ladder_sets.epon(tmp_path, _door(book), {}, [VUSA, ISF, SGLN], clock, RULES)
    table = tmp_path / "ladder" / "sets" / "EPON.md"
    assert said.splitlines()[-1] == f"SET EPON: 2 rules, 0 passed, table {table}"
    data = json.loads(table.with_suffix(".json").read_text())
    assert (data["status"], data["trials"], [r["rule"] for r in data["rules"]]) == (
        "PRE-REVIEW",
        18,  #: six cells, each with its two folds
        list(RULES),
    )
    made, plain = data["rules"]
    for rule in data["rules"]:  #: every line, the one that cannot yet be judged with its reason
        assert [c["cell"][1] for c in rule["cells"]] == ["VUSA", "ISF", "SGLN"]
        assert {c["trials"] for c in rule["cells"]} == {18} and "TooYoung" in rule["cells"][2][
            "error"
        ]
    vusa, plain_vusa = made["cells"][0], plain["cells"][0]
    assert "reproduced: the author's result, a planted author" in vusa["reproduction"][0]
    assert "against the author's 2" in vusa["reproduction"][0] and "reproduce" not in vusa["unrun"]
    assert (
        "reproduction" not in plain_vusa
        and "no author's figure" in plain_vusa["unrun"]["reproduce"]
    )
    assert plain_vusa["answer"] == "THIN" and set(plain_vusa["rungs"]) >= {
        "first",
        "luck",
        "market",
    }
    md = table.read_text()
    head = "| rule | line | venue | answer | rungs | trials | reproduction | goes forward |"
    assert md.startswith("# SET EPON - PRE-REVIEW") and md.count(head) == 2
    assert "first PASS:" in md and "regime UNRUN:" in md and "no author's figure" in md
    assert "goes forward" in md and ": 0 of 3 lines go forward" in md


def test_the_desks_folder_is_the_one_list_a_new_file_is_taken_and_keyed_a_bare_one_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A new eponymous file in the folder is imported and changes the keys, with no edit to the
    ladder; one that names its rules in no EPONYMOUS is refused, by name."""
    monkeypatch.setattr(desk, "__path__", [*desk.__path__, str(tmp_path)])
    monkeypatch.setattr(sys, "modules", dict(sys.modules))  #: the planted files leave no trace
    importlib.invalidate_caches()
    before = ladder.code(tmp_path)
    planted = tmp_path / "eponymous_planted.py"
    planted.write_text("class X: ...\nEPONYMOUS = {'planted_x': X}")
    assert ladder.eponymous(tmp_path) == ("planted_x",) and ladder.code(tmp_path) != before
    planted.write_text("class X: ...\nEPONYMOUS = {'planted_x': X}  # 2")
    assert ladder.code(tmp_path) not in (before, ladder.code(Path(desk.__file__).parent))
    (tmp_path / "eponymous_bare.py").write_text("X = 1")
    with pytest.raises(ValueError, match="desk.eponymous_bare names its rules in no EPONYMOUS"):
        ladder.eponymous(tmp_path)


def test_every_eponymous_file_of_the_real_desk_gives_a_rule_a_cell_and_a_first_rung_answer(
    tmp_path: Path,
) -> None:
    """On the real desk folder: each rule is found, makes a Cell and is judged on a tiny fixture."""
    files = sorted(Path(desk.__file__).parent.glob("eponymous_*.py"))
    found = ladder.eponymous()
    assert len(files) >= 16 and len(found) >= len(files) - 1
    assert "zweig_breadth_thrust" not in found  #: it takes a breadth no store holds: left out
    todo = [Cell(rule, VUSA, ladder.START, ladder.END) for rule in found]
    clock = lambda: datetime(2026, 11, 14, tzinfo=UTC)  # noqa: E731
    ladder.run(tmp_path, _door({VUSA: EDGE, ISF: NOISE}), {}, todo, clock, ladder_sets.EPON)
    rows = [json.loads(x) for x in (tmp_path / "ladder" / "EPON.jsonl").read_text().splitlines()]
    assert [r["cell"][0] for r in rows] == list(found)
    #: a rule on file (lab/published_epon.py) is judged; the rest wait for the next step
    off = {r["cell"][0] for r in rows if "error" in r}
    assert off == set(found) - set(EPONYMOUS_PUBLISHED)
    assert all("no published rule on file" in r["error"] for r in rows if "error" in r)
