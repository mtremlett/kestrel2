"""The ladder's sets trade a line only on the days it was a member of its list."""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from desk.lines import LINES, Line
from lab import (
    history_bars,
    intraday,
    ladder,
    ladder_sets,
    members,
    rulebook,
    scalping,
    trials,
    variants,
    verdict,
)
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


def _door(
    home: Path, answers: list[str], monkeypatch: pytest.MonkeyPatch, argv: tuple[str, ...] = ()
) -> int:
    """The command, given argv, after set EPON's cells each hold one folds answer."""
    rows = [
        {"cell": ["r", f"L{i}"], "rungs": {"folds": [a, "no years"]}} for i, a in enumerate(answers)
    ]
    (home / "ladder").mkdir(parents=True)
    (home / "ladder" / "EPON.jsonl").write_text("".join(json.dumps(r) + chr(10) for r in rows))
    monkeypatch.setattr(ladder_sets, "main", lambda *_: 0)
    return ladder.door({"KESTREL2_DATA": str(home)}, argv)


def test_a_set_whose_cells_all_fault_ends_red_naming_the_rung_and_real_fails_end_green(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    assert _door(tmp_path / "a", ["FAULT"] * 3, monkeypatch) == 1
    assert "FAULT: 3 of 3 cells at rung folds: no years" in capsys.readouterr().out
    assert _door(tmp_path / "b", ["FAIL"] * 3, monkeypatch) == 0
    assert "FAULT" not in capsys.readouterr().out
    for i, own in enumerate(("intraday", "scalping")):  #: a set with its own table: EPON unread
        assert _door(tmp_path / f"c{i}", ["FAULT"] * 3, monkeypatch, (own,)) == 0
        assert "FAULT" not in capsys.readouterr().out


def test_a_basket_row_carries_the_market_its_lines_venue_is_set_beside(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from test_lab_ladder import EDGE, ISF, VUSA, _door

    from lab import basket, rung_retail
    from lab.cell import Cell

    seen: list[rung_retail.Against | None] = []
    row = basket.row

    def spy(*a: Any) -> Any:
        seen.append(a[5])
        return row(*a)

    monkeypatch.setattr(basket, "row", spy)
    todo = [Cell("breakout_20_10", VUSA, START, END)]
    door = _door({VUSA: EDGE, ISF: EDGE})
    ladder_sets.baskets(door, {}, todo, ["breakout_20_10"], ladder_sets.EPON)
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


def test_the_weather_is_written_beside_the_set_naming_its_three_layers(tmp_path: Path) -> None:
    import math
    from datetime import timedelta
    from decimal import Decimal

    from desk.store import Bar

    series = []
    for n in range(1500):
        wave = 0.1 * math.sin(n / 37) + (0.04 + 0.03 * math.sin(n / 40)) * math.sin(n / 3)
        close = Decimal(str(round(100 * math.exp(0.0004 * n + wave), 4)))
        series.append(Bar(date(2015, 1, 1) + timedelta(days=n), close, close, close, close, 1))
    held = [Line("AAA", "US", "USD", 1), Line("BBB", "US", "USD", 1)]
    said = ladder_sets.weather_line(tmp_path, lambda _: series, held)
    layers = json.loads((tmp_path / "ladder" / "sets" / "weather.json").read_text())["layers"]
    assert [x["layer"] for x in layers] == ["volatility", "drawdown", "breadth"]
    assert all(x["worst_fold"] and x["trend_worst_fold"] and x["trials"] == 3 for x in layers)
    assert said.startswith("weather: volatility ") and said.endswith("; 3 trials")
    assert said.count("against trend's") == 3


def test_the_door_takes_intraday_and_variants_and_refuses_an_unknown_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(history_bars, "pounds", lambda _: {})
    monkeypatch.setattr(history_bars, "lines", lambda _: ())
    monkeypatch.setattr(intraday, "judge_set", lambda *_: "SET INTRADAY: stub")
    env = {"KESTREL2_DATA": str(tmp_path)}
    assert ladder_sets.main(env, ["intraday"]) == 0
    assert "SET INTRADAY: stub" in capsys.readouterr().out
    monkeypatch.setattr(scalping, "judge_set", lambda *_: "SET SCALP: stub")
    assert ladder_sets.main(env, ["scalping"]) == 0
    assert "SET SCALP: stub" in capsys.readouterr().out
    made = variants.family(rulebook.specs())  #: every ranged row's variants, each a trial
    assert len(made) > 12 and len({v.spec.name for v in made}) == len(made)
    for _ in range(2):  #: entered again, counted once
        assert ladder.door(env, ["variants"]) == 0  #: VAR's own results, never EPON's
        said = capsys.readouterr().out
        assert f"SET VAR: {len(made)} variants entered, {len(made)} trials" in said
    register = tmp_path / "ladder" / "VAR.trials.jsonl"
    assert trials.count(register, ladder_sets.VAR.question) == len(made)
    with pytest.raises(SystemExit, match="intraday"):
        ladder_sets.main(env, ["nonsense"])


def test_the_pooled_set_refuses_input_gaps_and_a_set_over_one_percent_fault_is_withheld(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from test_lab_ladder import AAPL, EDGE, ISF, NOISE, SPY, VUSA, _door

    from lab import ladder_pool
    from lab.cell import Cell

    ran: list[object] = []
    monkeypatch.setattr(ladder_pool, "run", lambda *a: ran.append(a))  #: the pool never begun
    rule = ["trend_50_200"]
    holed = _door({VUSA: EDGE, ISF: NOISE[:4] + NOISE[5:]})  #: ISF lacks a session (L20)
    with pytest.raises(ValueError, match="refuses to start, first ISF has no bar on 2010-01-05"):
        ladder_sets.epon(
            tmp_path, holed, {}, [VUSA], rules=rule, go=ladder_sets._pooled(lambda: holed)
        )
    assert not ran and not (tmp_path / "ladder").exists()
    dollar, todo = _door({AAPL: EDGE, SPY: NOISE}), [Cell(rule[0], AAPL, START, END)]
    pounds = {bar.day: Decimal("0.8") for bar in EDGE if bar != EDGE[50]}  #: a pound day missing
    ladder_sets._pooled(lambda: dollar)(tmp_path, dollar, pounds, todo)
    assert ran  #: its cell's named gap (`ladder.preflight`), never a refused set
    monkeypatch.setattr(ladder_pool, "run", lambda *a: ladder.run(a[0], a[1](), *a[2:]))
    whole = _door({VUSA: EDGE, ISF: NOISE})
    said = ladder_sets.epon(
        tmp_path, whole, {}, [VUSA, ISF], rules=rule, go=ladder_sets._pooled(lambda: whole)
    )
    assert "NOT PUBLISHED: " in said
    assert "## NOT PUBLISHED" in (tmp_path / "ladder" / "sets" / "EPON.md").read_text()
