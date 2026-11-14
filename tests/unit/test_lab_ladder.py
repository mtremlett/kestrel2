"""The ladder's first set: every published rule on every line through every rung built, each
answer kept with its reason and its count of trials; a run stopped anywhere takes up again."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from test_lab_reproduce import AT_CLOSE, _figure
from test_lab_reproduce import _bars as _author
from test_lab_rung import _walk

from desk import keeper
from desk.command import CAPITAL, POUND
from desk.lines import LINES, Line
from desk.orders import Settings
from desk.store import Bar
from lab import cell, deflated, folds, ladder, market, published, reproduce, rung, trials
from lab.cell import Cell
from lab.reproduce import Fill

VUSA, ISF, AAPL, SPY = (
    next(line for line in LINES if line.symbol == s) for s in ("VUSA", "ISF", "AAPL", "SPY")
)
#: a breakout that goes on rising, planted from 2010 to past the window's end; and none
EDGE, NOISE = _walk(1, 0.012, 0.012, days=3100), _walk(2, 0, 0, days=3100)
ROOM = Settings(CAPITAL)


def _set(*lines: Line) -> list[Cell]:
    return [Cell("breakout_20_10", line, ladder.START, ladder.END) for line in lines]


def _file(home: Path) -> Path:
    return home / "ladder" / "set1.jsonl"


def _rows(home: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in _file(home).read_text().splitlines()]


def test_each_cell_is_judged_on_every_rung_and_kept_with_its_reasons_and_trials(
    tmp_path: Path,
) -> None:
    book, todo = {VUSA: EDGE, ISF: NOISE}, _set(VUSA, ISF)
    said = ladder.run(tmp_path, book.__getitem__, {}, todo)
    assert said.startswith("ladder set 1: 2 cells") and "\n" not in said
    assert "against 6 trials: 2 judged now, 0 kept from before, 0 could not" in said
    assert "PASS 1, DOUBT 0, THIN 0, FAIL 1, FAULT 0; 0 not the author's rule; 0 passed" in said
    won, lost = _rows(tmp_path)
    #: each rung's answer is that rung's own, the cell and its two folds among six trials,
    #: priced from the desk's one capital and set beside its venue's market
    verdict = rung.judge(cell.run(todo[0], EDGE), EDGE, ROOM, {})
    register = tmp_path / "ladder" / "set1.trials.jsonl"
    (one,) = deflated.read(trials.correct(register, ladder.QUESTION, [verdict]))
    want = {name: answer.name for name, answer in one.rungs.items()} | {
        "folds": folds.judge(todo[0], EDGE, ROOM, {}, ladder.FOLDS).answer.name,
        "market": market.judge(verdict, EDGE, ISF, NOISE, {}).answer.name,
    }
    assert {name: answer for name, (answer, _) in won["rungs"].items()} == want
    assert (won["trials"], one.luck.trials, won["trades"]) == (6, 6, len(verdict.trades))
    assert f"{verdict.t:.2f} standard errors above" in won["rungs"]["first"][1]
    assert "times 6 trials" in won["rungs"]["luck"][1] and all(w for _, w in won["rungs"].values())
    #: the planted edge passes the one rule, and its worst fold made too few trades to say:
    #: so it has not passed every rung. The noise fails; no rung left out is left in silence
    assert want == dict.fromkeys(want, "PASS") | {"folds": "THIN"}
    assert (won["answer"], won["every"], lost["answer"]) == ("PASS", False, "FAIL")
    assert lost["rungs"]["first"][0] == lost["rungs"]["market"][0] == "FAIL"
    assert set(won["unrun"]) == {"reproduce", "regime", "plateau", "stress"}


def test_a_run_skips_what_is_kept_and_judges_again_only_what_has_changed(tmp_path: Path) -> None:
    book, todo = {VUSA: EDGE, ISF: NOISE}, _set(VUSA, ISF)
    ladder.run(tmp_path, book.__getitem__, {}, todo)
    kept = _file(tmp_path).read_bytes()
    assert "0 judged now, 2 kept from before" in ladder.run(tmp_path, book.__getitem__, {}, todo)
    _file(tmp_path).write_bytes(kept + b'{"set": 1, "cel')  #: a stop cut a line short
    ladder.run(tmp_path, book.__getitem__, {}, todo)
    assert _file(tmp_path).read_bytes() == kept
    #: one bar of the market mended: both cells stand on it, and each has a new last line
    book[ISF] = (*NOISE[:100], replace(NOISE[100], volume=7), *NOISE[101:])
    assert "2 judged now, 0 kept" in ladder.run(tmp_path, book.__getitem__, {}, todo)
    rows = _rows(tmp_path)
    assert [row["cell"][1] for row in rows] == ["VUSA", "ISF", "VUSA", "ISF"]
    assert (
        rows[0]["key"] != rows[2]["key"] and rows[0]["rungs"]["first"] == rows[2]["rungs"]["first"]
    )
    #: the set grown by a dollar line with no bars: nine trials now, so all are judged again;
    #: the one that cannot be is kept with its reason and tried on every run, written once
    more = _set(VUSA, ISF, AAPL)
    said = ladder.run(tmp_path, book.__getitem__, {}, more)
    assert "against 9 trials: 2 judged now, 0 kept from before, 1 could not be judged" in said
    assert "0 judged now, 2 kept from before, 1 could" in ladder.run(
        tmp_path, book.__getitem__, {}, more
    )
    assert [row["trials"] for row in _rows(tmp_path)] == [6, 6, 6, 6, 9, 9, 9]
    assert _rows(tmp_path)[-1]["error"].startswith("KeyError") and "key" not in _rows(tmp_path)[-1]
    #: its bars found, and no rate of exchange: refused with the day; the rates given, judged
    book |= {AAPL: EDGE, SPY: NOISE}
    assert "1 could not be judged" in ladder.run(tmp_path, book.__getitem__, {}, more)
    assert "no rate of pounds per USD" in _rows(tmp_path)[-1]["error"]
    pounds = {bar.day: Decimal("0.8") for bar in EDGE}
    assert "1 judged now, 2 kept from before, 0 could" in ladder.run(
        tmp_path, book.__getitem__, pounds, more
    )
    assert _rows(tmp_path)[-1]["answer"] == "PASS" and len(_rows(tmp_path)) == 9
    #: a dearer dollar on one day is another price: the dollar line alone is judged again
    pounds[EDGE[50].day] = Decimal("0.9")
    assert "1 judged now, 2 kept" in ladder.run(tmp_path, book.__getitem__, pounds, more)


def test_every_trial_is_counted_before_any_is_run_and_the_count_never_begins_again(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    said = ladder.run(tmp_path, {}.__getitem__, {}, _set(VUSA, ISF))
    assert "against 6 trials: 0 judged now, 0 kept from before, 2 could not be judged" in said
    register = tmp_path / "ladder" / "set1.trials.jsonl"
    assert trials.count(register, ladder.QUESTION) == 6
    register.unlink()  #: results with no register beside them: refused, never counted anew
    with pytest.raises(FileNotFoundError, match="no register of trials"):
        ladder.run(tmp_path, {}.__getitem__, {}, _set(VUSA, ISF))
    monkeypatch.setitem(cell.RUNGS, "lab.ladder", "edited since")
    with pytest.raises(RuntimeError, match="code on disk has changed"):
        ladder.run(tmp_path, {}.__getitem__, {}, _set(VUSA))


def test_a_rule_with_a_figure_on_file_is_judged_only_behind_its_authors_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    book, todo = {VUSA: _author(), ISF: NOISE}, _set(VUSA)
    monkeypatch.setattr(reproduce, "FIGURES", (_figure(Fill.NEXT_OPEN, *AT_CLOSE),))
    said = ladder.run(tmp_path / "missed", book.__getitem__, {}, todo)
    (missed,) = _rows(tmp_path / "missed")
    assert list(missed["rungs"]) == ["reproduce"] and "answer" not in missed
    assert (
        missed["rungs"]["reproduce"][0] == "FAIL"
        and "not reproduced" in missed["rungs"]["reproduce"][1]
    )
    assert "1 judged now" in said and "1 not the author's rule" in said
    monkeypatch.setattr(reproduce, "FIGURES", (_figure(Fill.CLOSE, *AT_CLOSE),))
    ladder.run(tmp_path / "made", book.__getitem__, {}, todo)
    (made,) = _rows(tmp_path / "made")
    answer, why = made["rungs"]["reproduce"]
    assert answer == "PASS" and "the author's result, a planted author" in why
    #: two trades in the author's few weeks: not enough evidence on ours, and the folds wait
    assert made["rungs"]["first"][0] == made["answer"] == "THIN"
    assert "folds" in made["unrun"] and "reproduce" not in made["unrun"]


def test_the_set_is_every_published_rule_on_every_line_and_its_doors_are_the_desks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    made = ladder.cells()
    assert len(made) == len(set(made)) == len(published.PUBLISHED) * len(LINES)
    assert {(c.start, c.end) for c in made} == {(ladder.START, ladder.END)}
    assert ladder.names(made[0])[0] == trials.name(made[0])
    assert len(set(ladder.names(made[0]))) == 1 + ladder.FOLDS
    #: a day's rate is one over the pound's last close before it: none from a close that is
    #: no pound's, none from one over four days old
    day, step = date(2020, 1, 6), keeper.DAY
    closes = [(day, "1.25"), (day + step, "2.5"), (day + 10 * step, "1.6")]

    def ask(line: Line, before: date) -> list[Bar]:
        assert (line, before) == (POUND, ladder.END + step)
        return [Bar(at, *[Decimal(close)] * 4, 0) for at, close in closes]

    pounds = ladder.rates(ask)
    assert sorted(pounds) == [day + n * step for n in (1, 11, 12, 13, 14)]
    assert (pounds[day + step], pounds[day + 11 * step]) == (Decimal("0.8"), Decimal("0.625"))
    #: bars come through the keeper's door, up to the window's end; a parked line is refused
    parked: set[str] = set()

    def saved(home: Path, before: date, lines: list[Line]) -> Any:
        assert (home, before, lines) == (tmp_path, ladder.END + step, [VUSA])
        return {VUSA: EDGE[:3]}, frozenset(parked)

    monkeypatch.setattr(keeper, "saved", saved)
    assert ladder.stored(tmp_path)(VUSA) == EDGE[:3]
    parked.add("VUSA")
    with pytest.raises(ValueError, match="VUSA: parked"):
        ladder.stored(tmp_path)(VUSA)
    with pytest.raises(SystemExit, match="KESTREL2_DATA names no data folder"):
        ladder.main({})
