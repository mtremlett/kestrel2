"""A spec as data: Spec.parse refuses each kind of bad row by name, and a SpecRule of
Donchian's entry and exit decides as the desk's own DonchianChannelBreakout does."""

from __future__ import annotations

import copy
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

import pytest

from desk.eponymous_bands import DonchianChannelBreakout
from desk.store import Bar
from lab.spec import Spec, SpecRule, variants

CASE = {"bars": [[11, 9, 10]] * 3 + [[13, 11, 12], [10, 7, 8]], "wants": [0, 0, 0, 1, 0]}
ROW: dict[str, Any] = {
    "name": "donchian3",
    "entry": "highest_high",
    "exit": "lowest_low",
    "stop": "no_stop",
    "filter": "no_filter",
    "params": {"entry": {"n": 3}, "exit": {"n": 3}},
    "source": "Faith, Way of the Turtle",
    "cases": [CASE],
}


def _row(**change: Any) -> dict[str, Any]:
    return {**copy.deepcopy(ROW), **change}


def test_a_good_row_is_a_frozen_spec_holding_its_parameters() -> None:
    spec = Spec.parse(ROW)
    assert (spec.entry, spec.params["entry"]["n"]) == ("highest_high", 3)
    with pytest.raises(AttributeError):
        spec.name = "x"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("row", "why"),
    [
        (_row(entry="moon_phase"), "unknown block"),
        (_row(entry="lowest_low"), "is a exit, not a entry"),
        ({k: v for k, v in ROW.items() if k != "source"}, "missing"),
        (_row(colour="red"), "extra"),
        (_row(params={"entry": {"n": 3}}), "takes parameters"),
        (_row(params={"entry": {"n": 3, "m": 4}, "exit": {"n": 3}}), "takes parameters"),
        (_row(params={"entry": {"n": "3"}, "exit": {"n": 3}}), "not a whole number"),
        (_row(params={"entry": {"n": 3.5}, "exit": {"n": 3}}), "not a int"),
        (_row(params={"entry": {"n": True}, "exit": {"n": 3}}), "not a int"),
        (_row(params={"entry": {"n": 1}, "exit": {"n": 3}}), "outside"),
        (_row(params={"entry": {"n": 3}, "exit": {"n": 3}, "mood": {}}), "params are given"),
        (
            _row(stop="trailing_stop", params={**ROW["params"], "stop": {"pct": "x"}}),
            "not a number",
        ),
        (_row(stop="trailing_stop", params={**ROW["params"], "stop": {"pct": 99}}), "outside"),
        (_row(cases=[]), "no known-answer case"),
        (_row(cases=[{**CASE, "wants": [0, 0, 0, 0, 0]}]), "gives"),
        (_row(cases=[{"bars": [[1, 1, 1]], "wants": []}]), "one wish for each"),
        (_row(cases=[{"bars": [[1, 1]], "wants": [0]}]), "[high, low, close]"),
        (_row(source=" "), "a name and a source"),
    ],
)
def test_parse_refuses_each_bad_row_by_name(row: dict[str, Any], why: str) -> None:
    with pytest.raises(ValueError, match=why.replace("[", r"\[").replace("]", r"\]")):
        Spec.parse(row)


def test_a_decimal_parameter_is_read_from_text_and_the_stop_trails() -> None:
    row = _row(stop="trailing_stop", params={**ROW["params"], "stop": {"pct": "10"}})
    up, down = [[1, 1, 100]] * 3, [[1, 1, 110], [1, 1, 99]]
    row["cases"] = [{"bars": [*up, [12, 1, 101], *down], "wants": [0, 0, 0, 1, 1, 0]}]
    assert Spec.parse(row).params["stop"]["pct"] == Decimal(10)


def test_the_filter_forbids_a_buy() -> None:
    row = _row(filter="close_above_average", params={**ROW["params"], "filter": {"n": 400}})
    row["cases"] = [CASE | {"wants": [0, 0, 0, 0, 0]}]
    Spec.parse(row)


def test_spec_rule_decides_as_the_donchian_rule_on_a_walk() -> None:
    twenty = {"bars": [[11, 9, 10]] * 20 + [[13, 11, 12]], "wants": [0] * 20 + [1]}
    spec = Spec.parse(_row(params={"entry": {"n": 20}, "exit": {"n": 20}}, cases=[twenty]))
    walk = []
    closes = [100 + ((n * 7) % 13) + n // 9 * (-1) ** (n // 30) * 3 for n in range(240)]
    for n, close in enumerate(closes):
        c = Decimal(close)
        walk.append(Bar(date(2020, 1, 1) + timedelta(n), c, c + 1, c - 1, c, 1000))
    mine, theirs, held_a, held_b = SpecRule(spec), DonchianChannelBreakout(), False, False
    seen = []
    for bar in walk:
        held_a, held_b = mine.step(bar, held_a), theirs.step(bar, held_b)
        seen.append((held_a, held_b))
    assert all(a == b for a, b in seen) and any(a for a, _ in seen) and not all(a for a, _ in seen)


def test_variants_are_every_setting_named_as_a_trial_and_refuse_a_bad_one() -> None:
    made = variants(Spec.parse(ROW), "entry", {"n": (3, 4, 5)})
    assert list(made) == [f"donchian3[entry:n={n}]" for n in (3, 4, 5)]
    assert made["donchian3[entry:n=4]"].params["entry"]["n"] == 4
    assert made["donchian3[entry:n=4]"].params["exit"]["n"] == 3
    with pytest.raises(ValueError, match="outside"):
        variants(Spec.parse(ROW), "entry", {"n": (1,)})
    with pytest.raises(ValueError, match="ranges for"):
        variants(Spec.parse(ROW), "entry", {"m": (3,)})
