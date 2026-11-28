"""The ladder's tapes (R-RUNNER-118): a rule's trades on a line are kept once, by what made them;
a rung changed runs no simulation, a rule changed runs its own again, the rows are the rows there
were, and a stop takes up from the last tape finished."""

from __future__ import annotations

import importlib
import pickle
import shutil
import sys
from collections import Counter
from collections.abc import Callable, Sequence
from contextlib import nullcontext
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from test_lab_ladder import EDGE, ISF, NOISE, VUSA, _door, _rows

import desk
from desk.orders import Settings
from desk.store import Bar
from lab import cell, ladder, ladder_epon, ladder_sets, rulebook, rung, tape, verdict
from lab.cell import Cell, Record

CLOCK = lambda: datetime(2026, 11, 14, tzinfo=UTC)  # noqa: E731
BOOK = {VUSA: EDGE, ISF: NOISE}
RULES = ("breakout_20_10", "trend_50_200")
TODO = [Cell(rule, line, ladder.START, ladder.END) for rule in RULES for line in BOOK]


@pytest.fixture
def uneased(monkeypatch: pytest.MonkeyPatch) -> None:
    """These tests are about tapes, not easing: the ladder runs uneased here (EASED off), so
    a rule is simulated once and no placebo rung simulates again; with EASED on the cold, warm
    and tapeless runs take past 15 minutes on GitHub (20 Nov, #993). The eased path has its
    own tests (test_lab_rung_golden.py)."""
    monkeypatch.setattr(verdict, "EASED", False)


@pytest.fixture
def sims(monkeypatch: pytest.MonkeyPatch) -> list[Cell]:
    """Every simulation the cell engine is asked for, in order."""
    asked: list[Cell] = []
    real = cell.run

    def run(c: Cell, bars: Sequence[Bar]) -> Record:
        asked.append(c)
        return real(c, bars)

    monkeypatch.setattr(cell, "run", run)
    return asked


def _judge(home: Path) -> list[dict[str, object]]:
    ladder.run(home, _door(BOOK), {}, TODO, CLOCK)
    return _rows(home)


@pytest.mark.usefixtures("uneased")  #: counts simulations: a placebo rung would add some
def test_a_rung_changed_runs_no_simulation_and_a_rule_changed_only_its_own(
    tmp_path: Path, sims: list[Cell], monkeypatch: pytest.MonkeyPatch
) -> None:
    _judge(tmp_path)
    made = len(sims)
    assert made and len(list((tmp_path / "ladder" / tape.FOLDER).rglob("*.tape"))) == made
    found = rung.found
    monkeypatch.setattr(rung, "found", lambda r: (found(r)[0], (*found(r)[1], "a rung edited")))
    assert len(_judge(tmp_path)) == 2 * len(TODO) and len(sims) == made, "judged again, not run"
    run: Callable[[str], str] = lambda _: "v1"  # noqa: E731
    kept = tape.kept(tmp_path / "other", cell.run, run)
    for c in TODO:
        kept(c, BOOK[c.line])
    before = len(sims)
    run = lambda rule: "v2" if rule == RULES[0] else "v1"  # noqa: E731
    kept = tape.kept(tmp_path / "other", cell.run, run)
    for c in TODO:
        kept(c, BOOK[c.line])
    assert [c.strategy for c in sims[before:]] == [RULES[0]] * 2


@pytest.mark.usefixtures("uneased")  #: counts simulations: a placebo rung would add some
def test_the_rows_are_the_rows_there_were_cold_warm_and_with_no_tapes(
    tmp_path: Path, sims: list[Cell], monkeypatch: pytest.MonkeyPatch
) -> None:
    rules = ladder_epon.eponymous()
    todo = tuple(Cell(rule, VUSA, ladder.START, ladder.END) for rule in rules)

    def asked(home: Path) -> str:
        return ladder.run(home, _door(BOOK), {}, todo, CLOCK, ladder_sets.EPON)

    asked(tmp_path / "cold")
    cold, made = (tmp_path / "cold" / "ladder" / "EPON.jsonl").read_bytes(), len(sims)
    shutil.copytree(
        tmp_path / "cold" / "ladder" / tape.FOLDER, tmp_path / "warm" / "ladder" / "tapes"
    )
    asked(tmp_path / "warm")
    assert (tmp_path / "warm" / "ladder" / "EPON.jsonl").read_bytes() == cold and len(sims) == made
    monkeypatch.setattr(tape, "on", lambda _: nullcontext())  #: as it was before the split
    asked(tmp_path / "plain")
    assert (tmp_path / "plain" / "ladder" / "EPON.jsonl").read_bytes() == cold


