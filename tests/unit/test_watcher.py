"""The supervisor's watcher: told when no supervisor lives past a restart, never for one."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import Mock

import pytest

from desk import watcher
from desk.supervisor import _only

T0 = datetime(2026, 11, 22, 8, tzinfo=UTC)


def test_the_watcher_raises_when_the_supervisor_receipt_is_stale(tmp_path: Path) -> None:
    say = Mock()
    assert not watcher.watched(tmp_path, T0, say)  # first look: noted
    assert not watcher.watched(tmp_path, T0 + watcher.RESTART_GRACE / 2, say)
    late = T0 + watcher.RESTART_GRACE
    assert watcher.watched(tmp_path, late, say)
    say.assert_called_once()
    assert say.call_args.args[0] == "supervisor 2026-11-22 08"  # the hour names it
    assert "Sun 22 Nov 08:00" in say.call_args.args[1]


def test_a_supervisor_that_lives_is_never_told_and_clears_the_note(tmp_path: Path) -> None:
    say = Mock()
    watcher.watched(tmp_path, T0, say)
    with _only(tmp_path, "supervisor"):
        assert not watcher.watched(tmp_path, T0 + timedelta(hours=2), say)
    assert not (tmp_path / watcher.WATCHER_NOTE).exists()
    say.assert_not_called()


def test_the_command_refuses_other_words_and_a_local_moment(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        watcher.main([])
    with pytest.raises(ValueError, match="UTC"):
        watcher.watched(tmp_path, datetime(2026, 11, 22, 8), Mock())
