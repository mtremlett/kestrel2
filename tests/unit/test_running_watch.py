"""The crash watch's look at each step of the desk unattended: made first, with the fast store and
the daily bars, and London's morning round waits for the market's first bar."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock

import pytest
import test_placing as tp
from test_paper import Said
from test_reports import END
from test_running import FLAT_, _desk, _step

from desk import book, running, watch
from desk.bars import Five, writing
from desk.lines import YARDSTICK


def test_every_step_looks_at_the_market_first_and_london_waits_for_its_first_bar(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    desk, post = _desk(tmp_path, IITU=FLAT_)
    look = Mock(wraps=watch.look)
    monkeypatch.setattr(watch, "look", look)
    none: Said = [END]
    open_ = datetime(2026, 12, 1, 8, 5, tzinfo=UTC)  # the fast store holds no bar of this day
    # the market is unheard of at 08:05: the look says wait, and no round of orders is begun
    _step(monkeypatch, desk, open_, none, tp.EMPTY)
    assert not running.notes(tmp_path) and not book.fills(tmp_path)
    (call,) = look.call_args_list
    assert call.args[:2] == (desk.root, desk.hot) and call.args[3:] == (open_, desk.post)
    assert list(call.args[2]) == list(desk.held.return_value[0])
    # its first bar lands: at the next step the round is made, and the look is made before it
    with writing(desk.hot) as round_:
        round_.five(YARDSTICK, [Five(open_ - timedelta(minutes=5), *(Decimal(40),) * 4, 1)])
    later = open_ + timedelta(minutes=5)
    _step(monkeypatch, desk, later, none, tp.EMPTY, none)
    assert [n.what for n in running.notes(tmp_path)] == ["orders LSE"] and look.call_count == 2
    assert [c.args[3] for c in look.call_args_list] == [open_, later]
