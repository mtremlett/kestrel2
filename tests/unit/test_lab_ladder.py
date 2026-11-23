"""The ladder's first set: every published rule on every line through every rung built, each
answer kept with its reason and its count of trials; a run stopped anywhere takes up again."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
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
from lab import (
    cell,
    deflated,
    folds,
    ladder,
    ladder_parts,
    ladder_sets,
    market,
    published,
    reproduce,
    rung,
    rung_ci,
    rung_costs,
    rung_cpcv,
    rung_regimes,
    shuffle,
    stress,
    tape,
    trials,
    verdict,
    weather,
)
from lab.batch import Bars
from lab.cell import Cell
from lab.reproduce import Fill
from lab.rung import Answer

VUSA, ISF, AAPL, SPY = (
    next(line for line in LINES if line.symbol == s) for s in ("VUSA", "ISF", "AAPL", "SPY")
)
#: a breakout that goes on rising, planted from 2010 to past the window's end; and none
EDGE, NOISE = _walk(1, 0.012, 0.012, days=3100), _walk(2, 0, 0, days=3100)
ROOM = Settings(CAPITAL)
RULES = ("breakout_20_10", "trend_50_200")
ISF_START = NOISE[0].day


@pytest.fixture
def eased_off(monkeypatch: pytest.MonkeyPatch) -> None:
    """The off assertions of these tests: the ladder's easing switch is set off, not assumed."""
    monkeypatch.setattr(verdict, "EASED", False)


def _set(*lines: Line) -> list[Cell]:
    return [Cell("breakout_20_10", line, ladder.START, ladder.END) for line in lines]


def _door(book: Mapping[Line, Sequence[Bar]]) -> Bars:
    """The book's bars; a line it does not hold is refused as the keeper's door refuses it."""

    def bars(line: Line) -> Sequence[Bar]:
        if line not in book:
            raise keeper.Stale(f"{line.symbol}: no bars are held")
        return book[line]

    return bars


def _file(home: Path) -> Path:
    return home / "ladder" / "set1.jsonl"


def _rows(home: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in _file(home).read_text().splitlines()]


