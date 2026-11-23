"""The watcher: a dead supervisor is told, a live or restarting one is not."""

from __future__ import annotations

from contextlib import ExitStack
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import Mock

import pytest

from desk import supervisor, watcher
from desk.supervisor import Job

T0 = datetime(2026, 11, 16, 8, tzinfo=UTC)
STEP = Job("step", "the_job", timedelta(minutes=5), timedelta(seconds=60))


def test_a_supervisor_alive_or_restarting_is_no_fault_and_a_dead_one_is_told(
    tmp_path: Path,
) -> None:
    say, wait = Mock(), Mock()
    with supervisor._only(tmp_path, "supervisor"):  # noqa: SLF001
        assert watcher.alive(tmp_path, wait) and not wait.called

    # restarted: held again at the second look
    def restart(_: float) -> None:
        held.enter_context(supervisor._only(tmp_path, "supervisor"))  # noqa: SLF001

    with ExitStack() as held:
        assert watcher.alive(tmp_path, restart)
    # nobody there at either look: told, once in the hour's name, with the job's lateness
    assert watcher.watch(tmp_path, T0, [STEP], say, wait)
    name, words = say.call_args.args
    assert name == "watch 2026-11-16 08"
    assert (
        watcher.DEAD.format(tmp_path) in words and supervisor.LATE.format("step", "at all") in words
    )


def test_the_command_takes_one_root() -> None:
    with pytest.raises(SystemExit, match="watcher"):
        watcher.main([])
