"""Variants: a row's ranged settings make every combination, all counted, centre on a plateau."""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest
from test_lab_plateau import FAIL, PASS, PEAK, _AnyRule, _verdict

from lab import cell, plateau, trials, variants
from lab.spec import Spec

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

    register = tmp_path / "trials.jsonl"
    trials.start(register)
    trials.ask(register, "donchian")
    assert variants.enter(register, "donchian", made) == 12 == trials.count(register, "donchian")

    def edge(setting: plateau.Setting) -> str:
        return PEAK if setting == (40, 80) else PASS if setting[1] <= 40 else FAIL

    surface = {v.setting: _verdict(edge(v.setting), v.spec.name) for v in made}
    chosen = variants.centre(ROW, surface)
    assert chosen.setting == (20, 20) and chosen.passed
    assert max(surface, key=lambda s: surface[s].t or 0) == (40, 80), "the best is a lone peak"


@pytest.mark.parametrize("name", [name for name, row in BOOK.items() if "ranges" in row])
def test_every_ranged_row_centres_on_a_plateau(name: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cell, "STRATEGIES", _AnyRule())
    row = Spec.parse({"name": name, **BOOK[name]})
    made = variants.variants(row)
    chosen = variants.centre(row, {v.setting: _verdict(PASS, v.spec.name) for v in made})
    assert chosen.passed, f"{name}: an all-passing surface shows no plateau"
    own = tuple(row.params[place][param] for place, param in row.ranges)
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
        5,
    ],
)
def test_a_range_off_the_row_or_outside_its_block_is_refused(ranges: object) -> None:
    with pytest.raises(ValueError, match="spec donchian"):
        Spec.parse({**ROW_RAW, "ranges": ranges})
    with pytest.raises(ValueError, match="no ranges"):
        variants.variants(Spec.parse({**ROW_RAW, "ranges": {}}))
