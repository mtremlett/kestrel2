"""lab.chain: a published set table makes each rule's variants, fixed before any result."""

from __future__ import annotations

import json
import os
from dataclasses import replace
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from lab import chain, history_bars, ladder, ladder_sets, published, rulebook, trials, variants
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


def test_the_centre_of_a_block_is_reported_never_the_best_corner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from test_lab_plateau import _verdict

    spec = BOOK["donchian_channel_breakout"]
    ranged = replace(spec, ranges=chain.ranges(spec))
    monkeypatch.setattr(rulebook, "specs", lambda *_, **__: {spec.name: ranged})
    made = variants.variants(ranged)
    corner = made[0].setting
    firsts = {
        v.spec.name: _verdict("0.2" if v.setting == corner else "0.05", v.spec.name) for v in made
    }
    chosen = chain.centre(spec, firsts)
    assert corner == (13, 13) and chosen.setting == (20, 20) and chosen.passed
    lone = {k: _verdict("-0.5", k) if "=20,exit.n=20" not in k else v for k, v in firsts.items()}
    assert not chain.centre(spec, lone).passed


def test_the_report_names_each_line_and_counts_every_trial(tmp_path: Path) -> None:
    from test_lab_ladder import EDGE, VUSA, _door

    sets = tmp_path / "ladder" / "sets"
    sets.mkdir(parents=True)
    rows = [
        {"rule": "donchian_channel_breakout", "cells": [{"cell": ["d", "VUSA", "LSE", *WINDOW]}]}
    ]
    (sets / "EPON.json").write_text(json.dumps({"rules": rows, "trials": 99}))
    path = chain.report(tmp_path, _door({VUSA: EDGE}), {}, "EPON")
    data = json.loads(path.with_suffix(".json").read_text())
    assert path.name == "EPON-chain.md" and data["trials"] == 99
    assert data["status"] == "PRE-REVIEW" and len(data["rows"]) == 1
    assert "PRE-REVIEW" in path.read_text() and "VUSA" in path.read_text()


def test_the_command_chains_a_new_table_once_and_a_newer_one_again(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from test_lab_ladder import EDGE, VUSA, _door

    sets = tmp_path / "ladder" / "sets"
    sets.mkdir(parents=True)
    rows = [
        {"rule": "donchian_channel_breakout", "cells": [{"cell": ["d", "VUSA", "LSE", *WINDOW]}]}
    ]
    table = sets / "EPON.json"
    table.write_text(json.dumps({"rules": rows, "trials": 99}))
    ranged = {k: replace(v, ranges=chain.ranges(v)) for k, v in BOOK.items()}
    monkeypatch.setattr(rulebook, "specs", lambda *_, **__: ranged)
    ran: list[str] = []

    def chained(*args: Any, **_: Any) -> str:
        ran.append(args[3])
        return ""

    monkeypatch.setattr(chain, "sweep", chained)
    monkeypatch.setattr(history_bars, "reader", lambda _: _door({VUSA: EDGE}))
    monkeypatch.setattr(history_bars, "pounds", lambda _: {})
    env = {"KESTREL2_DATA": str(tmp_path)}
    assert chain.main(env) == 0 and ran == ["EPON"]
    assert "99 trials" in capsys.readouterr().out
    assert chain.main(env) == 0 and ran == ["EPON"] and not capsys.readouterr().out
    later = (sets / "EPON-chain.json").stat().st_mtime + 5
    os.utime(table, (later, later))
    assert chain.main(env) == 0 and ran == ["EPON", "EPON"]
