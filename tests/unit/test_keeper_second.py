"""The keeper and the second source: its bars fill the archive's holes, and a parked
yardstick is a FIRST-LIGHT FAULT, never silent."""

from __future__ import annotations

from dataclasses import replace
from datetime import date
from decimal import Decimal
from pathlib import Path

from test_keeper import MON, UK, _at, _bars

from desk import keeper
from desk.lines import YARDSTICK, Line
from desk.store import Bar

MATE = replace(UK, symbol="VUSA")  # another London line, clean


def _daily(hole: bool, spike: bool) -> keeper.Ask[date, tuple[Bar, ...]]:
    def ask(line: Line, day: date) -> tuple[Bar, ...]:
        held = list(_bars(line, day))
        if line == YARDSTICK and hole:
            del held[-3]
        if line == YARDSTICK and spike:
            odd = held[-3]
            held[-3] = replace(
                odd, **{p: getattr(odd, p) * Decimal("1.7") for p in "open high low close".split()}
            )
        return tuple(held)

    return ask


def test_the_second_sources_bars_fill_a_hole_and_the_line_is_not_parked(tmp_path: Path) -> None:
    lines = (YARDSTICK, MATE)
    second = lambda line, day: _bars(line, day)  # noqa: E731
    keeper.keep(tmp_path, _at(6), lines, _daily(True, False), second=second)
    held, parked = keeper.saved(tmp_path, MON, lines)
    assert (parked, held[YARDSTICK]) == (frozenset(), _bars(YARDSTICK, MON))


def test_a_parked_yardstick_is_a_first_light_fault_naming_why(tmp_path: Path) -> None:
    said, missed = keeper.keep(tmp_path, _at(6), (YARDSTICK, MATE), _daily(False, True))
    assert len(missed) == 1 and "FIRST-LIGHT FAULT: the yardstick VUAG is parked: " in missed[0]
    assert "moved from" in missed[0] and len(said) == 1
