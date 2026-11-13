"""The ladder's batch service: many cells run in turn, a bad one recorded and the rest carried
on, and a restart taking up where the last run stopped, never running a finished cell again."""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from desk import strategy
from desk.store import Bar
from lab import batch, cell
from lab.batch import Failed
from lab.cell import Cell, Record, Trade

START = date(2020, 1, 1)
SHAPE = [10] * 20 + [10.4, 11, 11, 9.4, 9.4]  #: breakout_20_10 buys on bar 21, sells on bar 23
BARS = tuple(
    Bar(START + timedelta(n), p, p + Decimal("0.5"), p - Decimal("0.5"), p, 1)
    for n, p in enumerate(Decimal(str(value)) for value in SHAPE)
)
CELLS = tuple(Cell(name, "SPY", START, START + timedelta(24)) for name in strategy.STRATEGIES)
HELD = Cell("breakout_20_10", "SPY", START, START + timedelta(22))  #: still held at its end
EMPTY = Cell("breakout_20_10", "SPY", START + timedelta(30), START + timedelta(40))
UNREAD = Cell("breakout_20_10", "QQQ", START, START + timedelta(24))  #: its bars cannot be read


def _reader(read: list[str], stop_at: int = 0) -> Callable[[str], Sequence[Bar]]:
    """SPY's bars, each read noted; a stop (as by Ctrl-C) on read number stop_at."""

    def bars(symbol: str) -> Sequence[Bar]:
        read.append(symbol)
        if len(read) == stop_at:
            raise KeyboardInterrupt
        return {"SPY": BARS}[symbol]

    return bars


def _lines(journal: Path) -> list[object]:
    return [json.loads(line) for line in journal.read_bytes().splitlines()]


def test_every_cell_is_run_in_order_and_kept(tmp_path: Path) -> None:
    journal, read = tmp_path / "journal", list[str]()
    cells = (*CELLS, HELD)
    outcomes = batch.run(cells, _reader(read), journal)
    assert outcomes == tuple(cell.run(c, BARS) for c in cells)
    assert cell.run(HELD, BARS).trades == (Trade(START + timedelta(21), None),)
    assert len(_lines(journal)) == len(cells) == len(read)
    assert batch.run(cells[::-1], _reader(read), journal) == outcomes[::-1]
    assert len(read) == len(cells), "a finished cell was run again"


def test_a_bad_cell_is_recorded_and_the_rest_carry_on(tmp_path: Path) -> None:
    journal, read = tmp_path / "journal", list[str]()
    cells = (CELLS[0], EMPTY, UNREAD, CELLS[1])
    outcomes = batch.run(cells, _reader(read), journal)
    assert outcomes[::3] == (cell.run(CELLS[0], BARS), cell.run(CELLS[1], BARS))
    assert outcomes[1] == Failed(EMPTY, cell.LOADED, f"ValueError: {_raised(EMPTY)}")
    assert outcomes[2] == Failed(UNREAD, cell.LOADED, "KeyError: 'QQQ'")
    assert batch.run(cells, _reader(read), journal) == outcomes
    assert read[len(cells) :] == ["SPY", "QQQ"], "a failed cell is run again, the rest are not"


def _raised(bad: Cell) -> str:
    with pytest.raises(ValueError) as raised:
        cell.run(bad, BARS)
    return str(raised.value)


def test_a_restart_takes_up_where_the_last_run_stopped(tmp_path: Path) -> None:
    journal, read = tmp_path / "journal", list[str]()
    with pytest.raises(KeyboardInterrupt):
        batch.run(CELLS, _reader(read, stop_at=3), journal)
    assert len(_lines(journal)) == 2
    with journal.open("ab") as out:
        out.write(b'{"cell": ["breakout_20_10", "SP')  # a line a stop cut short
    read.clear()
    assert batch.run(CELLS, _reader(read), journal) == batch.run(CELLS, _reader([]), tmp_path / "j")
    assert len(read) == len(CELLS) - 2
    assert len(_lines(journal)) == len(CELLS)


def test_only_this_codes_outcomes_count_and_changed_code_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    journal, read = tmp_path / "journal", list[str]()
    batch.run(CELLS, _reader(read), journal)
    monkeypatch.setattr(cell, "code_version", lambda: "other code")
    with pytest.raises(RuntimeError, match="changed since this process loaded it"):
        batch.run(CELLS, _reader(read), journal)
    monkeypatch.setattr(cell, "LOADED", "other code")
    again = batch.run(CELLS, _reader(read), journal)
    assert [o.key.code for o in again if isinstance(o, Record)] == ["other code"] * len(CELLS)
    assert len(read) == 2 * len(CELLS)
