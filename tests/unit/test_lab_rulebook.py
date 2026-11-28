"""The lab's rule book: the five, the eponymous rules found by the folder, a planted rule's cell."""

from __future__ import annotations

import importlib
import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

import desk
from desk.lines import LINES
from desk.store import Bar
from desk.strategy import STRATEGIES, VARIANTS, _run
from lab import rulebook, spec, variants
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
    assert set(book) == {*STRATEGIES, *VARIANTS, "planted_rule", *rulebook.specs()}
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


def test_the_catalogue_names_rules_each_proven_and_a_row_without_python_is_served(
    tmp_path: Path,
) -> None:
    named = rulebook.specs()
    assert named and set(named) <= set(rulebook.rules())
    assert all(spec.name == name and spec.cases for name, spec in named.items())
    text, book = CATALOGUE.read_text("utf-8"), tmp_path / "book.toml"
    book.write_text(text + "\n[no_such_rule]\nx = 1\n", "utf-8")
    with pytest.raises(ValueError, match="extra"):
        rulebook.specs(book)
    book.write_text(text.replace("wants = [0,", "wants = [1,", 1), "utf-8")
    with pytest.raises(ValueError, match="case 0 gives"):
        rulebook.specs(book)


def test_a_variant_is_a_rule_by_name_and_stays_out_of_the_book() -> None:
    made = next(v for v in variants.family(rulebook.specs()))
    assert made.spec.name not in rulebook.rules()
    assert rulebook.rule(made.spec.name).__name__ == "SpecRule"
    with pytest.raises(ValueError, match="no variant is called"):
        rulebook.rule("breakout_20_10[nope=1]")


def test_a_catalogue_row_with_no_python_file_is_served_and_equals_its_python_twin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    text = CATALOGUE.read_text("utf-8")
    one = text[
        text.index("[donchian_channel_breakout]") : text.index("[connors_three_day_high_low]")
    ]
    book = tmp_path / "book.toml"
    book.write_text(one.replace("donchian_channel_breakout", "planted_row"), "utf-8")
    monkeypatch.setattr(rulebook, "CATALOGUE", book)
    assert "planted_row" not in rulebook.eponymous()
    served = rulebook.rule("planted_row")
    assert served.__name__ == "SpecRule" and "planted_row" in rulebook.rules()
    bars = tuple(
        Bar(date(2020, 1, 1) + timedelta(n), c, c + 2, c - 2, c, 1000)
        for n, c in enumerate(Decimal(100 + (n % 60) * 3) for n in range(300))
    )
    twin = rulebook.eponymous()["donchian_channel_breakout"]
    mine, theirs = (tuple(_run("x", made(), "X", bars)) for made in (served, twin))
    assert mine == theirs and any(d.action.name == "BUY" for d in mine)


def test_the_spec_book_is_read_once_per_text_and_an_edited_file_is_read_again(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """S1: the book's rows are parsed and proven once per text of the file, not on every call
    (every cell asks); the cache is keyed by the file's bytes, so an edit is never served stale."""
    parsed, real = [0], spec.Spec.parse

    def counted(row: dict[str, object]) -> spec.Spec:
        parsed[0] += 1
        return real(row)

    monkeypatch.setattr(spec.Spec, "parse", counted)
    book = tmp_path / "catalogue.toml"
    text = CATALOGUE.read_text(encoding="utf-8")
    book.write_text(text, encoding="utf-8")
    first = rulebook.specs(book)
    once = parsed[0]
    assert rulebook.specs(book) == first and parsed[0] == once, "the same text parsed again"
    book.write_text(text.replace('"Faith, Way', '"R. Faith, Way', 1), encoding="utf-8")
    assert rulebook.specs(book)["donchian_channel_breakout"].source.startswith("R. Faith")
