"""The ladder's batch service: many cells run in turn, a bad one recorded and the rest carried
on, and a restart taking up where the last run stopped, never running a finished cell again."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from desk import store, strategy, venues
from desk.lines import LINES, STAMP_DUTY, Line
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
AAPL, NVDA = (next(line for line in LINES if line.symbol == s) for s in ("AAPL", "NVDA"))
CELLS = tuple(Cell(name, AAPL, START, START + timedelta(24)) for name in strategy.STRATEGIES)
HELD = Cell("breakout_20_10", AAPL, START, START + timedelta(22))  #: still held at its end
EMPTY = Cell("breakout_20_10", AAPL, START + timedelta(30), START + timedelta(40))
UNREAD = Cell("breakout_20_10", NVDA, START, START + timedelta(24))  #: its bars cannot be read


def _reader(stop_at: int = 0, aapl: Sequence[Bar] = BARS) -> batch.Bars:
    """AAPL's bars; a stop (as by Ctrl-C) on read number stop_at."""
    read = list[str]()

    def bars(line: Line) -> Sequence[Bar]:
        read.append(line.symbol)
        if len(read) == stop_at:
            raise KeyboardInterrupt
        return {"AAPL": aapl}[line.symbol]

    return bars


@pytest.fixture
def ran(monkeypatch: pytest.MonkeyPatch) -> list[Cell]:
    """Each cell the rule is run on, by a batch or by a test; the real run is kept."""
    ran, real = list[Cell](), cell.run

    def counted(todo: Cell, bars: Sequence[Bar]) -> Record:
        ran.append(todo)
        return real(todo, bars)

    monkeypatch.setattr(cell, "run", counted)
    return ran


def _lines(journal: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in journal.read_bytes().splitlines()]


def test_every_cell_is_run_in_order_and_kept(tmp_path: Path, ran: list[Cell]) -> None:
    journal, cells = tmp_path / "journal", (*CELLS, HELD, CELLS[0])
    outcomes = batch.run(cells, _reader(), journal)
    assert outcomes == tuple(cell.run(c, BARS) for c in cells)
    assert batch.run(cells[::-1], _reader(), journal) == outcomes[::-1]
    assert ran == [*cells[:-1], *cells], "a finished cell was run again"
    assert len(_lines(journal)) == len(cells) - 1
    assert cell.run(HELD, BARS).trades == (Trade(START + timedelta(21), None),)


def test_a_bad_cell_is_recorded_and_the_rest_carry_on(tmp_path: Path) -> None:
    journal, cells = tmp_path / "journal", (CELLS[0], EMPTY, UNREAD, CELLS[1])
    outcomes = batch.run(cells, _reader(), journal)
    assert outcomes[::3] == (cell.run(CELLS[0], BARS), cell.run(CELLS[1], BARS))
    with pytest.raises(ValueError) as raised:
        cell.run(EMPTY, BARS)
    assert outcomes[1] == Failed(EMPTY, cell.LOADED, f"ValueError: {raised.value}")
    assert outcomes[2] == Failed(UNREAD, cell.LOADED, "KeyError: 'NVDA'")
    assert batch.run(cells, _reader(), journal) == outcomes
    assert len(_lines(journal)) == 4, "a failure the journal holds was written again"
    for _ in range(2):  # no bars to read at all: each cell's new failure is written, once
        assert all(isinstance(o, Failed) for o in batch.run(cells, batch.stored(tmp_path), journal))
    assert [row["error"][:17] for row in _lines(journal)[4:]] == ["FileNotFoundError"] * 4
    assert batch.run(cells, _reader(), journal) == outcomes  # the bars back: two records found
    assert _lines(journal)[8:] == _lines(journal)[:4], "a cell's last line is not its outcome"


def test_a_restart_takes_up_where_the_last_run_stopped(tmp_path: Path, ran: list[Cell]) -> None:
    journal = tmp_path / "journal"
    with pytest.raises(KeyboardInterrupt):
        batch.run(CELLS, _reader(stop_at=3), journal)
    assert len(_lines(journal)) == 2
    with journal.open("ab") as out:
        out.write(b'{"cell": ["breakout_20_10", "SP')  # a line a stop cut short
    assert batch.run(CELLS, _reader(), journal) == batch.run(CELLS, _reader(), tmp_path / "j")
    assert ran == [*CELLS, *CELLS], "a cell finished before the stop was run again"
    assert len(_lines(journal)) == len(CELLS)


def test_changed_code_refused_then_rerun(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    journal = tmp_path / "journal"
    batch.run(CELLS, _reader(), journal)
    monkeypatch.setattr(cell, "code_version", lambda: "other code")
    with pytest.raises(RuntimeError, match="changed since this process loaded it"):
        batch.run(CELLS, _reader(), journal)
    monkeypatch.setattr(cell, "LOADED", "other code")
    again = batch.run(CELLS, _reader(), journal)
    assert [o.key.code for o in again if isinstance(o, Record)] == ["other code"] * len(CELLS)
    assert len(_lines(journal)) == 2 * len(CELLS)


def test_only_a_cell_whose_bars_changed_is_run_again(tmp_path: Path, ran: list[Cell]) -> None:
    journal, cells, mended = tmp_path / "journal", (CELLS[0], HELD), list(BARS)
    mended[23] = replace(BARS[23], close=Decimal("9.5"))  # after HELD's end: HELD never reads it
    first = batch.run(cells, _reader(), journal)
    again = batch.run(cells, _reader(aapl=mended), journal)
    assert ran == [*cells, CELLS[0]], "only the cell that read the change is run again"
    assert again == (cell.run(CELLS[0], mended), first[1]) and again[0] != first[0]
    del ran[:]
    assert batch.run(cells, _reader(), journal) == first and ran == []  # the bars back: found
    assert _lines(journal)[-1] == _lines(journal)[0], "a cell's last line is not its outcome"


def test_one_symbol_is_two_companies_each_read_from_its_venues_folder(
    tmp_path: Path, ran: list[Cell]
) -> None:
    day, journal = date(2026, 11, 13), tmp_path / "journal"
    both = (Line("BA", "US", "USD", 1), Line("BA", "LSE", "GBP", 1, STAMP_DUTY))
    for line in both:
        base = Decimal(100 if line.venue == "US" else 200)
        days = venues.sessions(line.venue, day - timedelta(120), day - timedelta(1))
        bars = [
            Bar(d, base + n % 7, base + 8, base - 1, base + n % 7, 9) for n, d in enumerate(days)
        ]
        assert store.prepare(tmp_path / line.venue, {line: bars}, day) == ()
    cells = tuple(Cell("breakout_20_10", line, day - timedelta(120), day) for line in both)
    us, london = batch.run(cells, batch.stored(tmp_path), journal)
    assert us == cell.run(cells[0], store.read(tmp_path / "US", "BA"))
    assert london == cell.run(cells[1], store.read(tmp_path / "LSE", "BA"))
    assert [row["cell"][1:3] for row in _lines(journal)] == [["BA", "US"], ["BA", "LSE"]]
    del ran[:]
    assert batch.run(cells[::-1], batch.stored(tmp_path), journal) == (london, us)
    assert ran == [], "a finished cell was run again"
