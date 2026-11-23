"""The lines parked live, back by themselves; the lines staler than a session; the receipt."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from desk import bars, keeper, keeper_receipt, venues
from desk.bars import Five, Source
from desk.lines import Line
from desk.store import Bar

NOW, LINES = datetime(2026, 11, 16, 10, tzinfo=UTC), [Line(s, "LSE", "GBP", 1) for s in "ABCD"]


def _bar(minutes: int, price: int) -> Five:
    p = Decimal(price)
    return Five(NOW - timedelta(minutes=minutes), p, p, p, p, 1)


def test_a_late_missing_or_out_of_line_line_is_parked_and_comes_back(tmp_path: Path) -> None:
    hot, (clean, late, jump, none) = tmp_path / keeper.HOT, LINES
    with bars.writing(hot, Source.IBKR) as kept:
        kept.five(clean, [_bar(10, 100), _bar(5, 100)])
        kept.five(late, [_bar(30, 100), _bar(20, 100)])
        kept.five(jump, [_bar(10, 100), _bar(5, 200)])
    parked = keeper.parked_live(hot, LINES, NOW)
    assert set(parked) == {"B", "C", "D"} and "moved" in parked["C"]
    assert keeper.parked_live(hot, LINES, NOW - timedelta(minutes=115)) == {}  # just opened
    with bars.writing(hot, Source.IBKR) as kept:
        kept.five(late, [_bar(5, 100)])
    assert "B" not in keeper.parked_live(hot, LINES, NOW) and none.symbol in parked
    later = NOW + timedelta(minutes=3)  # the source's delay: minutes since a newest bar ended
    assert keeper.delays(hot, LINES, later) == {"A": 3, "B": 3, "C": 3}


def test_a_line_staler_than_a_session_is_a_miss_and_each_call_leaves_a_dated_receipt(
    tmp_path: Path,
) -> None:
    hot, (fresh, old, *_) = tmp_path / keeper.HOT, LINES
    one = Decimal(1)
    with bars.writing(hot) as kept:
        for line, last in ((fresh, date(2026, 11, 13)), (old, date(2026, 11, 12))):
            kept.daily(line, [Bar(last, one, one, one, one, 1)])
    told = keeper.stale(hot, LINES, NOW)  # Monday morning: Friday's close is the one owed
    assert [t.split(":")[0] for t in told] == ["B", "C", "D"] and "None" in told[1]
    keeper_receipt.write(tmp_path, NOW, ["done"], [], {})
    keeper_receipt.write(tmp_path, NOW, [], ["missed"], {})
    day = tmp_path / keeper_receipt.RECEIPTS / "2026-11-16.jsonl"
    assert [json.loads(line)["missed"] for line in day.read_text("utf-8").splitlines()] == [
        [],
        ["missed"],
    ]


def test_a_receipt_says_each_newest_bar_that_arrived_once_and_survives_a_kill(
    tmp_path: Path,
) -> None:
    """DQ-10, DQ-12: a bar's source and arrival; a restart drill between line and record."""
    hot, line, receipt = tmp_path / keeper.HOT, LINES[0], keeper_receipt
    one = Decimal(1)
    with bars.writing(hot, Source.IBKR) as kept:
        kept.daily(line, [Bar(date(2026, 11, 13), one, one, one, one, 1)])
    held = receipt.newest(hot, LINES)
    assert held == {"LSE:A daily": f"{date(2026, 11, 13).toordinal()} IBKR paper"}
    assert receipt.write(tmp_path, NOW, [], [], held) == held  # first sight: arrived
    assert receipt.write(tmp_path, NOW, [], [], held) == {}  # seen: not again
    day = tmp_path / receipt.RECEIPTS / "2026-11-16.jsonl"
    with day.open("a", encoding="utf-8") as out:
        out.write('{"at": "torn')  # a kill in the middle of a line
    (tmp_path / receipt.RECEIPTS / receipt.SEEN).unlink()  # a kill before the record was swapped in
    assert receipt.write(tmp_path, NOW, [], [], held) == held  # said again, never lost
    rows = day.read_text("utf-8").splitlines()
    assert json.loads(rows[-1])["arrived"] == held and len(rows) == 4


def test_a_session_no_daily_source_holds_is_bridged_from_the_five_minute_bars_held(
    tmp_path: Path,
) -> None:
    """3LGO: the archive lacks Friday, and the store holds that day's five-minute bars."""
    line, friday, now = LINES[0], date(2026, 11, 13), NOW.replace(hour=6)
    days = venues.sessions("LSE", date(2026, 8, 3), friday - timedelta(1))
    flat = tuple(
        Bar(d, p, p + 1, p - 1, p, 9 + n) for n, d in enumerate(days) if (p := Decimal(100 + n % 5))
    )
    o, h, low, c = map(Decimal, (101, 103, 100, 102))
    with bars.writing(tmp_path / keeper.HOT) as round_:
        round_.five(line, [Five(datetime(2026, 11, 13, 10, tzinfo=UTC), o, h, low, c, 7)])
    kept = keeper.keep(tmp_path, now, (line,), lambda *_: flat, lambda *_: (), lambda: 0.0)
    assert kept[1] == [] and keeper.saved(tmp_path, now.date(), [line])[0][line][-1] == Bar(
        friday, o, h, low, c, 7
    )
