"""THE CHECK RUNS THE PINNED TOOLS. `check.py` runs each tool as `python -m <tool>` under the
python that started it, so a session that starts it with the PC's own python (mypy 2.3.0, numpy
2.3.5) passes 'types clean' where GitHub, on requirements.txt's pins, fails (#2233, 26 Nov,
lab/rung_fit.py). Every pinned package must be installed at its pin (failure pattern 5's twin).
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _installed(name: str) -> str:
    """The version this python has of one package, or 'not installed'."""
    try:
        return version(name)
    except PackageNotFoundError:
        return "not installed"


def test_the_check_runs_the_pinned_tools() -> None:
    lines = (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
    pins = dict(
        line.strip().split("==", 1) for line in lines if "==" in line and not line.startswith("#")
    )
    wrong = {
        name: f"pinned {pin}, running {_installed(name)}"
        for name, pin in pins.items()
        if _installed(name) != pin
    }
    assert (
        not wrong
    ), f"not the declared environment (requirements.txt): {wrong}; use .venv's python"
