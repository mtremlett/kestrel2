"""THE CHECK ON GITHUB IS THE ONE CHECK, SPLIT, NEVER THINNED.

GitHub runs the steps of `python check.py` side by side, the unit tests in shares, and its
job named "check" (the one main's rules require) is green only when every step passed.
These guards hold the workflow to check.py: a step dropped from the list, a share of the
unit tests missing, or a "check" that could be green without its steps, is red here.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "check.yml"
STEP = re.compile(r"^ +- step: (\w+)\n(?: +shard: (\d+)/(\d+)\n)?", re.MULTILINE)


def _check_py() -> ModuleType:
    spec = importlib.util.spec_from_file_location("the_check", ROOT / "check.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _job(name: str) -> str:
    text = WORKFLOW.read_text(encoding="utf-8")
    found = re.search(rf"^  {name}:\n(.*?)(?=^  \S|\Z)", text, re.MULTILINE | re.DOTALL)
    assert found, f"the workflow has no job {name!r}"
    return found[1]


def test_github_runs_every_step_of_the_full_check() -> None:
    steps = STEP.findall(_job("step"))
    named = {name for name, _, _ in steps}
    assert named == {
        name for name, _ in _check_py().FULL
    }, f"workflow steps {named} differ from check.py's"
    assert "python check.py --only ${{ matrix.step }}" in _job("step")
    assert "fail-fast: false" in _job("step")


def test_the_unit_shares_are_one_to_n_with_no_gap() -> None:
    shares = [(int(i), int(n)) for name, i, n in STEP.findall(_job("step")) if name == "unit"]
    assert shares, "the unit step has no shares"
    parts = {n for _, n in shares}
    assert len(parts) == 1, f"the unit shares disagree on how many there are: {shares}"
    assert sorted(i for i, _ in shares) == list(range(1, parts.pop() + 1))


def test_the_shares_hold_every_unit_test_file_exactly_once() -> None:
    check = _check_py()
    every = sorted(
        f.relative_to(ROOT).as_posix() for f in (ROOT / "tests" / "unit").glob("test_*.py")
    )
    for parts in (1, 2, 3, 5):
        got = [
            a
            for i in range(1, parts + 1)
            for a in check.shard(["pytest", "tests/unit", "-q"], i, parts)
            if a.startswith("tests/")
        ]
        assert sorted(got) == every, f"{parts} shares do not hold every unit test file exactly once"


def test_the_required_check_is_green_only_when_every_step_is() -> None:
    job = _job("check")
    assert re.search(
        r"^    needs: step$", job, re.MULTILINE
    ), "the check job must wait for every step"
    assert re.search(
        r"^    if: always\(\)$", job, re.MULTILINE
    ), "a failed step must still run the check, red"
    assert 'test "${{ needs.step.result }}" = "success"' in job
    assert re.search(r"^    needs: check$", _job("announce"), re.MULTILINE)