@pytest.mark.usefixtures("uneased")  #: counts simulations: a placebo rung would add some
def test_a_run_stopped_takes_up_from_the_last_tape_written(
    tmp_path: Path, sims: list[Cell], monkeypatch: pytest.MonkeyPatch
) -> None:
    _judge(tmp_path / "whole")
    whole = len(sims)
    sims.clear()
    real, left = cell.run, [3]

    def stopping(c: Cell, bars: Sequence[Bar]) -> Record:
        left[0] -= 1
        if not left[0]:
            raise KeyboardInterrupt
        return real(c, bars)

    monkeypatch.setattr(cell, "run", stopping)
    with pytest.raises(KeyboardInterrupt):
        _judge(tmp_path / "home")
    monkeypatch.setattr(cell, "run", real)
    done = len(list((tmp_path / "home" / "ladder" / tape.FOLDER).rglob("*.tape")))
    assert done == 2 and not list((tmp_path / "home").rglob("*.new"))
    sims.clear()
    assert [r["cell"] for r in _judge(tmp_path / "home")] == [
        r["cell"] for r in _rows(tmp_path / "whole")
    ]
    assert len(sims) == whole - done


@pytest.mark.usefixtures("uneased")  #: counts simulations: a placebo rung would add some
def test_a_rule_is_simulated_once_on_a_line_and_each_window_is_cut_from_it(
    tmp_path: Path, sims: list[Cell]
) -> None:
    _judge(tmp_path)
    assert sorted(Counter((c.strategy, c.line.symbol) for c in sims).values()) == [1] * len(TODO)
    bars, kept = BOOK[VUSA], tape.kept(tmp_path / "cut", cell.run)
    days = [bar.day for bar in bars]
    for start, end in ((0, -1), (0, 300), (100, 400), (len(days) // 2, len(days) // 2 + 90)):
        window = Cell(RULES[0], VUSA, days[start], days[end])
        assert kept(window, bars) == cell.run(window, bars)


@pytest.mark.usefixtures("uneased")  #: counts simulations: a placebo rung would add some
def test_a_change_of_settings_prices_the_same_tape_again_and_simulates_nothing(
    tmp_path: Path, sims: list[Cell]
) -> None:
    bars, kept = BOOK[VUSA], tape.kept(tmp_path, cell.run)
    whole = Cell(RULES[0], VUSA, bars[0].day, bars[-1].day)
    record = kept(whole, bars)
    big, small = (
        rung.judge(record, bars, Settings(c), {}) for c in (Decimal(10_000), Decimal(500))
    )
    assert kept(whole, bars) == record and len(sims) == 1, "the tape was read, not run again"
    assert big.trades != small.trades


def test_a_tape_is_stored_compressed_and_reads_back_the_same(tmp_path: Path) -> None:
    c = TODO[0]
    bars = BOOK[c.line]
    whole = cell.run(Cell(c.strategy, c.line, bars[0].day, bars[-1].day), bars)
    tape.kept(tmp_path, cell.run)(c, bars)
    (file,) = tmp_path.glob("*.tape")
    assert file.stat().st_size < len(pickle.dumps((whole.bars, whole.trades)))
    assert tape.kept(tmp_path, lambda *_: pytest.fail("simulated"))(c, bars) == tape.kept(
        tmp_path / "cold", cell.run
    )(c, bars)


def test_editing_one_rule_of_a_file_leaves_its_sibling_keyed_as_it_was(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A shared helper moves both keys; a Windows line ending moves neither."""
    home = tmp_path / "desk"
    home.mkdir()
    monkeypatch.setattr(desk, "__path__", [*desk.__path__, str(home)])
    monkeypatch.setattr(sys, "modules", dict(sys.modules))  #: the planted file leaves no trace
    importlib.invalidate_caches()
    (home / "__init__.py").write_text("")
    text = "H = 1\n\n\nclass A: ...\n\n\nclass B:\n    n = 1\n\n\nEPONYMOUS = {'pa': A, 'pb': B}\n"
    path = home / "eponymous_planted.py"

    def keys(source: str | bytes) -> list[str]:
        path.write_bytes(source if isinstance(source, bytes) else source.encode())
        return [tape.code_of_rule(n, tmp_path, home) for n in ("pa", "pb")]

    a, b = keys(text)
    edited = keys(text.replace("n = 1", "n = 2"))
    assert edited[0] == a and edited[1] != b
    moved = keys(text.replace("H = 1", "H = 2"))
    assert moved[0] != a and moved[1] != b
    assert keys(text.replace("\n", "\r\n").encode()) == [a, b]


def test_a_rule_made_from_a_catalogue_row_is_keyed_by_its_row(tmp_path: Path) -> None:
    """T1: a row's params edited in the catalogue give its variants a new key, so no stale tape
    or verdict is read; a Python rule of the same name, which never reads the row, keeps its own."""
    variant, python = "connors_three_day_high_low[entry.n=2,exit.n=3]", "connors_three_day_high_low"
    edited = tmp_path / "catalogue.toml"
    text = rulebook.CATALOGUE.read_text(encoding="utf-8")
    edited.write_text(text.replace("filter = { n = 200 }", "filter = { n = 150 }", 1), "utf-8")
    assert tape.code_of_rule(variant, book=edited) != tape.code_of_rule(variant)
    assert tape.code_of_rule(python, book=edited) == tape.code_of_rule(python)
