"""lab.chain: a published set table makes each rule's variants, fixed before any result."""

from __future__ import annotations

from dataclasses import replace

import pytest

from lab import chain, rulebook
from lab.cell import Cell

BOOK = rulebook.specs()
WINDOW = ["2015-01-02", "2024-12-31"]


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
