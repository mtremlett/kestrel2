"""The verdict of one cell (`lab/verdict.py`): the one rule reads the folds and the market, a
step of units is refused before any rung, a line too young is its own label, and nothing goes
forward while a rung is unrun."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from test_lab_ladder import EDGE, ISF, NOISE, ROOM, VUSA, eased_off  # noqa: F401 - used by name

from desk.store import Bar
from lab import deflated, ladder, market, shuffle, verdict
from lab.cell import Cell
from lab.folds import Pooled
from lab.rung import Answer, Rates

#: the off ladder's cells, asked for by name
OFF = pytest.mark.usefixtures("eased_off")
CELL = Cell("breakout_20_10", VUSA, EDGE[0].day, ladder.END)


def _judge(
    bars: Sequence[Bar] = EDGE, pounds: Rates | None = None, sour: bool = False
) -> dict[str, Any]:
    """The cell's verdict with the folds of its rule, the one line pooled; `sour` has the
    worst year fail."""
    pooled = verdict.pool([(CELL, EDGE)], {})
    if sour:
        pooled = replace(pooled, years=(replace(pooled.years[0], answer=Answer.FAIL),))
    return verdict.judge(CELL, bars, ISF, NOISE, pounds or {}, 6, (), lambda: pooled)


@pytest.mark.parametrize("rung_failing", ["folds", "market"])
@OFF
def test_a_cell_failing_only_one_rung_is_not_a_pass(
    monkeypatch: pytest.MonkeyPatch, rung_failing: str
) -> None:
    real = market.judge
    if rung_failing == "market":
        monkeypatch.setattr(
            market, "judge", lambda *a: replace(real(*a), answer=Answer.FAIL, line=None)
        )
    sour = rung_failing == "folds"
    rungs = _judge(sour=sour)["rungs"]
    others = {name: answer for name, (answer, _) in rungs.items() if name != rung_failing}
    assert rungs[rung_failing][0] == "FAIL" and others["first"] == "PASS"
    #: a soft market FAIL never leaks into the shuffle; the fixture's THIN folds decide
    said = {"folds": "FAIL", "market": "THIN"}[rung_failing]
    assert _judge(sour=sour)["every"] is False and _judge(sour=sour)["answer"] == said


def test_a_luck_fail_alone_never_holds_a_cell_back() -> None:
    #: L18: the luck rung is reported only, the deflated Sharpe the gate (R-RUNGS-36)
    passed = dict.fromkeys([*deflated.NAMED, "stress"], (Answer.PASS, "why"))
    assert verdict.every(passed | {"luck": (Answer.FAIL, "why")})
    assert not verdict.every(passed | {"stress": (Answer.FAIL, "why")})


def test_a_step_of_units_is_refused_unless_the_master_names_it() -> None:
    day = EDGE[300].day
    up = Decimal("1.27")
    stepped = [
        bar
        if bar.day < day
        else Bar(bar.day, bar.open * up, bar.high * up, bar.low * up, bar.close * up, bar.volume)
        for bar in EDGE
    ]
    pounds = {bar.day: Decimal("0.79") for bar in EDGE}
    with pytest.raises(verdict.UnitStep, match=str(day)):
        _judge(stepped, pounds)
    named = replace(VUSA, real_moves=frozenset({(day, stepped[300].close)}))
    verdict._unstepped(named, stepped, pounds)
    verdict._unstepped(VUSA, EDGE, pounds)
    #: the same rise made inside the session, from an open at the close before: a real move, not
    #: units (the blind review, R-RUNNER-40: 251 London lines refused, most for a crash day)
    rose = replace(EDGE[300], open=EDGE[299].close, low=EDGE[299].close, close=stepped[300].close)
    verdict._unstepped(VUSA, [*EDGE[:300], replace(rose, high=rose.close)], pounds)


def test_nothing_goes_forward_while_a_rung_is_unrun_and_the_table_says_cells_beside_trials(
    tmp_path: Path,
) -> None:
    passed = {"first": ["PASS", "passed"]}
    row = {"cell": ["breakout_20_10", "VUSA", "LSE"], "trials": 3, "answer": "PASS", "every": True}
    row |= {"rungs": passed, "unrun": {"regime": "the weather is not built"}}
    row |= {"holding": "+1.00% strategy, +0.50% holding ISF, +0.50% difference"}
    assert not verdict.goes(row) and verdict.goes(row | {"unrun": {}})
    assert not verdict.goes({k: v for k, v in row.items() if k != "unrun"}), "unsaid is not none"
    table = verdict.write_table(
        tmp_path, "T", "Does it earn?", [row], ["breakout_20_10"], 3, (7, 11)
    )
    md = table.read_text(encoding="utf-8")
    assert (
        "\nrungs built: 7 of 11\n" in md
        and ": 0 of 1 lines go forward" in md
        and md.rstrip().endswith("| no |")
    )
    assert "| holding |" in md and "+0.50% holding ISF, +0.50% difference |" in md
    assert "Does it earn? Cells: 1. Each is judged against 3 trials" in md
    data = json.loads(table.with_suffix(".json").read_text(encoding="utf-8"))
    assert (data["cells"], data["trials"], data["rules"][0]["passed"]) == (1, 3, False)
    assert (data["rungs_built"], data["rungs"]) == (7, 11)


def test_the_table_s_path_never_holds_a_partial_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[tuple[str, bool]] = []
    swap = Path.replace

    def spy(self: Path, target: Any) -> Path:
        seen.append((Path(target).name, Path(target).exists()))
        assert self.read_text(encoding="utf-8")
        return swap(self, target)

    monkeypatch.setattr(Path, "replace", spy)
    verdict.write_table(tmp_path, "T", "Does it earn?", [], [], 0, (0, 1))
    assert seen == [("T.json", False), ("T.md", False)], "content appears only by the replace"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["T.json", "T.md"], "no .tmp left"


@OFF
def test_every_judged_cell_says_what_simply_holding_its_market_made() -> None:
    said = _judge()["holding"]
    assert "% strategy, " in said and " holding ISF, " in said and said.endswith(" difference")


def test_a_line_too_young_to_have_traded_is_too_young_and_no_fault() -> None:
    with pytest.raises(verdict.TooYoung, match="waits on 452"):
        _judge(EDGE[:100])
    assert not issubclass(verdict.TooYoung, ArithmeticError)


def test_resampled_drawdowns_are_parts_of_the_capital_and_drawn_the_same_again() -> None:
    #: +500 and -500 drawn twice: a fall of 0, 500, 500 or 1,000 pounds, of 10,000 capital
    both = [Decimal(500), Decimal(-500)]
    assert verdict.drawdowns(both, "a trial") == {"median": 0.05, "p95": 0.1}
    assert verdict.drawdowns(both, "a trial") == verdict.drawdowns(both, "a trial")
    assert verdict.drawdowns([Decimal(-1000)], "x") == {"median": 0.1, "p95": 0.1}


@OFF
def test_folds_that_cannot_be_run_are_a_fault_with_their_reason_and_the_rest_stand() -> None:
    def short() -> Pooled:
        raise ValueError("no 5 whole years of history to fold")

    done = verdict.judge(CELL, EDGE, ISF, NOISE, {}, 6, (), short)
    assert done["rungs"]["folds"] == [
        "FAULT",
        "the folds could not be run: no 5 whole years of history to fold",
    ]
    assert done["rungs"]["first"][0] == "PASS" and done["answer"] == "FAULT"


@OFF
def test_a_market_with_a_missing_day_is_a_fault_in_its_own_words() -> None:
    #: the blind re-review (R-RUNNER-188): the market rung's FAULT was given the first rung's words
    held = [*NOISE[:2000], *NOISE[2001:]]
    answer, why = verdict.judge(CELL, EDGE, ISF, held, {}, 6, (), lambda: verdict.pool([], {}))[
        "rungs"
    ]["market"]
    assert answer == "FAULT" and f"has no bar on {NOISE[2000].day}" in why, why


@OFF
def test_a_cell_is_judged_among_its_rules_own_lines_else_charged_the_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pooled = verdict.pool([(CELL, EDGE)], {})
    (among,) = deflated.judge([verdict.ready(CELL, EDGE, {}, ())], 4)  #: L18: the rule's own lines
    for eased in (False, True):
        monkeypatch.setattr(verdict, "EASED", eased)
        alone, lines = (
            verdict.judge(CELL, EDGE, ISF, NOISE, {}, 63920, (), lambda: pooled, among=one)
            for one in (None, among)
        )
        assert "63920 trials" in alone["rungs"]["luck"][1], "no lines given: the count"
        assert "times 5 trials" in lines["rungs"]["luck"][1], "judged among its lines"


@pytest.mark.parametrize("path", ["whole", "sour folds", "missing market day"])
@OFF
def test_every_path_through_the_judge_answers_every_rung_in_its_own_words(path: str) -> None:
    #: the mechanism of R-RUNNER-193: four fixes in a row were each a path through `judge` no test
    #: walked; on every path each rung answers, and no non-PASS rung borrows another's reason
    held = [*NOISE[:2000], *NOISE[2001:]] if path == "missing market day" else NOISE
    pooled = verdict.pool([(CELL, EDGE)], {})
    if path == "sour folds":
        pooled = replace(pooled, years=(replace(pooled.years[0], answer=Answer.FAIL),))
    rungs = verdict.judge(CELL, EDGE, ISF, held, {}, 6, (), lambda: pooled)["rungs"]
    assert {"first", "folds", "market", "stress"} <= set(rungs)
    whys = {name: why for name, (_, why) in rungs.items()}
    assert all(whys.values()) and len(set(whys.values())) == len(whys), whys


@pytest.mark.parametrize("eased", [False, True])
def test_the_scorecard_grades_every_rung_after_a_soft_fail_and_stops_at_a_negative_mean(
    monkeypatch: pytest.MonkeyPatch, eased: bool
) -> None:
    ran: list[int] = []

    def share(*_: object) -> float:
        ran.append(1)
        return 0.0

    monkeypatch.setattr(shuffle, "share", share)
    monkeypatch.setattr(verdict, "EASED", eased)
    first = verdict.ready(CELL, EDGE, {}, ())
    pooled = verdict.pool([(CELL, EDGE)], {})

    def judged(t: str) -> dict[str, Any]:
        failed = replace(first, answer=Answer.FAIL, t=Decimal(t))
        return verdict.judge(CELL, EDGE, ISF, NOISE, {}, 6, (), lambda: pooled, failed)

    soft = judged("1.5")  #: failing only the confidence interval, its mean above nothing
    assert soft["rungs"]["first"][0] == "FAIL" and soft["answer"] == "FAIL"
    assert bool(ran) is eased and ("not run" in soft["rungs"]["shuffle"][1]) is not eased
    assert soft["rungs"]["stress"][0] == "PASS" and soft["every"] is False
    assert soft["rungs"]["deflated"][0] == ("WEAK" if eased else "DOUBT"), "DOUBT is graded WEAK"
    hard = judged("-0.5")  #: a negative mean: stops at once
    assert (list(hard["rungs"]) == ["first"]) is eased and hard["answer"] == "FAIL"


@pytest.mark.parametrize("eased", [False, True])
def test_a_basket_at_one_standard_error_incubates_and_over_the_stress_limit_never_does(
    monkeypatch: pytest.MonkeyPatch, eased: bool
) -> None:
    monkeypatch.setattr(verdict, "EASED", eased)
    first = verdict.ready(CELL, EDGE, {}, ())

    def said(t: str, ladders: Answer, stress: Answer = Answer.PASS) -> str:
        return verdict.basket_answer(replace(first, answer=ladders, t=Decimal(t)), stress)

    assert said("0.9", Answer.FAIL) == "FAIL"
    assert said("1.0", Answer.FAIL) == ("INCUBATE" if eased else "FAIL")
    assert said("2.1", Answer.PASS) == "PASS"  #: the ladder's own answer, never demoted
    for over in (Answer.FAIL, Answer.THIN, Answer.FAULT):  #: stress over its limit or untested
        assert said("1.5", Answer.FAIL, over) == "FAIL"
    assert said("1.5", Answer.THIN) == "THIN"  #: too few trades says nothing


@OFF
def test_one_weak_soft_rung_no_longer_kills_a_cell_and_one_failed_hard_gate_always_does(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    passes = dict.fromkeys(verdict.HARD + verdict.SOFT, Answer.PASS)
    said = verdict.one_answer
    assert said(passes | {"regime": Answer.DOUBT, "market": Answer.THIN}, 1.0) == "PASS"
    assert said(passes | dict.fromkeys(verdict.SOFT, Answer.DOUBT), 1.0) == "FAIL", "over MAX_WEAK"
    for soft in verdict.SOFT:
        assert said(passes | {soft: Answer.FAIL}, 1.0) == "FAIL", soft
    for gate in verdict.HARD:
        assert said(passes | {gate: Answer.FAIL}, 1.0) == "FAIL", gate
    assert said(passes | {"first": Answer.THIN}, 1.0) == "THIN" and said(passes, 2.5) == "STOP"
    assert said({name: a for name, a in passes.items() if name != "shuffle"}, 1.0) is None
    assert said(passes | {"stress": Answer.FAULT}, 1.0) == "FAULT", "a fault in the test"
    assert said(passes | {"stress": Answer.FAULT, "folds": Answer.THIN}, 1.0) == "THIN"
    weak = dict.fromkeys(verdict.HARD + verdict.SOFT + ("luck",), (Answer.PASS, "")) | {
        "regime": (Answer.DOUBT, ""),
        "luck": (Answer.FAIL, ""),
    }
    assert verdict.gates(weak | {"regimes": (Answer.THIN, "")}), "the declared regime rung: soft"
    assert verdict.gates(weak | {"fit": (Answer.DOUBT, "")}), "fit with the book (#2233): soft"
    assert not verdict.gates(weak | {"fit": (Answer.FAIL, "")}), "its FAIL still holds a cell"
    for no in ({"regimes": weak["luck"]}, {"stress": weak["luck"]}, {"costs": weak["regime"]}):
        assert not verdict.gates(weak | no), "a soft FAIL, or any hard rung short, holds a cell"
    monkeypatch.setattr(shuffle, "share", lambda *_: 0.0)  #: a WEAK market never skips it
    ran = verdict.shuffled(
        CELL, EDGE, ROOM, {}, weak | {"market": weak["regime"], "yearly": weak["first"]}, ()
    )
    assert ran is not None and ran[0] is Answer.PASS, "no lowest of NAMED before the shuffle"
    stopped = weak | {"folds": (Answer.FAULT, ""), "stress": (Answer.FAIL, "")}
    assert verdict._stopped(0, stopped, {})["answer"] == "FAULT", "a FAULT is no FAIL"
    monkeypatch.setattr(verdict, "one_answer", lambda *_: "WIRED")
    assert _judge()["answer"] == "WIRED", "judge answers by the one rule"
