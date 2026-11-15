"""The lab's rule book: the five, the eponymous rules found by the folder, a planted rule's cell."""

from __future__ import annotations

import importlib
import sys
from datetime import date
from pathlib import Path

import pytest

import desk
from desk.lines import LINES
from desk.strategy import STRATEGIES
from lab import rulebook
from lab.cell import Cell

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
    assert set(book) == {*STRATEGIES, "planted_rule"}
    assert rulebook.rule("planted_rule", tmp_path) is STRATEGIES["breakout_20_10"]
    with pytest.raises(ValueError, match="no strategy is called 'best_ever'"):
        rulebook.rule("best_ever", tmp_path)
    monkeypatch.setattr(rulebook, "DESK", tmp_path)
    line, day = LINES[0], date(2026, 1, 5)
    assert Cell("planted_rule", line, day, day).strategy == "planted_rule"
    with pytest.raises(ValueError, match="no strategy"):
        Cell("best_ever", line, day, day)
