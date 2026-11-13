#!/usr/bin/env python
"""THE ONE CHECK. Nothing else verifies anything on this desk.

    python check.py           everything (the gate for a merge)
    python check.py --fast    format, lint and the guards only, for a commit hook
    python check.py --scenes  the north-star scenes alone, in plain English

The git hook runs this. The GitHub check runs this. "Done" means this exited 0 and
you read the output. There is no second way of being sure, because a second way is
how a desk ends up with two answers to the same question.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parent

Step = tuple[str, list[str]]

FAST: list[Step] = [
    ("format", ["ruff", "format", "--check", "."]),
    ("lint", ["ruff", "check", "."]),
    ("guards", ["pytest", "tests/guards", "-q"]),
]

FULL: list[Step] = [
    *FAST,
    ("types", ["mypy"]),
    ("unit", ["pytest", "tests/unit", "-q"]),
    ("scenes", ["pytest", "tests/scenes", "-q"]),
]

#: The one published progress number, in docs/PLAN.md. The scenes step holds it true.
PUBLISHED = re.compile(r"Scenes passing: \*\*(\d+) of (\d+)\*\*")
NOT_BUILT = "NotImplementedError: "


def run(name: str, command: list[str]) -> tuple[str, int, float]:
    started = time.monotonic()
    tool = [sys.executable, "-m", *command] if command[0] != sys.executable else command
    result = subprocess.run(tool, cwd=ROOT, check=False)  # noqa: S603
    return name, result.returncode, time.monotonic() - started


def judge(report: Path) -> tuple[int, int, list[str]]:
    """Passing scenes, all scenes, and each scene that failed for any reason other than
    reaching a part of the desk that is not built yet."""
    passed, total, wrong = 0, 0, []
    for case in ElementTree.parse(report).getroot().iter("testcase"):  # noqa: S314
        total += 1
        outcome = next((c for c in case if c.tag in ("failure", "error", "skipped")), None)
        message = "" if outcome is None else outcome.get("message", outcome.tag)
        if outcome is None:
            passed += 1
        elif outcome.tag == "failure" and message.startswith(NOT_BUILT):
            print(f"  NOT BUILT  {case.get('name')}: {message.removeprefix(NOT_BUILT)}")
        else:
            wrong.append(f"{case.get('name')}: {outcome.tag}: {message}")
    return passed, total, wrong


def scenes(command: list[str]) -> tuple[str, int, float]:
    """THE SCENES ARE A RATCHET, NOT A KNOWN-FAILING LIST. Each scene passes, or stops at
    a part of the desk that raises NotImplementedError and is listed in docs/STATUS.md.
    Any other failure is red. So is a count different from the one docs/PLAN.md
    publishes: a passing scene that regresses, and a new pass nobody recorded."""
    started = time.monotonic()
    with tempfile.TemporaryDirectory() as folder:
        report = Path(folder) / "scenes.xml"
        run("scenes", [*command, f"--junitxml={report}"])
        if not report.exists():
            print("  the scenes wrote no report: pytest did not run them")
            return "scenes", 1, time.monotonic() - started
        passed, total, wrong = judge(report)
    match = PUBLISHED.search((ROOT / "docs" / "PLAN.md").read_text(encoding="utf-8"))
    published = (int(match[1]), int(match[2])) if match else None
    for line in wrong:
        print(f"  WRONG      {line}")
    print(f"  scenes passing: {passed} of {total}; docs/PLAN.md publishes {published}")
    if published != (passed, total):
        print("  the published number is not the measured one: correct docs/PLAN.md")
    red = bool(wrong) or published != (passed, total)
    return "scenes", int(red), time.monotonic() - started


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="the one check")
    parser.add_argument("--fast", action="store_true", help="format, lint and guards only")
    parser.add_argument("--scenes", action="store_true", help="the north-star scenes only")
    args = parser.parse_args(argv)

    if args.scenes:
        steps = [("scenes", ["pytest", "tests/scenes", "-q", "-v"])]
    else:
        steps = FAST if args.fast else FULL

    results = []
    for name, command in steps:
        #: A missing directory is not a pass. Until a stage creates its tests, the step
        #: says ABSENT out loud rather than printing nothing and exiting 0.
        target = next((Path(a) for a in command if a.startswith("tests/")), None)
        if target is not None and not (ROOT / target).exists():
            print(f"  {name:8} ABSENT  ({target} does not exist yet)")
            continue
        print(f"\n=== {name}")
        results.append(scenes(command) if name == "scenes" else run(name, command))

    print("\n--- the check")
    for name, code, seconds in results:
        print(f"  {name:8} {'PASS' if code == 0 else f'FAIL rc={code}'}  {seconds:5.1f}s")
    failed = [name for name, code, _ in results if code != 0]
    print(f"\n{'RED: ' + ', '.join(failed) if failed else 'GREEN'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
