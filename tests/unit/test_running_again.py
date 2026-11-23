"""The round owed once more (R-RUNNER-395): only orders the desk itself cancelled go again."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest
from test_running import MON

from desk import book, running, venues
from desk.lines import LINES

LSE = [line.symbol for line in LINES if line.venue == "LSE"][:3]
TODAY = MON.date()


def _plant(root: Path, cancelled: list[str], noted: tuple[str, ...] = ("orders LSE",)) -> None:
    book._write(
        root / book.CANCELS, [[f"{TODAY:%Y%m%d}-s-{s}", TODAY.isoformat()] for s in cancelled]
    )
    for what in noted:
        running._note(root, MON, what, "x")


def test_only_the_desks_own_cancels_go_again_once_and_not_after_the_close(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    look, open_ = SimpleNamespace(), venues.hours("LSE", TODAY).open
    assert running._again(tmp_path, open_, look) == {}  # type: ignore[arg-type]  # no cancels
    _plant(tmp_path, LSE[:2])  # a third order was refused or cancelled by the broker: not listed
    now = open_ + timedelta(minutes=30)
    assert running._again(tmp_path, now, look) == {"LSE": set(LSE[:2])}  # type: ignore[arg-type]
    assert running._again(tmp_path, now, None) == {}  # the look failed
    fill = SimpleNamespace(order_id=f"{TODAY:%Y%m%d}-s-{LSE[0]}-r1", day=TODAY)
    monkeypatch.setattr(book, "fills", lambda _root: [fill])  # one went again and filled
    assert running._again(tmp_path, now, look) == {"LSE": {LSE[1]}}  # type: ignore[arg-type]
    after = venues.hours("LSE", TODAY).close + timedelta(minutes=1)
    assert running._again(tmp_path, after, look) == {}  # type: ignore[arg-type]
    running._note(tmp_path, now, "orders LSE again", "x")
    assert running._again(tmp_path, now, look) == {}  # type: ignore[arg-type]  # never a third
