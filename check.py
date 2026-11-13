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
import subprocess
import sys
import time
from pathlib import Path

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


def run(name: str, command: list[str]) -> tuple[str, int, float]:
    started = time.monotonic()
    tool = [sys.executable, "-m", *command] if command[0] != sys.executable else command
    result = subprocess.run(tool, cwd=ROOT, check=False)  # noqa: S603
    return name, result.returncode, time.monotonic() - started


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
        results.append(run(name, command))

    print("\n--- the check")
    for name, code, seconds in results:
        print(f"  {name:8} {'PASS' if code == 0 else f'FAIL rc={code}'}  {seconds:5.1f}s")
    failed = [name for name, code, _ in results if code != 0]
    print(f"\n{'RED: ' + ', '.join(failed) if failed else 'GREEN'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
