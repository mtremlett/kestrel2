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
from test_placing import ACCOUNT, FILLS
from test_reports import END
from test_running import FLAT_, _desk, _step

from desk import book, clearance, halt, paper, placing, running, watch
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
    assert _step(monkeypatch, desk, open_, none, tp.EMPTY) == [FILLS, ACCOUNT]  # no order
    assert not running.notes(tmp_path) and not book.fills(tmp_path)
    (call,) = look.call_args_list
    assert call.args[:2] == (desk.root, desk.hot) and call.args[3:] == (open_, desk.post)
    assert list(call.args[2]) == list(desk.held(open_.date())[0])
    broker = call.kwargs["door"]()  # a crash halt's door builds the paper broker on demand
    assert isinstance(broker, placing.Paper)
    # its first bar lands: at the next step the round is made, and the look is made before it
    with writing(desk.hot) as round_:
        round_.five(YARDSTICK, [Five(open_ - timedelta(minutes=5), *(Decimal(40),) * 4, 1)])
    # London's orders wait for 09:00 UK (R-RUNNER-453): 08:10 sends none, 09:05 sends the round
    _step(monkeypatch, desk, open_ + timedelta(minutes=5), none, tp.EMPTY)
    assert not running.notes(tmp_path)
    later = open_ + timedelta(minutes=60)
    _step(monkeypatch, desk, later, none, tp.EMPTY, none)
    assert [n.what for n in running.notes(tmp_path)] == ["orders LSE"] and look.call_count == 3
    assert [c.args[3] for c in look.call_args_list][::2] == [open_, later]
    # a look that fails holds the round, and the rest of the step is done; the failure is raised
    look.side_effect = OSError("the store is gone")
    with pytest.raises(OSError, match="store is gone"):
        _step(monkeypatch, desk, later + timedelta(days=1), none, tp.EMPTY)
    assert [n.what for n in running.notes(tmp_path)][1:] == ["trouble OSError"]
    assert len(clearance.checks(tmp_path)) == 3
    # and a gateway that is silent is looked past: the look is made at any hour
    look.side_effect = None
    monkeypatch.setattr(paper, "dial", Mock(side_effect=ConnectionRefusedError))
    running.step(desk, later + timedelta(days=1, hours=14))
    assert look.call_args.args[3] == later + timedelta(days=1, hours=14)


def test_the_alarm_of_a_send_that_pulled_the_kill_switch_is_told_in_its_words_once(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    desk, post = _desk(tmp_path, IITU=FLAT_)
    words = "o-3: place failed with OSError(); the kill switch is on"
    monkeypatch.setattr(watch, "look", Mock(side_effect=book.Alarm(words)))
    now = datetime(2026, 12, 1, 9, 0, tzinfo=UTC)
    for later in (now, now + timedelta(minutes=5)):
        with pytest.raises(book.Alarm, match="kill switch is on"):
            _step(monkeypatch, desk, later, [END], tp.EMPTY)
    (note,) = running.notes(tmp_path)
    assert note.what == "trouble Alarm" and words in note.words
    assert [c.args[0] for c in post.call_args_list].count(note.words) == 1


def test_a_halt_in_force_takes_the_working_buys_down_at_the_step(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    desk, _ = _desk(tmp_path, IITU=FLAT_)
    now = datetime(2026, 12, 1, 8, 1, tzinfo=UTC)
    cancel = Mock(return_value=())
    monkeypatch.setattr(placing.Paper, "cancel", cancel)
    _step(monkeypatch, desk, now, [END], tp.EMPTY)
    cancel.assert_not_called()  # no halt: nothing is cancelled
    halt.call(tmp_path, now, "a crash", by=watch.WATCH, his=False)
    _step(monkeypatch, desk, now + timedelta(minutes=5), [END], tp.EMPTY)
    cancel.assert_called_once_with()
