"""The ladder's unit of work: one strategy on one line over one window. Its trades are the
desk's own decisions, from the grid engine or, where that refuses, from the desk's own; it
cannot see a bar after its window, and its key moves when the code or the bars it read
move, and only then."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from test_strategy import GOLDEN, _jumpy, _walk

from desk import strategy
from desk.store import Bar
from desk.strategy import Action
from lab import cell, grid
from lab.cell import Cell, Trade

START = date(2020, 1, 1)
#: breakout_20_10, worked out in test_strategy: buys on bar 21, sells on bar 23
SHAPE = [10] * 20 + [10.4, 11, 11, 9.4, 9.4]


def _bars(closes: Sequence[float | int]) -> tuple[Bar, ...]:
    half, prices = Decimal("0.5"), [Decimal(str(value)) for value in closes]
    return tuple(Bar(_day(n), p, p + half, p - half, p, 1) for n, p in enumerate(prices))


def _day(n: int) -> date:
    return START + timedelta(n)


def _cell(first: int, last: int, name: str = "breakout_20_10") -> Cell:
    return Cell(name, "SPY", _day(first), _day(last))


def test_a_cell_names_a_real_strategy_a_real_line_and_a_window() -> None:
    with pytest.raises(ValueError, match="no strategy"):
        Cell("best_ever", "SPY", _day(0), _day(9))
    with pytest.raises(ValueError, match="instrument master"):
        Cell("breakout_20_10", "ACME", _day(0), _day(9))
    with pytest.raises(ValueError, match="ends before it starts"):
        _cell(9, 8)
    assert _cell(9, 9).end == _day(9)


def test_its_trades_are_the_desks_own_decisions() -> None:
    bars = _bars(SHAPE * 3)
    for name in strategy.STRATEGIES:
        record = cell.run(_cell(0, len(bars) - 1, name), bars)
        acted = [
            (d.day, d.action)
            for d in strategy.decide({"SPY": bars})
            if d.strategy == name and d.action is not Action.HOLD
        ]
        paired = [(t.bought, Action.BUY) for t in record.trades]
        paired += [(t.sold, Action.SELL) for t in record.trades if t.sold is not None]
        assert sorted(paired) == acted, name
    record = cell.run(_cell(0, len(bars) - 1), bars)
    assert record.trades == tuple(Trade(_day(n), _day(n + 2)) for n in (21, 46, 71))
    with pytest.raises(ValueError, match="oldest first"):
        cell.run(_cell(0, 24), bars[1:2] + bars[:1] + bars[2:])


def test_the_grid_answers_and_the_desk_decides_what_it_refuses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    desk, asked = strategy.decide, [0]

    def counted(bars: Mapping[str, Sequence[Bar]]) -> tuple[strategy.Decision, ...]:
        asked[0] += 1
        return desk(bars)

    monkeypatch.setattr(strategy, "decide", counted)
    for series, kind in (("walk 1", _walk(1, 1200)), ("jumpy 10", _jumpy(10))):
        for name, days in GOLDEN[series].items():
            record = cell.run(Cell(name, "SPY", kind[0].day, kind[-1].day), kind)
            found = [t.bought for t in record.trades]
            found += [t.sold for t in record.trades if t.sold is not None]
            assert sorted(found) == [kind[int(n)].day for n in days.split()], (series, name)
        #: the grid answers every rule on the walk; on the jumpy series a close sits
        #: exactly on a Supertrend band, and that one cell is the desk's own engine's
        assert asked[0] == (series == "jumpy 10"), series
    with pytest.raises(grid.TooClose):
        grid.held("supertrend_10_3", grid.prices(_jumpy(10)))


def test_a_trade_belongs_to_the_window_it_was_bought_in() -> None:
    bars = _bars(SHAPE)
    assert cell.run(_cell(22, 24), bars).trades == ()
    assert cell.run(_cell(21, 22), bars).trades == (Trade(_day(21), None),)
    assert cell.run(_cell(0, 24), bars).trades == (Trade(_day(21), _day(23)),)
    assert cell.run(_cell(21, 22), bars).bars == 2


def test_the_history_before_the_window_warms_the_rule() -> None:
    #: the window holds only the breakout itself; the twenty bars before it are what it beats
    assert cell.run(_cell(21, 24), _bars(SHAPE)).trades == (Trade(_day(21), _day(23)),)


def test_a_bar_after_the_window_changes_nothing() -> None:
    bars = _bars(SHAPE)
    record = cell.run(_cell(0, 21), bars)
    later = bars[:22] + tuple(replace(b, close=b.close * 3) for b in bars[22:])
    assert cell.run(_cell(0, 21), later) == record
    assert cell.run(_cell(0, 21), bars[:22]) == record


def test_the_data_version_moves_with_any_bar_it_read() -> None:
    bars = _bars(SHAPE)
    before = cell.run(_cell(21, 24), bars).key
    one, seven = bars[0], Decimal(7)
    moved = (replace(one, open=seven), replace(one, high=seven), replace(one, low=seven))
    for first in (*moved, replace(one, close=seven)):
        assert cell.run(_cell(21, 24), (first,) + bars[1:]).key.data != before.data, first
    early = (replace(bars[0], volume=2, day=_day(-1)),) + bars[1:]
    assert cell.run(_cell(21, 24), early).key.data != before.data
    assert cell.run(_cell(21, 24), bars[1:]).key.data != before.data
    assert cell.run(_cell(21, 24), bars).key == before
    assert before.code == cell.code_version()


def test_a_window_with_no_bars_is_refused() -> None:
    bars = _bars(SHAPE)
    with pytest.raises(ValueError, match="SPY.*no bars"):
        cell.run(_cell(30, 40), bars)


def _tree(root: Path, files: dict[str, str]) -> None:
    for name, text in files.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_bytes(text.encode())


def test_the_code_version_is_every_desk_and_lab_module_the_cell_reaches(tmp_path: Path) -> None:
    _tree(
        tmp_path,
        {
            "lab/__init__.py": "",
            "lab/cell.py": "from desk.strategy import decide\nimport json\n",
            "desk/__init__.py": "",
            "desk/strategy.py": "from desk import store\n",
            "desk/store.py": "X = 1\n",
            "desk/broker.py": "Y = 1\n",
        },
    )
    first = cell.code_version(tmp_path)
    assert cell.code_version(tmp_path) == first
    _tree(tmp_path, {"desk/broker.py": "Y = 2\n"})
    assert cell.code_version(tmp_path) == first, "a module the cell never reaches"
    _tree(tmp_path, {"desk/store.py": "X = 2\n"})
    reached = cell.code_version(tmp_path)
    assert reached != first, "a module reached through another"
    (tmp_path / "desk/store.py").write_bytes(b"X = 2\r\n")
    assert cell.code_version(tmp_path) == reached, "the same code checked out on Windows"
    for package in ("lab/__init__.py", "desk/__init__.py"):
        _tree(tmp_path, {package: "Z = 1\n"})
        assert cell.code_version(tmp_path) != reached, f"{package} runs on import"
        reached = cell.code_version(tmp_path)


def test_the_code_version_reaches_the_strategies() -> None:
    reached = cell.reached(cell.ROOT)
    assert {"lab/__init__.py", "lab/cell.py", "desk/strategy.py", "desk/store.py"} <= set(reached)
    assert "lab/grid.py" in reached, "a change to the grid engine is a change to every result"
