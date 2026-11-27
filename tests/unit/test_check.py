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


#: Seconds each unit file took in GitHub's check on 27 Nov (draft #2332, run 45958938974, the
#: five shares summed from `--durations=0`): every file at 10 s or more. A file not named weighs
#: its size, as check.py weighs it. The noise kit (#2237, after that run) carries check.py's own
#: 340 s: left out, it weighed its size, so its share read 134 s and the test tipped (#2396).
MEASURED = {
    "test_lab_ladder_pool.py": 459, "test_lab_ladder.py": 409, "test_lab_ladder_epon.py": 264,
    "test_lab_rung_known_answer.py": 134, "test_lab_rung_known_answer_noise.py": 340,
    "test_simcity_incidents.py": 131, "test_lab_tape.py": 125,
    "test_simcity.py": 98, "test_lab_rung_registry.py": 52, "test_lab_chain.py": 50,
    "test_lab_rung_golden.py": 46, "test_lab_verdict.py": 37, "test_lab_shuffle.py": 33,
    "test_lab_ladder_sets.py": 30, "test_command.py": 23, "test_lab_ladder_spec.py": 20,
    "test_lab_sweep.py": 12, "test_lab_tune.py": 12, "test_simcity_fills.py": 10,
}  # fmt: skip


def test_every_slow_unit_file_is_weighed_by_its_measured_seconds() -> None:
    slow = {name for name, seconds in MEASURED.items() if seconds >= 30}
    lacks = sorted(slow - set(check.SECONDS))
    assert not lacks, f"slow files the table lacks: {lacks}"


def test_no_unit_share_runs_a_quarter_over_the_mean_on_the_measured_seconds() -> None:
    def took(path: str) -> float:
        name = Path(path).name
        return MEASURED.get(name, (check.ROOT / path).stat().st_size / 20_000)

    loads = [sum(map(took, check.shard([check.UNIT_DIR], part, 5))) for part in range(1, 6)]
    mean = sum(loads) / len(loads)
    assert max(loads) <= mean * 1.25, f"shares' measured seconds {[round(x) for x in loads]}"
