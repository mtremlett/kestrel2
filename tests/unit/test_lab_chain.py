"""lab.chain: a published set table makes each rule's variants, fixed before any result."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest

from lab import chain, ladder, ladder_sets, published, rulebook, trials
from lab.cell import Cell

BOOK = rulebook.specs()
WINDOW = ["2012-01-03", "2016-12-30"]


def _table() -> dict[str, object]:
    def rule(name: str, symbol: str, venue: str) -> dict[str, object]:
        return {"rule": name, "cells": [{"cell": [name, symbol, venue, *WINDOW]}]}

    return {
        "rules": [
            rule("donchian_channel_breakout", "VUAG", "LSE"),
            rule("keltner_channel_trend", "SPY", "US"),
        ]
    }


def test_ranges_are_the_published_value_and_a_step_either_side() -> None:
    donchian = chain.ranges(BOOK["donchian_channel_breakout"])
    assert donchian == {("entry", "n"): (13, 20, 30), ("exit", "n"): (13, 20, 30)}
    assert chain.ranges(BOOK["keltner_channel_trend"]) == {
        ("entry", "n"): (7, 10, 15),
        ("exit", "n"): (7, 10, 15),
    }


def test_a_parameter_held_to_one_value_is_not_ranged() -> None:
    row = BOOK["donchian_channel_breakout"]
    pinned = replace(row, params={**row.params, "entry": {"n": 2}})  # 2 is the block's low
    assert ("entry", "n") not in chain.ranges(pinned)


def test_cells_are_every_variant_on_every_line(monkeypatch: pytest.MonkeyPatch) -> None:
    ranged = {k: replace(v, ranges=chain.ranges(v)) for k, v in BOOK.items()}
    monkeypatch.setattr(rulebook, "specs", lambda *_, **__: ranged)
    made = chain.cells(_table())
    assert len(made) == 18 and all(isinstance(c, Cell) for c in made)
    assert len({c.strategy for c in made}) == 18
    assert {c.line.symbol for c in made} == {"VUAG", "SPY"}
    assert all(str(c.start) == WINDOW[0] and str(c.end) == WINDOW[1] for c in made)
    assert "donchian_channel_breakout[entry.n=13,exit.n=13]" in {c.strategy for c in made}


def test_a_set_chains_into_its_variants_through_the_tapes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from test_lab_ladder import EDGE, ISF, NOISE, VUSA, _door

    ranged = {k: replace(v, ranges=chain.ranges(v)) for k, v in BOOK.items()}
    monkeypatch.setattr(rulebook, "specs", lambda *_, **__: ranged)
    proven = published.proven.__wrapped__
    #: until `published.proven` knows a variant's base rule (asked of RUNGS), the base is proved
    monkeypatch.setattr(published, "proven", lambda name: proven(name.partition("[")[0]))
    book = _door({VUSA: EDGE, ISF: NOISE})
    own = [Cell("donchian_channel_breakout", VUSA, *map(date.fromisoformat, WINDOW))]
    own += [Cell("keltner_channel_trend", ISF, *map(date.fromisoformat, WINDOW))]
    ladder.run(tmp_path, book, {}, own, plan=ladder_sets.EPON)
    rows = [
        {
            "rule": c.strategy,
            "cells": [{"cell": [c.strategy, c.line.symbol, c.line.venue, *WINDOW]}],
        }
        for c in own
    ]
    sets = tmp_path / "ladder" / "sets"
    sets.mkdir(parents=True)
    (sets / "EPON.json").write_text(json.dumps({"rules": rows}))
    made = chain.cells({"rules": rows})
    said = chain.sweep(tmp_path, book, {}, "EPON", go=ladder.run)
    register = tmp_path / "ladder" / "EPON.trials.jsonl"
    assert trials.count(register, ladder_sets.EPON.question) == len(own) + len(made)
    assert len(list((tmp_path / "ladder" / "tapes").glob("*.tape"))) >= len(made)
    assert f"{len(made)} judged now" in said
    assert "0 judged now" in chain.sweep(tmp_path, book, {}, "EPON", go=ladder.run)
