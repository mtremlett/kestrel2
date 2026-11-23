"""Variants: a row's ranged settings make every combination, all counted, centre on a plateau."""

from __future__ import annotations

import ast
import tomllib
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from test_lab_plateau import FAIL, PASS, PEAK, _AnyRule, _verdict

from desk.store import Bar
from desk.strategy import Rule
from lab import cell, plateau, trials, variants
from lab.spec import Spec, SpecRule

BOOK = tomllib.loads((Path(__file__).parents[2] / "lab" / "catalogue.toml").read_text("utf-8"))
ROW_RAW = {"name": "donchian_channel_breakout", **BOOK["donchian_channel_breakout"]}
ROW = Spec.parse(ROW_RAW)


def test_twelve_variants_all_counted_and_the_pick_is_the_plateau_centre(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cell, "STRATEGIES", _AnyRule())
    assert ROW.ranges == {("entry", "n"): (10, 20, 40), ("exit", "n"): (10, 20, 40, 80)}
    made = variants.variants(ROW)
    assert len(made) == 12 and len({v.spec.name for v in made}) == 12
    assert made[0].spec.params["entry"] == {"n": 10} and made[0].spec.params["exit"] == {"n": 10}
    assert made[-1].setting == (40, 80) and ROW.params["entry"] == {"n": 20}
    assert not made[0].spec.ranges
    assert all(variants.find({ROW.name: ROW}, v.spec.name) == v.spec for v in made)
    made_rule = variants.rule({ROW.name: ROW}, made[0].spec.name)  #: a cell runs it bare
    assert made_rule.__module__ == "lab.spec" and made_rule.__name__ == "SpecRule"
    rising = [Bar(date(2026, 1, 1 + k), *(Decimal(k + 1),) * 4, 1) for k in range(15)]

    def said(rule: Rule) -> list[bool]:
        return [rule.step(bar, False) for bar in rising]

    assert said(made_rule()) == said(SpecRule(made[0].spec)) != said(SpecRule(ROW))
    shared = {**ROW_RAW, "ranges": {"entry+exit": {"n": [10, 20]}}}
    assert variants.variants(Spec.parse(shared))[0].spec.params["exit"] == {"n": 10}
    with pytest.raises(ValueError, match="one setting"):  # the places disagree: two settings
        Spec.parse({**shared, "params": {**ROW_RAW["params"], "exit": {"n": 40}}})
    four = {"entry": {"n": 4}, "stop": {"n": 4}}
    box = {"name": "darvas_box", **BOOK["darvas_box"], "params": four}
    with pytest.raises(ValueError, match="case 0 gives"):  # the box's sessions reach its blocks
        Spec.parse(box)
    for stray in (ROW.name, f"{ROW.name}[entry.n=30,exit.n=10]", "nobody[entry.n=10]"):
        with pytest.raises(ValueError, match="no variant"):
            variants.find({ROW.name: ROW}, stray)

    register = tmp_path / "trials.jsonl"
    trials.start(register)
    trials.ask(register, "donchian")
    names = [v.spec.name for v in made]
    assert trials.enter(register, "donchian", names) == 12 == trials.count(register, "donchian")

    def edge(setting: plateau.Setting) -> str:
        return PEAK if setting == (40, 80) else PASS if setting[1] <= 40 else FAIL

    surface = {v.setting: _verdict(edge(v.setting), v.spec.name) for v in made}
    chosen = plateau.choose(list(ROW.ranges.values()), surface)
    assert chosen.setting == (20, 20) and chosen.passed
    assert max(surface, key=lambda s: surface[s].t or 0) == (40, 80), "the best is a lone peak"
    tree = ast.parse(Path(variants.__file__).read_text("utf-8"))  #: the rule book may import it
    read = {
        "." * n.level + (n.module or "") for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)
    }
    read |= {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    lab = {module for module in read if module.startswith(("lab", "."))}
    assert lab == {"lab.spec"}, "variants reaches the rule book back through lab: a cycle (#1608)"


@pytest.mark.parametrize("name", [name for name, row in BOOK.items() if "ranges" in row])
def test_every_ranged_row_centres_on_a_plateau(name: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cell, "STRATEGIES", _AnyRule())
    row = Spec.parse({"name": name, **BOOK[name]})
    made = variants.variants(row)
    chosen = plateau.choose(
        list(row.ranges.values()), {v.setting: _verdict(PASS, v.spec.name) for v in made}
    )
    assert chosen.passed, f"{name}: an all-passing surface shows no plateau"
    own = tuple(row.params[place.split("+")[0]][param] for place, param in row.ranges)
    assert chosen.setting == own, f"{name}: its published setting is not its ranges' centre"


@pytest.mark.parametrize(
    "ranges",
    [
        {"entry": {"x": [10, 20]}},
        {"stop": {"n": [10, 20]}},
        {"entry": {"n": [10, 5000]}},
        {"entry": {"n": [10, 20, 10]}},
        {"entry": {"n": []}},
        {"entry": {"n": 10}},
        {"entry": {"n": [40, 10, 20]}},
        {"bogus": {}},
        {"entry+entry": {"n": [10, 20]}},
        {"entry+stop": {"n": [10, 20]}},
        {"entry": {"n": [10, 20]}, "entry+exit": {"n": [10, 20]}},
        5,
    ],
)
def test_a_range_off_the_row_or_outside_its_block_is_refused(ranges: object) -> None:
    with pytest.raises(ValueError, match="spec donchian"):
        Spec.parse({**ROW_RAW, "ranges": ranges})
    with pytest.raises(ValueError, match="no ranges"):
        variants.variants(Spec.parse({**ROW_RAW, "ranges": {}}))
