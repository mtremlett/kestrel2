"""The ladder's set EPON: each eponymous rule reproduced and judged on every line the store holds,
and a results table written with every column, labelled PRE-REVIEW."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType

import pytest
from test_lab_ladder import EDGE, ISF, NOISE, VUSA, _door
from test_lab_reproduce import AT_CLOSE, _figure
from test_lab_reproduce import _bars as _author

from desk import strategy
from desk.lines import LINES
from lab import grid, ladder, published, reproduce
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
    said = ladder.epon(tmp_path, _door(book), {}, [VUSA, ISF, SGLN], clock, RULES)
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


def test_a_rule_file_the_ladder_does_not_name_or_that_names_no_rules_is_refused(
    tmp_path: Path,
) -> None:
    one, bare = ModuleType("desk.eponymous_x"), ModuleType("desk.eponymous_x")
    one.EPONYMOUS = {"x": 1}  # type: ignore[attr-defined]
    (tmp_path / "eponymous_x.py").touch()
    assert ladder.eponymous([one], tmp_path) == ("x",)
    (tmp_path / "eponymous_y.py").touch()
    with pytest.raises(ValueError, match="not the modules the ladder names"):
        ladder.eponymous([one], tmp_path)
    (tmp_path / "eponymous_y.py").unlink()
    with pytest.raises(ValueError, match="no EPONYMOUS mapping"):
        ladder.eponymous([bare], tmp_path)
    assert {m.__name__ for m in ladder.MODULES} >= {"desk.eponymous_bands"}
