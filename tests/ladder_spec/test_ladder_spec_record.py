"""What the ladder counts and keeps, by its spec (the docstring of `lab/ladder.py`): every
gating rung in the one verdict, one trial a cell with its rule's code in its name, what made
each answer, the author's figure through the folds, the kept rates, a step of units refused
and the resampled drawdowns.

The check does not run this folder. Each test here is the spec's, written before the code:
it fails until the ladder is built as written, and is never set aside to make it pass.
"""

from __future__ import annotations

import re
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from ladder_worlds import BELL, EDGE, EIGHT, RATE, RULE, SIXTEEN, judged, world

from desk import venues
from desk.command import POUND
from desk.lines import LINES, Line
from desk.store import Bar
from lab import deflated, ladder, reproduce
from lab.cell import Cell
from lab.published import Case
from lab.reproduce import Figure, Fill, Hand, Measure, Stated
from lab.rung import Answer

GATES = {"first", "luck", "deflated", "yearly", "folds", "market", "shuffle"}
MADE = {"commit", "code", "rule", "data", "market", "rates"}


def test_one_verdict_over_every_gating_rung_and_one_trial_a_cell(tmp_path: Path) -> None:
    assert set(deflated.NAMED) == GATES, "the shuffle gates with the six before it (G1)"
    rows = judged(tmp_path, world(BELL, 1))
    for row in rows:
        assert set(row["rungs"]) >= GATES and row["trials"] == len(SIXTEEN), "a fold is no trial"
        assert row["answer"] == min(Answer[row["rungs"][gate][0]] for gate in GATES).name
        assert row["answer"] == "FAIL"
    #: a trial's name carries the hash of its rule's code: the same on every line of the
    #: rule, another for another rule, and the one each line says made it (M4)
    here, there, other = (
        ladder.names(Cell(rule, line, ladder.START, ladder.END))
        for rule, line in ((RULE, EIGHT[0]), (RULE, EIGHT[1]), ("trend_50_200", EIGHT[0]))
    )
    assert len(here) == 1 and (code := re.search(r"\b[0-9a-f]{12}\b", here[0])) is not None
    assert code[0] in there[0] and code[0] not in other[0]
    for row in rows:
        made = row["made"]
        assert set(made) == MADE and all(re.fullmatch(r"[0-9a-f]{40,64}", v) for v in made.values())
        assert len(made["commit"]) == 40 and made["rule"].startswith(code[0])
    assert len({row["made"]["data"] for row in rows}) == len(rows), "each line's own bars"
    assert len({tuple(row["made"][k] for k in sorted(MADE - {"data"})) for row in rows}) == 1


def test_a_rule_behind_its_authors_figure_is_judged_on_every_rung_the_folds_too(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    #: an author's test planted on a market of its own: two trades, bought and sold at the
    #: close, +72.7% and -28%; the code makes it again, so it stands behind every verdict
    market = next(line for line in LINES if line.symbol == "3LGO")
    days = venues.sessions("LSE", date(2020, 1, 2), date(2020, 2, 19))
    closes = tuple(Decimal(c) for c in (*[10] * 20, 11, *[20] * 10, 19, 25, 18, 18))
    printed = Case("", closes, ()).bars()
    bars = tuple(replace(bar, day=day) for bar, day in zip(printed, days, strict=True))
    stated = (
        Stated(Measure.TRADES, Decimal(2), Decimal(0)),
        Stated(Measure.MEAN_GAIN, Decimal("22.36"), Decimal("0.01")),
    )
    source = (RULE, "a planted author", market, days[0], days[-1])
    monkeypatch.setattr(reproduce, "FIGURES", (Figure(*source, Fill.CLOSE, stated, Hand.AUTHOR),))
    for row in judged(tmp_path, world(EDGE, 1) | {market: bars}):
        answer, why = row["rungs"]["reproduce"]
        assert answer == "PASS" and "a planted author" in why
        assert "folds" not in row["unrun"], "the folds take the author's result with the rest (M2)"
        assert row["rungs"]["folds"][0] == row["answer"] == "PASS"


def test_the_rates_are_one_kept_table_never_asked_for_twice(tmp_path: Path) -> None:
    day, asked = date(2020, 1, 6), []

    def ask(line: Line, before: date) -> list[Bar]:
        asked.append((line, before))
        closes = [(day, Decimal("1.25")), (day + timedelta(1), Decimal("1.6"))]
        return [Bar(when, close, close, close, close, 0) for when, close in closes]

    def gone(line: Line, before: date) -> list[Bar]:
        raise AssertionError(f"{line.symbol} before {before}: asked for again, and it is kept")

    rates: Any = ladder.rates  #: the door as the spec gives it (M5): the data home, the archive
    first = rates(tmp_path, ask)
    assert asked == [(POUND, ladder.END + timedelta(1))] and any((tmp_path / "ladder").iterdir())
    #: a day's rate is one over the pound's last close before it, and never a later one
    assert (first[day + timedelta(1)], first[day + timedelta(2)]) == (RATE, Decimal("0.625"))
    assert day not in first and rates(tmp_path, gone) == first


def test_a_step_of_units_is_never_judged(tmp_path: Path) -> None:
    #: a London line of a dollar fund, its first 3,000 days in dollars and the rest in
    #: pounds: the close falls by the day's rate overnight, well under the store's jump
    book, line, at = world(BELL, 1), EIGHT[0], 3000
    dollars = tuple(
        Bar(bar.day, bar.open / RATE, bar.high / RATE, bar.low / RATE, bar.close / RATE, 1)
        for bar in book[line][:at]
    )
    stepped, *others = judged(tmp_path, book | {line: (*dollars, *book[line][at:])})
    assert "answer" not in stepped and book[line][at].day.isoformat() in stepped["error"]
    assert all(row["answer"] == "FAIL" for row in others), "the lines beside it are judged"


def test_the_drawdowns_resampled_are_kept_and_made_the_same_again(tmp_path: Path) -> None:
    first, again = (judged(tmp_path / home, world(BELL, 1)) for home in ("first", "again"))
    for row in first:
        #: parts of the capital: the deepest fall of a middling draw, and of one in twenty
        fall = row["drawdown"]
        assert set(fall) == {"median", "p95"} and 0 < fall["median"] <= fall["p95"] < 1
    assert [row["drawdown"] for row in first] == [row["drawdown"] for row in again]
