"""day - the ISA buys only lines recorded as ones an ISA can hold (R-DATA-12)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from desk import book, day, venues
from desk.broker import Pretend
from desk.halt import Blocker
from desk.lines import Line
from desk.orders import Settings
from desk.store import Bar

DAYS = venues.sessions("LSE", date(2025, 1, 6), date(2025, 2, 28))[:23]
#: Bollinger buys the close of 9 under its lower band
CLOSES = [Decimal(c) for c in [*[10] * 20, 9, 10, 10]]


def test_nothing_is_bought_on_a_line_recorded_as_one_no_isa_can_hold(tmp_path: Path) -> None:
    bars = tuple(Bar(on, c, c + 1, c - 1, c, 1_000_000) for on, c in zip(DAYS, CLOSES, strict=True))
    lines = [Line("A", "LSE", "GBP", 1, isa=False), Line("B", "LSE", "GBP", 1, isa=True)]
    lines.append(Line("C", "LSE", "GBP", 1, retail=False))
    archive = {line: bars[:21] for line in lines}
    broker = Pretend({line: bars for line in lines}, {})
    broker.open(DAYS[21])
    sent = day.trade(
        tmp_path, archive, broker, Settings(Decimal(10_000)), DAYS[21], {"GBP": Decimal(1)}
    )
    assert [(s.order_id[-1], s.blocker) for s in sent] == [
        ("A", Blocker.GATE),
        ("B", None),
        ("C", Blocker.GATE),
    ]
    assert "no stocks and shares ISA can hold" in str(sent[0].reason)
    assert "no UK retail customer may buy" in str(sent[2].reason)
    assert set(book.positions(tmp_path)) == {"B"}


def test_a_strategy_that_met_its_kill_condition_buys_nothing(tmp_path: Path) -> None:
    bars = tuple(Bar(on, c, c + 1, c - 1, c, 1_000_000) for on, c in zip(DAYS, CLOSES, strict=True))
    line = Line("B", "LSE", "GBP", 1)
    room, rates = Settings(Decimal(10_000)), {"GBP": Decimal(1)}

    def morning(root: Path, killed: frozenset[str]) -> tuple[book.Sent, ...]:
        broker = Pretend({line: bars}, {})
        broker.open(DAYS[21])
        return day.trade(root, {line: bars[:21]}, broker, room, DAYS[21], rates, killed=killed)

    name = morning(tmp_path / "a", frozenset())[0].order_id.split("-")[1]
    barred = morning(tmp_path / "b", frozenset({name}))
    assert [(s.blocker, s.filled) for s in barred] == [(Blocker.GATE, 0)]
    assert f"{name} met its kill condition" in str(barred[0].reason)
    assert not book.positions(tmp_path / "b")


def test_a_line_parked_by_hand_is_not_bought_until_unparked(tmp_path: Path) -> None:
    bars = tuple(Bar(on, c, c + 1, c - 1, c, 1_000_000) for on, c in zip(DAYS, CLOSES, strict=True))
    line = Line("B", "LSE", "GBP", 1)
    (tmp_path / "parked.csv").write_text("symbol,who,why\nB,coordinator,doubtful\n")
    broker = Pretend({line: bars}, {})
    broker.open(DAYS[21])
    args = ({line: bars[:21]}, broker, Settings(Decimal(10_000)), DAYS[21], {"GBP": Decimal(1)})
    sent = day.trade(tmp_path, *args)
    assert [(s.blocker, s.filled) for s in sent] == [(Blocker.GATE, 0)]
    assert "parked by hand: B (coordinator: doubtful)" in str(sent[0].reason)
    (tmp_path / "parked.csv").unlink()
    assert [s.blocker for s in day.trade(tmp_path, *args)] == [None]
