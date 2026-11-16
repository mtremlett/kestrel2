"""pnl: the hourly profit and loss, by a hand-worked day."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from desk import bars, book, halt, pnl
from desk.bars import Five
from desk.book import Switch
from desk.broker import Fill
from desk.lines import LINES
from desk.pnl import Mood
from desk.store import Bar

MON, FRI = date(2026, 11, 16), date(2026, 11, 13)
NOW = datetime(2026, 11, 16, 14, tzinfo=UTC)
VUAG, EQQQ, UNHELD = (
    next(line for line in LINES if line.symbol == s) for s in ("VUAG", "EQQQ", "3LGO")
)
#: Held since Friday: 10 VUAG, 4 EQQQ. Bought today: 2 VUAG at 100.50. Friday's closes 100 and
#: 300; the newest bars 101 and 297. Day, by hand: 10 x 1 + 4 x (-3) + 2 x 0.50 = -1.00, less
#: the buy's costs: commission 3.00 (the minimum), spread and slippage 0.1005 each, 3.201 in
#: all = -4.201, told -4.20. The market: 1,000 x +1% = 10.00.
BOUGHT = Fill("e1", "o1", "VUAG", 2, Decimal("100.5"), MON)
TEXT = """📊 Desk 14:00 UK
🔴 Day -£4.20 after costs
🔴 EQQQ 4 sh -1.00%
🟢 VUAG 12 sh +1.00%
🟢 Holding the market: +£10.00 (+1.00%)
✅ trading"""


def _report(last: dict[str, str], mood: Mood = Mood.TRADING) -> str:
    closes = {"VUAG": Decimal(100), "EQQQ": Decimal(300)}
    now = {symbol: Decimal(price) for symbol, price in last.items()}
    held = {"VUAG": 10, "EQQQ": 4}
    return pnl.report(NOW, LINES, held, [BOUGHT], closes, now, {}, Decimal(1000), mood)


def test_the_report_is_the_hand_worked_day_in_a_few_lines() -> None:
    assert _report({"VUAG": "101", "EQQQ": "297"}) == TEXT
    for mood in (Mood.HALTED, Mood.KILLED):
        assert _report({"VUAG": "101", "EQQQ": "297"}, mood).endswith(f"\n{mood.value}")


def test_a_line_with_no_bar_yet_is_told_so_and_never_calm() -> None:
    # VUAG held at its close: 4 x (-3) + 2 x (100 - 100.50) = -13.00, less 3.201 = -16.201.
    assert _report({"EQQQ": "297"}).splitlines()[1:] == [
        "🔴 Day -£16.20 after costs",
        "🔴 EQQQ 4 sh -1.00%",
        "⚪ VUAG 12 sh no bar yet",
        "⚪ Holding the market: no bar yet",
        "✅ trading",
    ]


def _at(clock: str) -> datetime:
    return datetime.fromisoformat(f"2026-11-16T{clock}").replace(tzinfo=UTC)


def test_the_message_is_read_from_the_ledger_the_bars_and_the_halts(tmp_path: Path) -> None:
    rows = [("e0", "o0", "VUAG", 10, "99", FRI), ("e2", "o2", "EQQQ", 4, "300", FRI)]
    book._write(tmp_path / book.LEDGER, [book.COLUMNS, *rows, (*BOUGHT.__dict__.values(),)])

    def flat(c: int) -> tuple[Decimal, Decimal, Decimal, Decimal, int]:
        return (Decimal(c),) * 4 + (1,)

    with bars.writing(tmp_path / "bars.db") as round_:  # VUAG: 13:50, 13:55 and 14:00 (unended)
        round_.five(
            VUAG,
            [Five(_at(t), *flat(c)) for t, c in (("13:50", 99), ("13:55", 101), ("14:00", 150))],
        )
        round_.five(EQQQ, [Five(_at("13:55"), *flat(297))])
    daily = {VUAG: [Bar(FRI, *flat(100))], EQQQ: [Bar(FRI, *flat(300))], UNHELD: []}

    def told() -> str:
        return pnl.told(tmp_path, tmp_path / "bars.db", daily, {}, Decimal(1000), NOW)

    assert told() == TEXT
    halt.call(tmp_path, NOW, "a crash", by=halt.OPERATOR)
    assert told().endswith(Mood.HALTED.value)
    book.turn(tmp_path, Switch.ON, NOW + timedelta(minutes=1), "drill")
    assert told().endswith(Mood.KILLED.value)
