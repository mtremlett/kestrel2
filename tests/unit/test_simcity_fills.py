"""simcity_fills: the desk's real buys decided again from the bars before them come out the same;
a recorded size, stop or signal that differs fails naming the fill and the field."""

from __future__ import annotations

import sys
from dataclasses import replace
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from desk import book, day
from desk.broker import Fill, Pretend
from desk.lines import YARDSTICK
from desk.orders import Settings
from desk.simcity_fills import Mismatch, replay

sys.path.insert(0, str(Path(__file__).parents[1] / "scenes"))  #: the scenes' rehearsal data
from rehearsal import CLEAN as SCENE  # noqa: E402  the path above comes first
from rehearsal import LINES, SESSIONS

CLEAN = {**SCENE, YARDSTICK: SCENE[LINES[1]]}  #: the yardstick among its lines, as the scenes'
ROOM, RATES = Settings(Decimal(10_000)), {"GBP": Decimal(1), "USD": Decimal("0.79")}


@pytest.fixture(scope="module")
def lived(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[tuple[Fill, ...], dict[str, Decimal]]:
    """The scenes' months lived at the pretend broker: the desk's own ledger and stop levels."""
    root, pretend, began = tmp_path_factory.mktemp("desk"), Pretend(CLEAN, {}), CLEAN_FIRST
    for on in (s for s in SESSIONS if s > began):
        pretend.open(on)
        saved = {
            x: [b for b in bars if b.day <= on] for x, bars in CLEAN.items() if bars[0].day < on
        }
        day.run(root, saved, pretend, ROOM, on, RATES, True)
    return book.fills(root), book.levels(root)


CLEAN_FIRST: date = min(bars[0].day for bars in CLEAN.values())


def test_an_honest_ledger_replays_the_same_and_a_planted_difference_names_fill_and_field(
    lived: tuple[tuple[Fill, ...], dict[str, Decimal]],
) -> None:
    fills, stops = lived
    buys = [i for i, f in enumerate(fills) if f.quantity > 0]
    assert buys and replay(CLEAN, fills, stops, ROOM, RATES) == ()
    i = buys[0]
    size = [*fills[:i], replace(fills[i], quantity=fills[i].quantity + 1), *fills[i + 1 :]]
    first = fills[i].execution_id, "size", str(fills[i].quantity + 1), str(fills[i].quantity)
    assert replay(CLEAN, size, stops, ROOM, RATES)[0] == Mismatch(*first)
    name = f"{fills[i].order_id}-stop"
    low = {**stops, name: stops[name] - 1}
    (wrong,) = replay(CLEAN, fills, low, ROOM, RATES)
    assert (wrong.fill, wrong.field) == (fills[i].execution_id, "stop")
    assert fills[i].execution_id in wrong.words()
