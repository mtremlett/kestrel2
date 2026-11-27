"""simcity_faults: the matrix names every class and moment; its seven built cells (the Friday
blip, 1100-1102, hang-up) keep their promises; a planted resend or kill turns one red."""

from __future__ import annotations

from contextlib import suppress
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from desk import simcity_faults as faults
from desk.broker import Crash, Disconnected
from desk.lines import Line
from desk.orders import Order, Settings
from desk.store import Bar

A, MON = Line("A", "LSE", "GBP", 1), date(2025, 11, 10)
BAR = Bar(MON, Decimal(50), Decimal(51), Decimal(49), Decimal(51), 1)
ORDER = Order("o-1", A, 10, *map(Decimal, (50, 1, 45)))


def _run(cell: faults.Cell, root: Path, plant: str = "") -> list[str]:
    broker = faults.pretend(cell, {A: (BAR,)})
    broker.open(MON)
    if plant == "resend":
        broker.report = lambda _: None  # type: ignore[method-assign,assignment]
    if plant == "kill":
        place = broker.place

        def boom(order: Order) -> object:
            with suppress(Crash, Disconnected):
                place(order)
            raise RuntimeError("2157")

        broker.place = boom  # type: ignore[method-assign,assignment]
    return faults.run(cell, root, broker, ORDER, Settings(Decimal(10_000)))


def test_the_table_names_every_class_and_moment_and_counts_what_is_not_built() -> None:
    for name in ("1100", "1101", "1102", "2110", "2103", "2157", "2158", "201", "202", "10147"):
        assert name in faults.CLASSES
    assert {"100", "162", "hang-up"} <= set(faults.CLASSES) and len(faults.MOMENTS) == 5
    assert len(faults.CELLS) == len(faults.CLASSES) * 5 and set(faults.BUILT) <= set(faults.CELLS)
    assert len(faults.BUILT) == 7 and "7 of 325 cells built" in faults.summary()
    assert f"{len(faults.BUILT)} of {len(faults.CELLS)} cells built" in faults.summary()
    with pytest.raises(NotImplementedError):
        faults.run(("201", "before transmit"), Path(), None, ORDER, None)  # type: ignore[arg-type]


@pytest.mark.parametrize("cell", sorted(faults.BUILT))
def test_a_built_cell_keeps_its_promises_and_a_planted_resend_or_kill_turns_it_red(
    tmp_path: Path, cell: faults.Cell
) -> None:
    assert _run(cell, tmp_path / "ok") == []
    assert faults.PROMISES[0] in _run(cell, tmp_path / "resend", "resend")
    assert faults.PROMISES[3] in _run(cell, tmp_path / "kill", "kill")[0]