@pytest.mark.usefixtures(
    "eased_off"
)  #: its want is the off ladder's own answers, not the graded ones
def test_each_cell_is_judged_on_every_rung_and_kept_with_its_reasons_and_trials(
    tmp_path: Path,
) -> None:
    book, todo = {VUSA: EDGE, ISF: NOISE}, _set(VUSA, ISF)
    said = ladder.run(tmp_path, _door(book), {}, todo)
    assert said.startswith("ladder set 1: 2 cells") and "\n" not in said
    assert "against 2 trials: 2 judged now, 0 kept from before, 0 could not" in said
    assert "PASS 0, DOUBT 0, THIN 1, FAIL 1, FAULT 0; 0 with no verdict, a named" in said
    won, lost = _rows(tmp_path)
    #: each rung's answer is that rung's own, the two cells alone among two trials (a fold is
    #: no trial), the folds the rule's years pooled over its lines, priced from the desk's one
    #: capital and set beside its venue's market; and the window judged begins at the line's
    #: first bar, so a yearly figure is of years it had bars in
    own = Cell("breakout_20_10", VUSA, EDGE[0].day, ladder.END)
    verdict = rung.judge(cell.run(own, EDGE), EDGE, ROOM, {})
    (one,) = deflated.judge([verdict], 1)
    assert won["from"] == "2010-01-01" and f"of {one.yearly:.2f};" in won["rungs"]["yearly"][1]
    want = {name: answer.name for name, answer in one.rungs.items()} | {
        "folds": folds.pool(
            [(own, EDGE), (Cell(own.strategy, ISF, ISF_START, own.end), NOISE)], ROOM, {}
        ).answer.name,
        "market": market.judge(verdict, EDGE, ISF, NOISE, {}).answer.name,
        "ci": rung_ci.judge(verdict.gains).name,
        "stress": stress.judge(own, EDGE, ROOM, {}).judged()[0].name,
        "costs": rung_costs.judge(verdict).answer.name,
        "cpcv": rung_cpcv.judge(verdict).answer.name,
        "regime": rung_regimes.by_weather(
            verdict.key.rung(rung_regimes.__name__), verdict.trades, weather.trend(EDGE), ()
        ).answer.name,
        "regimes": rung_regimes.RUNG.judge(verdict)[0].name,
        "shuffle": "THIN",  #: run last, and only on a trial that passed all before it
    }
    assert {name: answer for name, (answer, _) in won["rungs"].items()} == want
    assert (won["trials"], one.luck.trials, won["trades"]) == (2, 2, len(verdict.trades))
    assert f"{verdict.t:.2f} standard errors above" in won["rungs"]["first"][1]
    assert "times 2 trials" in won["rungs"]["luck"][1] and all(w for _, w in won["rungs"].values())
    #: the planted edge passes every rung but its worst fold, too thin to say: so the one
    #: verdict, over every named rung, is THIN. The noise fails; no rung is left in silence
    assert want == dict.fromkeys(want, "PASS") | {
        "folds": "THIN",
        "regime": "THIN",
        "shuffle": "THIN",
    }
    assert (won["answer"], won["every"], lost["answer"]) == ("THIN", False, "FAIL")
    assert lost["rungs"]["first"][0] == lost["rungs"]["market"][0] == "FAIL"
    assert set(won["unrun"]) == {"reproduce", "plateau", "unwired"}
    #: the rungs built in modules the ladder does not yet judge are named, never left in silence
    assert "rung_dsr" in won["unrun"]["unwired"] and "declare no RUNG" in won["unrun"]["unwired"]
    assert 0 <= won["drawdown"]["median"] <= won["drawdown"]["p95"] < 1, "measured, never gated"


def test_a_planted_edge_is_judged_by_its_years_pooled_over_the_rules_lines_not_found_thin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Sixteen lines with the edge planted in the last 2,400 days of each: a line alone makes
    two or three trades a year, too few to be heard, and the rule's sixteen together make over
    thirty. So the fold of each of the five years PASSES, and the one answer is every line's."""
    monkeypatch.setattr(shuffle, "share", lambda *_: Decimal("0.01"))  #: a hundred runs each
    names = "3LGO 2MU SMGB IITU VHYG 5QQQ ISF VUSA SGLN VUAG EQQQ IB1T AAPL TSLA NVDA AMD".split()
    lines = [next(line for line in LINES if line.symbol == name) for name in names]
    walks = {line: _walk(n, 0.012, 0.012, days=3100)[-2400:] for n, line in enumerate(lines, 1)}
    pounds = {bar.day: Decimal("0.8") for bar in EDGE}
    ladder.run(tmp_path, _door(walks | {SPY: NOISE}), pounds, _set(*lines))
    rows = _rows(tmp_path)
    assert [row["cell"][1] for row in rows] == list(names) and not [r for r in rows if "error" in r]
    folded = {tuple(row["rungs"]["folds"]) for row in rows}
    assert len(folded) == 1 and next(iter(folded))[0] == "PASS", folded
    assert (
        "worst of 5 yearly folds" in next(iter(folded))[1]
        and "over 16 lines" in next(iter(folded))[1]
    )


