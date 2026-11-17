"""A round moves each held line's stop to 10% under its own fill, once (R-RUNNER-220)."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest
import test_placing as tp
from test_reports import AAPL, IITU
from test_running import DAY, FLAT_, MON, _desk

from desk import book, day, restop, running
from desk.book_parts import keep
from desk.broker import Fill
from desk.orders import Refused, Sale


def test_a_round_moves_each_held_lines_stop_under_its_fill_once(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(day, "trade", lambda *_: ())
    held = {"IB1T": ("4.8825", "4.6602"), "MSTR": ("104.92", "100.458")}
    fills = [Fill(f"x{s}", f"o-{s}", s, 1, Decimal(p), MON.date()) for s, (p, _) in held.items()]
    book._record(tmp_path, fills)
    sent: list[tuple[str, Decimal]] = []
    rests = {s: Decimal(old) for s, (_, old) in held.items()}

    class Broker:
        stops = staticmethod(lambda: tuple((s, 1) for s in rests))
        restop = staticmethod(lambda s, level: sent.append((s, level)))

    for venue in ("LSE", "US", "LSE"):  #: the last round finds the levels kept
        running._round(_desk(tmp_path)[0], Broker(), venue, MON)  # type: ignore[arg-type]
    assert sent == [("IB1T", Decimal("4.39425")), ("MSTR", Decimal("94.428"))]


def test_a_held_line_left_out_of_a_round_is_told_apart_with_its_stop(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(day, "trade", lambda *_: ())
    monkeypatch.setattr(restop, "move", lambda *_: {})
    book._record(tmp_path, [Fill("x", "o-IITU", "IITU", 1, Decimal(36), MON.date())])
    keep(tmp_path / book.STOPS, [book.LEVELS, ("o-IITU-stop", "32.4")])
    desk = _desk(tmp_path, IITU=FLAT_)[0]
    running._round(desk, None, "LSE", MON + DAY)  # type: ignore[arg-type]
    words = running.notes(tmp_path)[-1].words
    assert "IITU held, not judged today: no bar of Mon 16 Nov; its stop rests at 32.4." in words
    assert (
        words.endswith("32.4.") and "Left out, parked or with no bar of Mon 16 Nov: VUAG." in words
    )
    assert "IITU, " not in words  # held: named apart, not in the plain list


def test_an_order_is_dated_the_session_before_today_on_its_own_venues_calendar(
    tmp_path: Path,
) -> None:
    # the Tuesday after Easter 2027: London was shut from Thursday, New York traded on Monday
    easter, thursday = tp._paper(tmp_path, datetime(2027, 3, 30, 8, 5, tzinfo=UTC)), "20270325-x-"
    for order, saying in (
        (Sale(f"{thursday}IITU", IITU, 5), "was not drilled"),  # so it may go: the next refusal
        (Sale("20270324-x-IITU", IITU, 5), "is not the session of LSE's next after"),
        (Sale(f"{thursday}AAPL", AAPL, 5), "is not the session of US's next after"),
        (Sale("drill-sale", IITU, 5), "next after the one it is dated"),  # and one not dated
    ):
        with pytest.raises(Refused, match=saying):
            easter.place(order)
