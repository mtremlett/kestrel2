"""The wait of an order at the market is measured: the moments it was sent, the broker first
accepted it, each fill came and the desk cancelled it, taken from the gateway's own messages
and kept beside the day's orders."""

from __future__ import annotations

import csv
import io
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from test_paper import ACCOUNTS, HELLO, NEXT, Said, _account, _but, _gateway, _order, _wire
from test_placing import AT, BUY_IT, CHILD, ENDED_42, HELD, ID, MINE, SALE, _ready
from test_reports import END, LISTED

from desk import order_times, paper, placing
from desk.listing import Listing

T0 = datetime(2026, 11, 19, 8, 10, tzinfo=UTC)
SHARES = "26"


class _Tape:
    """A gateway as a tape: each message comes at its second after the start, and the clock
    is set to it as the message is read; after the last it is silent, until the wait runs out."""

    def __init__(self, tape: Sequence[tuple[int, Sequence[str]]]) -> None:
        self.now, self._chunks = T0, []
        for second, fields in tape:
            wire = _wire(fields).getvalue()
            self._chunks += [(second, wire[:4]), (second, wire[4:])]

    def read(self, size: int = -1) -> bytes:
        if not self._chunks:
            raise TimeoutError("timed out")
        second, chunk = self._chunks.pop(0)
        self.now = T0 + timedelta(seconds=second)
        assert len(chunk) == size
        return chunk


def _rows(root: Path) -> list[tuple[str, str, str]]:
    with (root / order_times.TIMES).open(encoding="utf-8") as file:
        return [(r["event"], r["at"], r["shares"]) for r in csv.DictReader(file)]


def _at(seconds: int) -> str:
    return (T0 + timedelta(seconds=seconds)).isoformat(timespec="milliseconds")


def test_a_trail_holds_when_it_was_sent_accepted_and_filled(tmp_path: Path) -> None:
    fill = ["0"] * 31
    fill[:3], fill[19] = ["11", paper.UNASKED, "41"], SHARES
    submitted, filled = MINE[1], _but(MINE[1], 2, "Filled")
    tape = _Tape([(0, HELLO), (0, ACCOUNTS), (0, NEXT), (2, submitted), (40, fill), (40, filled)])
    times = order_times.Times(lambda: tape.now, paper.DESK)
    chunks = io.BytesIO()
    door, listed = paper.Door(paper.DESK), LISTED["IITU"]
    assert isinstance(listed, Listing)
    number, word, _ = placing._place(  # noqa: SLF001 - the send path, driven by its tape
        tape,  # type: ignore[arg-type]  # all a wire is asked is its reads
        chunks.write,
        listed,
        SALE,
        door,
        times,
    )
    assert (number, word) == ("41", "Filled")
    times.keep(tmp_path, ID)
    assert _rows(tmp_path) == [
        ("sent", _at(0), ""),
        ("accepted", _at(2), ""),
        ("fill", _at(40), SHARES),
    ]


def test_an_order_the_broker_never_accepts_records_sent_and_the_cancel(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    old = _order("7", "SELL STP", "b-stop", "PreSubmitted")
    was, idle = _account([HELD], *old), _account([HELD], *CHILD, *old)
    gone = [_but(MINE[1], 2, "Cancelled")]
    answers: list[Said] = [[CHILD[1]], gone, idle, [("102",)], [END], idle, [ENDED_42]]
    _gateway(monkeypatch, [], was, *answers, silent=True)
    stamps = iter(T0 + timedelta(milliseconds=ms) for ms in (5, 1250))
    door = paper.Door(paper.DESK)
    placing.Paper(LISTED, _ready(tmp_path), lambda: AT, door, lambda: next(stamps)).place(BUY_IT)
    assert [(e, a) for e, a, _ in _rows(tmp_path)] == [
        ("sent", "2026-11-19T08:10:00.005+00:00"),
        ("cancelled", "2026-11-19T08:10:01.250+00:00"),
    ]
