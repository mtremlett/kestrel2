"""The audit command: with the data folder unset it fails loudly and opens no file."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_unset_data_folder_fails_loudly_and_opens_nothing(tmp_path: Path) -> None:
    """KESTREL2_DATA unset: non-zero exit, a message naming it, no file made in the folder."""
    env = {k: v for k, v in os.environ.items() if k != "KESTREL2_DATA"}
    env["PYTHONPATH"] = str(ROOT)
    run = subprocess.run(  # noqa: S603  # fixed argv
        [sys.executable, "-m", "desk.audit", "--audit"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert run.returncode != 0
    assert "KESTREL2_DATA" in run.stderr
    assert list(tmp_path.iterdir()) == []
