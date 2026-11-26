"""The known-answer kit, cases c to f (the 21 Nov plan, R-RUNNER-496; a and b are in
`test_lab_ladder_known_answer.py`): a look-ahead cheat, a cost churner, one lucky year and a
thin line in a full basket, each on fixture data through the real future-blind check or the
real ladder, against one table of the verdicts each must give."""

from __future__ import annotations

import json
import random
from collections.abc import Mapping, Sequence
from decimal import Decimal
from pathlib import Path
from typing import Any, ClassVar

import pytest
import test_lab_spec_blind as blind
from test_lab_ladder import SPY, _door
from test_lab_rung import _bars, _walk

from desk.lines import LINES, Line
from desk.store import Bar
from desk.strategy import CLOSES, Declared, Rule, Timeframe
from lab import ladder, rulebook, shuffle, tape, verdict
from lab.cell import Cell
from lab.published_case import Published, known
from lab.published_epon import EPONYMOUS_PUBLISHED

NAMES = "3LGO 2MU SMGB IITU VHYG 5QQQ ISF VUSA SGLN VUAG EQQQ IB1T AAPL TSLA NVDA AMD".split()
SIXTEEN = [next(line for line in LINES if line.symbol == name) for name in NAMES]
DAYS = 6200  #: 2010 to the end of 2026: the window's last five whole years (2021-25) are folded
LUCKY = 2023  #: case e's one year of profit

#: The table: each case's rungs and the one answer the real ladder must give, on every line.
WANT: dict[str, dict[str, str]] = {
    "d churner": {"first": "FAIL", "costs": "FAIL", "answer": "FAIL"},
    "e lucky year": {"folds": "FAIL", "answer": "FAIL"},
    "f thin line": {"first": "THIN", "folds": "PASS", "answer": "THIN"},
}


class Cheat:
    """Case c: in the market whenever TOMORROW's close is higher than today's."""

    def __init__(self, series: Sequence[Bar]) -> None:
        self._tomorrow = {a.day: b.close for a, b in zip(series, series[1:], strict=False)}

    def step(self, bar: Bar, holding: bool) -> bool:  # noqa: ARG002 - the Rule interface
        return self._tomorrow.get(bar.day, bar.close) > bar.close


class Churner:
    """Case d: in the market every other bar, so a trade every two bars."""

    declared: ClassVar[Declared] = Declared(Timeframe.DAILY, None, LINES, CLOSES)

    def step(self, bar: Bar, holding: bool) -> bool:  # noqa: ARG002 - the Rule interface
        return not holding


def _drift(seed: int) -> tuple[Bar, ...]:
    """A line rising 0.03% a day under a little noise: a tiny gross edge for any holder."""
    rng, closes = random.Random(seed), [100.0]  # noqa: S311 - a repeatable test walk
    while len(closes) < DAYS:
        closes.append(closes[-1] * (1.0003 + rng.gauss(0, 0.002)))
    return _bars(closes)[-2400:]


def _rows(
    home: Path, walks: Mapping[Line, Sequence[Bar]], rule: str = "breakout_20_10"
) -> list[dict[str, Any]]:
    """The real ladder's rows for the rule on each line, beside a market of noise."""
    spy = _walk(99, 0, 0, days=DAYS // 2)
    pounds = {bar.day: Decimal("0.8") for bar in spy}
    todo = [Cell(rule, line, ladder.START, ladder.END) for line in walks]
    ladder.run(home, _door(dict(walks) | {SPY: spy}), pounds, todo)
    path = home / "ladder" / "set1.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines()]


def _said(rows: Sequence[dict[str, Any]], case: str) -> None:
    """Every row judged, none in error, and each gives the table's verdicts."""
    assert rows and not [r for r in rows if "error" in r], rows
    for row in rows:
        got = {k: row["answer"] if k == "answer" else row["rungs"][k][0] for k in WANT[case]}
        assert got == WANT[case], (row["cell"], row["rungs"])


@pytest.fixture(autouse=True)
def _off(monkeypatch: pytest.MonkeyPatch) -> None:
    """A hundred shuffles a run, and the ladder's off answers, not its eased ones."""
    monkeypatch.setattr(shuffle, "share", lambda *_: Decimal("0.01"))
    monkeypatch.setattr(verdict, "EASED", False)


def test_c_a_look_ahead_cheat_is_refused_by_the_future_blind_check() -> None:
    """The check every rule of the book passes (`test_lab_spec_blind.py`) refuses the cheat,
    and every rule the ladder can be handed is one it checks."""
    assert blind._blind(Cheat, blind._bars(), seed=3), "the cheat went unseen"
    assert set(rulebook.rules()) <= set(blind.RULES)


def test_d_a_cost_churner_fails_the_cell_on_its_costs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Planted in the book with its own known answers, so the ladder's door lets it in."""
    book: dict[str, type[Rule]] = {**rulebook.rules(), "churner": Churner}
    monkeypatch.setattr(rulebook, "rules", lambda folder=None: book)  # noqa: ARG005
    case = known("in on bars 0, 2 and 4", [10] * 5, ((0, 1), (2, 3), (4, None)))
    planted = Published("the kit's planted churner", (case,))
    monkeypatch.setitem(EPONYMOUS_PUBLISHED, "churner", planted)
    real = tape.code_of_rule  #: the test module is not under the code's root: keyed by name
    monkeypatch.setattr(tape, "code_of_rule", lambda s: "planted" if s == "churner" else real(s))
    rows = _rows(tmp_path, {line: _drift(n) for n, line in enumerate(SIXTEEN[-4:], 1)}, "churner")
    _said(rows, "d churner")
    #: the gross edge is real and small: positive, a tenth or so of what the broker takes
    assert all("the edge holds to 0.1 times the costs" in r["rungs"]["costs"][1] for r in rows)


def test_e_one_lucky_year_fails_the_folds(tmp_path: Path) -> None:
    """A breakout that loses a little every year but one, and earns its whole profit there."""
    pushes = [0.03 if year == LUCKY else -0.003 for year in range(2010, 2027)]
    walks = {line: _walk(n, *pushes, days=365)[-2400:] for n, line in enumerate(SIXTEEN, 1)}
    rows = _rows(tmp_path, walks)
    _said(rows, "e lucky year")
    assert all("above nothing" in r["rungs"]["first"][1] for r in rows), "the whole is profit"
    assert all(f"folds, {LUCKY}:" not in r["rungs"]["folds"][1] for r in rows)


def test_f_a_line_too_thin_alone_is_judged_on_its_basket_not_faulted(tmp_path: Path) -> None:
    """AMD holds only the last 2,000 days of the edge: too few trades alone, its fifteen
    siblings' years pooled with its own give the folds enough."""
    walks = {line: _walk(n, 0.012, 0.012, days=DAYS // 2)[-2400:] for n, line in enumerate(SIXTEEN)}
    walks[SIXTEEN[-1]] = walks[SIXTEEN[-1]][-2000:]
    thin = _rows(tmp_path, walks)[-1]
    _said([thin], "f thin line")
    assert thin["cell"][1] == "AMD" and "over 16 lines" in thin["rungs"]["folds"][1]
