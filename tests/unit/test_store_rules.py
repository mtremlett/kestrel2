"""The store is designed once, not fitted to the data a line at a time (failure pattern 13):
every rule in desk/store.py is pinned by a row below, and a rule added without a row fails."""

from __future__ import annotations

import ast
from collections.abc import Callable, Sequence
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from test_store import DAY, LONG, US, _bars, _scaled

from desk import store
from desk.lines import Line
from desk.store import Bar, Refused


def b_day(at: int) -> date:
    return _bars(US, LONG)[at].day


Make = Callable[
    [list[Bar]], Sequence[Bar] | Refused
]  #: the long run of clean bars in, the archive's answer out
SATURDAY = date(2025, 11, 8)
RULES: dict[str, tuple[Make, Line, str]] = {  # rule site -> (synthetic archive, line, fault seen)
    "_once:1": (lambda b: [*b, replace(b[5], close=b[5].close + 1)], US, "differently; none kept"),
    "_once:2": (lambda b: [*b, b[5]], US, " given 2 times"),
    "_entered:1": (lambda b: b, replace(US, suspended=frozenset({b_day(-5)})), "as suspended"),
    "_entered:2": (lambda b: [*b, replace(b[0], day=SATURDAY)], US, "not a closed session"),
    "_entered:3": (lambda b: [*b[:5], replace(b[5], low=Decimal(0)), *b[6:]], US, "cannot be"),
    "_entered:4": (lambda b: [*b[:5], replace(b[5], high=b[5].low - 1), *b[6:]], US, "outside its"),
    "_entered:5": (lambda b: [*b[:5], replace(b[5], high=b[5].high * 2), *b[6:]], US, "bad print"),
    "_priced:1": (lambda b: [*b[:-8], _scaled(b[-8], Decimal(100)), *b[-7:]], US, "wrong unit"),
    "_priced:2": (
        lambda b: [*b[:-8], replace(_scaled(b[-8], Decimal("1.7")), volume=0), *b[-7:]],
        US,
        "no volume",
    ),
    "_priced:3": (
        lambda b: [*b[:-9], *(_scaled(x, Decimal(100)) for x in b[-9:-7]), *b[-7:]],
        US,
        "unit",
    ),
    "_priced:4": (lambda b: [*b[:-8], _scaled(b[-8], Decimal("1.7")), *b[-7:]], US, "moved from"),
    "_split:1": (
        lambda b: [*(_scaled(x, Decimal(1) / 500) for x in b[:30]), *b[30:]],
        replace(US, splits=frozenset({(b_day(30), Decimal(7))})),
        "split of 7",
    ),
    "_thawed:1": (
        lambda b: [
            *b[:5],
            *(Bar(x.day, b[4].close, b[4].close, b[4].close, b[4].close, 0) for x in b[5:10]),
            *b[10:],
        ],
        US,
        "frozen",
    ),
    "_clean:1": (lambda b: [*b[:5], replace(b[5], volume=-1), *b[6:]], US, "cannot be"),
    "_clean:2": (lambda _: [], US, "every session missing"),
    "_clean:3": (lambda b: [*b[:-6], *b[-5:]], US, "sessions missing"),
    "prepare:1": (lambda _: Refused("HTTP Error 404"), US, "the archive refused it"),
}
KNOBS = {  # every tuning constant of the store, with the value it is judged by
    "JUMP": Decimal("1.6"), "STRETCH": Decimal("0.03"), "RECENT": 60, "BLIP": 20, "FROZEN": 5,
    "FX_STEP": Decimal("0.05"), "FX_FAR": Decimal("0.10"), "RATE_AGE": timedelta(days=7),
    "SPLIT_NEAR": Decimal("0.25"), "HISTORY": "history",
}  # fmt: skip


def _sites() -> set[str]:
    """Every place desk/store.py finds a fault, as function:nth, and every tuning constant."""
    source = (Path(store.__file__)).read_text(encoding="utf-8")
    tree = ast.parse(source)
    found = set()
    for fn in (n for n in tree.body if isinstance(n, ast.FunctionDef)):
        marks = sorted(
            n.lineno
            for n in ast.walk(fn)
            if (isinstance(n, ast.Call) and getattr(n.func, "id", "") == "Fault")
            or (isinstance(n, ast.Return) and isinstance(n.value, ast.JoinedStr))
        )
        found |= {f"{fn.name}:{n}" for n, _ in enumerate(marks, 1)}
    return found


def test_every_rule_in_the_store_is_pinned_by_a_row_that_fires_it() -> None:
    assert _sites() == set(RULES), "a rule in desk/store.py has no row in RULES, or a row no rule"


def test_every_tuning_constant_of_the_store_is_pinned_to_its_value() -> None:
    names = {k for k in vars(store) if k.isupper() and not k.startswith("_")}
    names -= {"COLUMNS", "NO_RATES", "UNRECORDED", "ASTRAY", "FAR"}  # derived or wording
    assert names == set(KNOBS), "a constant was added or dropped without a row in KNOBS"
    assert {k: getattr(store, k) for k in KNOBS} == KNOBS


@pytest.mark.parametrize("site", sorted(RULES))
def test_each_rule_fires_on_its_synthetic_row(tmp_path: Path, site: str) -> None:
    make, line, seen = RULES[site]
    clean = list(_bars(US, LONG))
    answer = make(clean)
    store.prepare(tmp_path, {line: answer}, DAY)
    assert any(seen in f for f in store.faults(tmp_path, US.symbol)), site


@pytest.mark.parametrize("spike", [Decimal("1.7"), Decimal("1.2")], ids=["bad print", "wide day"])
def test_a_wide_day_among_quiet_ones_leaves_no_step_in_its_neighbours(
    tmp_path: Path, spike: Decimal
) -> None:
    """IDTL 17 March 2020 (a move of 0.03%) and VUAG 13-17 March: a day whose high stood far above
    its own prices once made its quiet neighbours 'a split'. A day past JUMP is no bar; a wider
    day than the market's is dropped on entry, so no step is found beside it; EQQQ's true jump
    (the _priced:4 row) is still refused."""
    clean = list(_bars(US, LONG))
    odd = replace(clean[-8], high=clean[-8].close * spike)
    store.prepare(tmp_path, {US: [*clean[:-8], odd, *clean[-7:]]}, DAY)
    assert not any("moved from" in f for f in store.faults(tmp_path, US.symbol))
