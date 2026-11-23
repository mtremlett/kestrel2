"""The one check waits its turn on the operator's PC: at most N full checks at once."""

from __future__ import annotations

import subprocess
import sys
import threading
from pathlib import Path

import pytest

import check


def test_at_most_n_full_checks_run_at_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KESTREL_CHECK_TURNS", "2")
    monkeypatch.setenv("KESTREL2_DATA", str(tmp_path))
    monkeypatch.setattr(check, "WAIT_SECONDS", 0.01)
    third = threading.Event()

    def another() -> None:
        with check.turn():
            third.set()

    with check.turn(), check.turn():
        waiting = threading.Thread(target=another, daemon=True)
        waiting.start()
        assert not third.wait(0.3), "a third check ran while two held both turns"
    assert third.wait(5), "the third check never got the turn that was freed"
    waiting.join(5)


def test_without_turns_nothing_waits(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("KESTREL_CHECK_TURNS", raising=False)
    with check.turn(), check.turn(), check.turn():
        pass


def test_a_turn_left_by_a_check_that_died_is_freed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("KESTREL_CHECK_TURNS", "1")
    monkeypatch.setenv("KESTREL2_DATA", str(tmp_path))
    gone = subprocess.run(  # noqa: S603 - this python, a fixed one-liner
        [sys.executable, "-c", "import os; print(os.getpid())"],
        capture_output=True,
        text=True,
        check=True,
    )
    (tmp_path / "check-turns").mkdir()
    (tmp_path / "check-turns" / "turn-0").write_text(gone.stdout.strip(), encoding="utf-8")
    took = threading.Thread(target=lambda: check.turn().__enter__(), daemon=True)
    took.start()
    took.join(5)
    assert not took.is_alive(), "a dead check's turn was never freed"
