"""The lab's rule book: the five, the eponymous rules found by the folder, a planted rule's cell."""

from __future__ import annotations

import importlib
import sys
from datetime import date
from pathlib import Path

import pytest

import desk
from desk.lines import LINES
from desk.strategy import STRATEGIES, VARIANTS
from lab import rulebook
from lab.cell import Cell
from lab.rulebook import CATALOGUE

PLANTED = """
from desk.strategy import STRATEGIES

EPONYMOUS = {"planted_rule": STRATEGIES["breakout_20_10"]}
"""


def test_the_book_has_the_five_and_a_planted_files_rules_and_refuses_the_unknown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "eponymous_planted.py").write_text(PLANTED)
    monkeypatch.setattr(desk, "__path__", [*desk.__path__, str(tmp_path)])
    monkeypatch.setattr(sys, "modules", dict(sys.modules))  #: the planted file leaves no trace
    importlib.invalidate_caches()
    book = rulebook.rules(tmp_path)
    assert set(book) == {*STRATEGIES, *VARIANTS, "planted_rule"}
    clash = next(iter(VARIANTS))
    (tmp_path / "eponymous_clash.py").write_text(PLANTED.replace("planted_rule", clash))
    with pytest.raises(ValueError, match="named twice"):
        rulebook.eponymous(tmp_path)
    (tmp_path / "eponymous_clash.py").unlink()
    assert rulebook.rule("planted_rule", tmp_path) is STRATEGIES["breakout_20_10"]
    with pytest.raises(ValueError, match="no strategy is called 'best_ever'"):
        rulebook.rule("best_ever", tmp_path)
    monkeypatch.setattr(rulebook, "DESK", tmp_path)
    line, day = LINES[0], date(2026, 1, 5)
    assert Cell("planted_rule", line, day, day).strategy == "planted_rule"
    with pytest.raises(ValueError, match="no strategy"):
        Cell("best_ever", line, day, day)


def test_the_catalogue_names_only_python_rules_each_proven(tmp_path: Path) -> None:
    named = rulebook.specs()
    assert named and set(named) <= set(rulebook.eponymous())
    assert all(spec.name == name and spec.cases for name, spec in named.items())
    text, book = CATALOGUE.read_text("utf-8"), tmp_path / "book.toml"
    book.write_text(text + "\n[no_such_rule]\nx = 1\n", "utf-8")
    with pytest.raises(ValueError, match="no_such_rule"):
        rulebook.specs(book)
    book.write_text(text.replace("wants = [0,", "wants = [1,", 1), "utf-8")
    with pytest.raises(ValueError, match="case 0 gives"):
        rulebook.specs(book)
