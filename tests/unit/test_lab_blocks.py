"""The building blocks, known answers on hand-made bars: each fires on exactly the bars its
definition fixes, and not before it has seen enough."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest

from desk.store import Bar
from lab.blocks import BLOCKS, Block, Kind


def _fire(name: str, bars: list[tuple[int, int, int]], holding: bool = False, **params: int) -> str:
    block: Block = BLOCKS[name].make(
        **{k: Decimal(v) if name == "trailing_stop" else v for k, v in params.items()}
    )
    out = ""
    for n, (high, low, close) in enumerate(bars):
        c, h, lo = map(Decimal, (close, high, low))
        bar = Bar(date(2020, 1, 1) + timedelta(n), c, h, lo, c, 1000)
        out += "1" if block.see(bar, holding) else "0"
    return out


FLAT = [(11, 9, 10)] * 3


@pytest.mark.parametrize(
    ("name", "bars", "holding", "params", "answer"),
    [
        ("highest_high", [*FLAT, (12, 10, 12), (13, 11, 13)], False, {"n": 3}, "00011"),
        ("lowest_low", [*FLAT, (9, 7, 8), (8, 7, 8)], False, {"n": 3}, "00010"),
        (
            "close_below_average",
            [(1, 1, 3), (1, 1, 3), (1, 1, 3), (1, 1, 2)],
            False,
            {"n": 3},
            "0001",
        ),
        (
            "close_above_average",
            [(1, 1, 1), (1, 1, 1), (1, 1, 1), (1, 1, 5)],
            False,
            {"n": 3},
            "0001",
        ),
        (
            "trailing_stop",
            [(1, 1, 100), (1, 1, 110), (1, 1, 100), (1, 1, 99)],
            True,
            {"pct": 10},
            "0001",
        ),
        ("trailing_stop", [(1, 1, 1), (1, 1, 1)], False, {"pct": 10}, "00"),
        (
            "close_below_close_ago",
            [(1, 1, 5), (1, 1, 5), (1, 1, 4), (1, 1, 4)],
            False,
            {"n": 2},
            "0011",
        ),
        ("held_bars", FLAT, True, {"n": 2}, "011"),
        ("no_stop", FLAT, True, {}, "000"),
        ("no_filter", FLAT, False, {}, "111"),
    ],
)
def test_block_fires_on_the_bars_its_definition_fixes(
    name: str, bars: list[tuple[int, int, int]], holding: bool, params: dict[str, int], answer: str
) -> None:
    assert _fire(name, bars, holding, **params) == answer


def test_every_block_has_its_kind_and_parameters_in_range() -> None:
    assert {s.kind for s in BLOCKS.values()} == set(Kind)
    assert all(p.low < p.high for s in BLOCKS.values() for p in s.params.values())