def test_a_rule_edited_judges_again_only_its_own_cells(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    book = {VUSA: EDGE, ISF: NOISE}
    todo = [Cell(r, line, ladder.START, ladder.END) for r in RULES for line in book]
    at = datetime(2026, 11, 14, tzinfo=UTC)
    assert "4 judged now" in ladder.run(tmp_path, _door(book), {}, todo, lambda: at)
    real = tape.rule_code
    edited = lambda rule: "edited" if rule == RULES[0] else real(rule)  # noqa: E731
    monkeypatch.setattr(tape, "rule_code", edited)
    said = ladder.run(tmp_path, _door(book), {}, todo, lambda: at)
    assert "2 judged now, 2 kept from before" in said
    assert [r["cell"][0] for r in _rows(tmp_path)[4:]] == [RULES[0]] * 2


def test_a_run_skips_what_is_kept_and_judges_again_only_what_has_changed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    book, todo = {VUSA: EDGE, ISF: NOISE}, _set(VUSA, ISF)
    start = datetime(2026, 11, 14, tzinfo=UTC)
    tick = iter(start + timedelta(hours=n) for n in range(100))  #: each run an hour on

    def run(home: Path, bars: Bars, pounds: Mapping[date, Decimal], todo: list[Cell]) -> str:
        at = next(tick)
        return ladder.run(home, bars, pounds, todo, lambda: at)

    run(tmp_path, _door(book), {}, todo)
    kept = _file(tmp_path).read_bytes()
    assert "0 judged now, 2 kept from before" in run(tmp_path, _door(book), {}, todo)
    _file(tmp_path).write_bytes(kept + b'{"set": 1, "cel')  #: a stop cut a line short
    run(tmp_path, _door(book), {}, todo)
    assert _file(tmp_path).read_bytes() == kept
    #: one bar of the market mended: both cells stand on it, and each has a new last line
    book[ISF] = (*NOISE[:100], replace(NOISE[100], volume=7), *NOISE[101:])
    assert "2 judged now, 0 kept" in run(tmp_path, _door(book), {}, todo)
    rows = _rows(tmp_path)
    assert [row["cell"][1] for row in rows] == ["VUSA", "ISF", "VUSA", "ISF"]
    assert (
        rows[0]["key"] != rows[2]["key"] and rows[0]["rungs"]["first"] == rows[2]["rungs"]["first"]
    )
    #: the set grown by a dollar line with no bars: three trials now, so all are judged again;
    #: the one that cannot be is kept with its reason and its try time, tried an hour on
    more = _set(VUSA, ISF, AAPL)
    said = run(tmp_path, _door(book), {}, more)
    assert "against 3 trials: 2 judged now, 0 kept from before, 1 could not be judged" in said
    assert "0 judged now, 2 kept from before, 1 could" in run(tmp_path, _door(book), {}, more)
    assert [row["trials"] for row in _rows(tmp_path)] == [2, 2, 2, 2, 3, 3, 3, 3]
    assert _rows(tmp_path)[-1]["error"].startswith("Stale") and "key" not in _rows(tmp_path)[-1]
    #: its bars found, and no rate of exchange: the set refuses to start, naming the first day
    #: unrated, and writes nothing (L20); the rates given, judged
    book |= {AAPL: EDGE, SPY: NOISE}
    with pytest.raises(ValueError, match="refuses to start, first AAPL: no rate of pounds per"):
        run(tmp_path, _door(book), {}, more)
    assert len(_rows(tmp_path)) == 8
    pounds = {bar.day: Decimal("0.8") for bar in EDGE}
    said = run(tmp_path, _door(book), pounds, more)
    #: the dollar line joins its rule's pooled folds, so the two pound lines are judged again too
    assert "3 judged now, 0 kept from before, 0 could" in said
    assert _rows(tmp_path)[-1]["answer"] == "THIN" and len(_rows(tmp_path)) == 11
    #: a dearer dollar on one day is another price, in the folds of all three
    pounds[EDGE[50].day] = Decimal("0.9")
    assert "3 judged now, 0 kept" in run(tmp_path, _door(book), pounds, more)
    assert "0 judged now, 3 kept" in run(tmp_path, _door(book), pounds, more)
    monkeypatch.setattr(ladder, "CAPITAL", CAPITAL * 2)  #: a bigger pot is another key
    assert "3 judged now, 0 kept" in run(tmp_path, _door(book), pounds, more)


def test_a_line_the_desks_sizing_refuses_is_a_judged_outcome_and_the_set_carries_on(
    tmp_path: Path,
) -> None:
    dear = [
        replace(b, open=b.open * 999, high=b.high * 999, low=b.low * 999, close=b.close * 999)
        for b in EDGE
    ]  #: one share costs more than the room of 2000 pounds
    book = {ISF: NOISE, VUSA: dear, AAPL: EDGE, SPY: NOISE}
    pounds = {bar.day: Decimal("0.8") for bar in EDGE}
    said = ladder.run(tmp_path, _door(book), pounds, _set(VUSA, ISF))
    refused, fine = _rows(tmp_path)
    assert (
        refused["refused"].startswith("refused by the desk's sizing: ") and "error" not in refused
    )
    assert "answer" not in refused and fine["answer"] in ("THIN", "FAIL") and "refused" not in fine
    assert "1 judged now, 0 kept from before, 0 could not be judged and are tried" in said
    assert "again next run, 1 refused by the desk's sizing;" in said
    assert "0 judged now, 1 kept" in ladder.run(tmp_path, _door(book), pounds, _set(VUSA, ISF))
    assert verdict.cell_line(refused)[1].startswith("refused by the desk's sizing")


def test_a_short_line_is_judged_on_its_proxys_longer_bars_and_says_so(tmp_path: Path) -> None:
    vuag = next(line for line in LINES if line.symbol == "VUAG")
    pounds = {bar.day: Decimal("0.8") for bar in EDGE}
    book = {vuag: EDGE[1500:], SPY: EDGE, ISF: NOISE}  #: VUAG began 1,500 days after SPY
    ladder.run(tmp_path, _door(book), pounds, _set(vuag, VUSA))
    short, plain = _rows(tmp_path)  #: VUSA has no proxy; VUAG's cell stays VUAG, never SPY
    assert short["cell"][1] == "VUAG" and short["proxy"] == "proxy: SPY for VUAG"
    assert short.get("error") is None, short
    assert short["from"] == EDGE[0].day.isoformat() and "proxy" not in plain
    book[vuag] = EDGE  #: no shorter than its proxy: judged on its own bars, no label
    ladder.run(tmp_path / "own", _door(book), pounds, _set(vuag))
    assert "proxy" not in _rows(tmp_path / "own")[0]
    said = verdict.cell_line(short)[1]
    assert said.startswith("proxy: SPY for VUAG <br>")


def test_every_trial_is_counted_before_any_is_run_and_the_count_never_begins_again(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    register = tmp_path / "ladder" / "set1.trials.jsonl"
    register.parent.mkdir()  #: a first run stopped before its register was whole begins again
    register.with_suffix(".new").write_bytes(trials.HEAD)
    clock, todo = [datetime(2026, 11, 14, 12, 0, tzinfo=UTC)], _set(VUSA, ISF)
    said = ladder.run(tmp_path, _door({}), {}, todo, lambda: clock[0])
    assert "against 2 trials: 0 judged now, 0 kept from before, 2 could not be judged" in said
    assert trials.count(register, ladder.QUESTION) == 2
    #: a line too short to have made a trade waits on its history: with nothing changed it is
    #: never appended again, however long on, and the moment its bars differ it is judged
    short = _door({VUSA: EDGE[:1], ISF: NOISE})
    clock[0] += timedelta(minutes=30)
    ladder.run(tmp_path, short, {}, todo, lambda: clock[0])
    waits = _rows(tmp_path)[2]
    assert "waits on 452" in waits["error"] and "answer" not in waits and "key" in waits
    clock[0] += timedelta(hours=2)
    before = _file(tmp_path).read_bytes()
    ladder.run(tmp_path, short, {}, todo, lambda: clock[0])
    assert (
        _file(tmp_path).read_bytes() == before
        and len(_rows(tmp_path)) == 4
        and _rows(tmp_path)[2] == waits
    )
    ladder.run(tmp_path, _door({VUSA: EDGE, ISF: NOISE}), {}, todo, lambda: clock[0])
    #: both are judged again, for their rule's lines are not as they were: the edge, with
    #: 6 or 7 trades a year pooled over two lines, is too thin to say; the noise fails
    assert [row["answer"] for row in _rows(tmp_path)[-2:]] == ["THIN", "FAIL"]
    holed = NOISE[:4] + NOISE[5:]  #: the market missing Tuesday 5 January 2010, a session
    with pytest.raises(
        ValueError, match="^1 gap in the set's inputs.* ISF has no bar on 2010-01-05"
    ):
        ladder.run(tmp_path / "holed", _door({VUSA: EDGE, ISF: holed}), {}, todo)
    assert not (tmp_path / "holed").exists()  #: refused before its register or a row
    #: a cell with a rung FAULT is a fault; over 1% of the cells and the table is withheld
    ok, bad = {"rungs": {"first": ["WEAK", ""]}}, {"rungs": {"folds": ["FAULT", "no years"]}}
    assert (
        ladder_parts.faults([ok] * 99 + [bad])[1] and not ladder_parts.faults([ok] * 98 + [bad])[1]
    )
    assert ladder_parts.faults([ok] * 98 + [bad])[0][-1] == "NOT PUBLISHED: 1 of 99 cells FAULT"
    register.unlink()  #: results with no register beside them: refused, never counted anew
    with pytest.raises(FileNotFoundError, match="no register of trials"):
        ladder.run(tmp_path, _door({}), {}, _set(VUSA, ISF))
    monkeypatch.setitem(cell.RUNGS, "lab.ladder", "edited since")
    with pytest.raises(RuntimeError, match="code on disk has changed"):
        ladder.run(tmp_path, _door({}), {}, _set(VUSA))


@pytest.mark.usefixtures("eased_off")  #: its want is the off ladder's rows, with no placebo rung
def test_a_rule_with_a_figure_on_file_is_judged_only_behind_its_authors_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    author, todo = _author(), _set(ISF)  #: the author's market is VUSA; the line judged, ISF
    book = {VUSA: author, ISF: EDGE}
    monkeypatch.setattr(reproduce, "FIGURES", (_figure(Fill.NEXT_OPEN, *AT_CLOSE),))
    said = ladder.run(tmp_path / "missed", _door(book), {}, todo)
    (missed,) = _rows(tmp_path / "missed")
    assert list(missed["rungs"]) == ["reproduce"] and "answer" not in missed
    answer, why = missed["rungs"]["reproduce"]
    assert answer == "FAIL" and "not reproduced" in why
    assert "1 judged now" in said and "1 not the author's rule; 0 passed" in said
    monkeypatch.setattr(reproduce, "FIGURES", (_figure(Fill.CLOSE, *AT_CLOSE),))
    said = ladder.run(tmp_path / "made", _door(book), {}, todo)
    (made,) = _rows(tmp_path / "made")
    answer, why = made["rungs"]["reproduce"]
    assert answer == "PASS" and "the author's result, a planted author" in why
    #: the folds take the author's result with the rest and are judged: on this one line they
    #: hold 2 trades a year, too few to say, so the worst fold holds the verdict at THIN
    assert "folds" in made["rungs"] and not {"folds", "reproduce"} & set(made["unrun"])
    answer, why = made["rungs"]["folds"]
    assert answer == made["answer"] == "THIN" and "2 trades" in why
    assert "every rung run, 0 of them behind" in said
    #: a bar of the author's market mended: another result stands behind it, so judged again
    book[VUSA] = (replace(author[0], volume=7), *author[1:])
    assert "1 judged now, 0 kept" in ladder.run(tmp_path / "made", _door(book), {}, todo)


def test_eased_on_a_cell_is_judged_with_its_rules_family_count_not_left_as_could_not(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(verdict, "EASED", True)
    assert "0 could not" in ladder.run(tmp_path, _door({VUSA: EDGE, ISF: NOISE}), {}, _set(VUSA))


def test_the_set_is_every_published_rule_on_every_line_and_its_doors_are_the_desks() -> None:
    made = ladder.cells()
    assert len(made) == len(set(made)) == len(published.PUBLISHED) * len(LINES)
    assert {(c.start, c.end) for c in made} == {(ladder.START, ladder.END)}
    assert ladder.names(made[0])[0] == trials.name(made[0])
    assert ladder.names(made[0]) == [trials.name(made[0])] and ladder.FOLDS == 5
    #: a day's rate is the desk's one rule (desk/carry.py): one over the pound's last close
    #: before it while fresh, none from a close that is no pound's; 2025-04-22, the day after
    #: Easter Monday, whose last close is five days old, has its rate
    step = keeper.DAY
    at = [(date(2025, 4, 17), "1.25"), (date(2025, 4, 23), "2.5"), (date(2025, 4, 24), "1.6")]

    def ask(line: Line, before: date) -> list[Bar]:
        assert (line, before) == (POUND, ladder.END + step)
        return [Bar(when, Decimal(c), Decimal(c), Decimal(c), Decimal(c), 0) for when, c in at]

    pounds = ladder.rates(ask)
    assert pounds[date(2025, 4, 22)] == Decimal("0.8") and date(2025, 4, 21) in pounds
    assert date(2025, 4, 24) not in pounds and pounds[date(2025, 4, 25)] == Decimal("0.625")
    with pytest.raises(SystemExit, match="KESTREL2_DATA names no data folder"):
        ladder_sets.main({})


def test_the_shuffle_is_run_last_and_only_on_a_trial_that_passed_every_rung_before_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    own = Cell("breakout_20_10", VUSA, EDGE[0].day, ladder.END)
    before = {name: (Answer.PASS, "") for name in deflated.NAMED[:-1]}
    ran = verdict.shuffled(own, EDGE, ROOM, {}, before, ())  # the only run of a hundred
    assert ran is not None and ran[0] is Answer.PASS and "100 shuffles" in ran[1]
    monkeypatch.setattr(shuffle, "share", lambda *_: pytest.fail("shuffled for nothing"))
    doubt = before | {"yearly": (Answer.DOUBT, "too good")}
    #: its answer the least, its words its own
    unrun = verdict.shuffled(own, EDGE, ROOM, {}, doubt, ())
    assert unrun is not None and unrun[0] is Answer.DOUBT and "too good" not in unrun[1]
    assert unrun[1].startswith("not run") and "yearly answered DOUBT" in unrun[1]
    assert verdict.shuffled(own, EDGE, ROOM, {}, {"first": before["first"]}, ()) is None


def test_superseded_lines_compact_to_one_per_cell_and_a_stop_mid_rewrite_leaves_the_file_whole(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    file = tmp_path / "set.jsonl"
    old = [{"cell": [k], "n": n} for n, k in enumerate("abaab")]
    file.write_bytes(b"".join(json.dumps(r).encode() + b"\n" for r in old))
    before = ladder.Kept(file)
    last = {k: before.get(k) for k in before.at}
    whole = file.read_bytes()

    def stopped(*_: object) -> Path:
        raise KeyboardInterrupt

    monkeypatch.setattr(Path, "replace", stopped)
    with pytest.raises(KeyboardInterrupt):
        before.compact()
    assert file.read_bytes() == whole  #: a stop mid-rewrite: the old file whole
    monkeypatch.undo()
    before.compact()
    after = ladder.Kept(file)
    assert after.lines == 2 and {k: after.get(k) for k in after.at} == last
    assert file.read_bytes().count(b"\n") == 2
