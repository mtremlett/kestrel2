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
import contextlib
import os
import re
import subprocess
import sys
import tempfile
import time
from collections.abc import Iterator
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


#: Seconds between looks for a free turn.
WAIT_SECONDS = 2.0


def _alive(pid: int) -> bool:
    """Whether a process still runs (a check that died leaves its turn file behind). On
    Windows it asks the process's exit code, never os.kill, which would end it there."""
    import ctypes  # noqa: PLC0415

    windll = getattr(ctypes, "windll", None)
    if windll is None:  # not Windows
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        return True
    handle = windll.kernel32.OpenProcess(0x1000, False, pid)  # query limited information
    if not handle:
        return False
    code = ctypes.c_ulong()
    windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
    windll.kernel32.CloseHandle(handle)
    return bool(code.value == 259)  # still active


def _take(path: Path) -> bool:
    """A turn is a file made in one step (it exists, or this check made it), naming its
    check's process. One whose process has gone is freed, so a killed check holds no turn."""
    try:
        made = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        try:
            owner = int(path.read_text(encoding="utf-8") or 0)
        except (OSError, ValueError):
            return False  # being written this instant: look again
        if owner and not _alive(owner):
            path.unlink(missing_ok=True)
        return False
    with os.fdopen(made, "w", encoding="utf-8") as out:
        out.write(str(os.getpid()))
    return True


@contextlib.contextmanager
def turn() -> Iterator[None]:
    """AT MOST N FULL CHECKS AT ONCE ON ONE PC. Up to twelve sessions check side by side on
    the operator's PC; on 14 November six at once took nine minutes each against thirty
    seconds alone. KESTREL_CHECK_TURNS=N (set by the runner) makes a check wait its turn;
    unset, on GitHub or in a person's own run, nothing waits."""
    turns = int(os.environ.get("KESTREL_CHECK_TURNS") or 0)
    if turns <= 0:
        yield
        return
    folder = Path(os.environ.get("KESTREL2_DATA") or tempfile.gettempdir()) / "check-turns"
    folder.mkdir(parents=True, exist_ok=True)
    started, told = time.monotonic(), False
    while True:
        for path in (folder / f"turn-{n}" for n in range(turns)):
            if _take(path):
                if told:
                    print(f"  (waited {time.monotonic() - started:.0f}s for a turn)")
                try:
                    yield
                finally:
                    path.unlink(missing_ok=True)
                return
        if not told:
            print(f"  waiting for a turn: {turns} full checks at once on this PC")
            told = True
        time.sleep(WAIT_SECONDS)


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

    results: list[tuple[str, int, float]] = []
    with turn() if steps is FULL else contextlib.nullcontext():
        _steps(steps, results)
    return _report(results)


def _steps(steps: list[Step], results: list[tuple[str, int, float]]) -> None:
    for name, command in steps:
        #: A missing directory is not a pass. Until a stage creates its tests, the step
        #: says ABSENT out loud rather than printing nothing and exiting 0.
        target = next((Path(a) for a in command if a.startswith("tests/")), None)
        if target is not None and not (ROOT / target).exists():
            print(f"  {name:8} ABSENT  ({target} does not exist yet)")
            continue
        print(f"\n=== {name}")
        results.append(scenes(command) if name == "scenes" else run(name, command))


def _report(results: list[tuple[str, int, float]]) -> int:
    print("\n--- the check")
    for name, code, seconds in results:
        print(f"  {name:8} {'PASS' if code == 0 else f'FAIL rc={code}'}  {seconds:5.1f}s")
    failed = [name for name, code, _ in results if code != 0]
    print(f"\n{'RED: ' + ', '.join(failed) if failed else 'GREEN'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
