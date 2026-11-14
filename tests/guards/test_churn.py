"""THE CHURN GUARD. Fixes on fixes to one file are the doom loop the first desk died of: each
fix true, the mechanism never found. A product file whose last ten changes on main hold
three fixes, counting this change when it is one, fails the check until
`docs/FAILURE_PATTERNS.md` names the file beside the mechanism that keeps breaking it.

A fix is a change whose title starts `fix` (main's history is one squashed change per pull
request, titled as the pull request was). This change's title is its pull request's on
GitHub, and otherwise the subjects of its own commits.

Approved by the operator, 14 November 2026 (gate G-B, docs/DECISIONS.md).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRODUCT = ("desk/", "lab/")
WINDOW = 10  #: a file's last this many changes, this one included when it is a fix
FIXES = 3  #: this many fixes among them is a recurring problem
FIX = re.compile(r"fix\b")


def _git(*args: str) -> str:
    return subprocess.run(  # noqa: S603
        ["git", *args],  # noqa: S607
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    ).stdout


def _titles(base: str) -> list[str]:
    """This change's title: its pull request's on GitHub, else its own commits' subjects."""
    if os.environ.get("GITHUB_EVENT_NAME") == "pull_request":
        event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))
        return [str(event["pull_request"]["title"])]
    return _git("log", "--format=%s", f"{base}..HEAD").splitlines()


def _churned(base: str, is_fix: bool) -> dict[str, int]:
    """Each product file this change touches, with its fixes in its last WINDOW changes,
    where those reach FIXES."""
    touched = _git("diff", "--name-only", "--no-renames", base).splitlines()
    out: dict[str, int] = {}
    for path in (p for p in touched if p.startswith(PRODUCT) and p.endswith(".py")):
        history = _git("log", f"-{WINDOW - int(is_fix)}", "--format=%s", base, "--", path)
        fixes = sum(bool(FIX.match(s)) for s in history.splitlines()) + int(is_fix)
        if fixes >= FIXES:
            out[path] = fixes
    return out


def test_a_file_fixed_again_and_again_names_its_mechanism() -> None:
    """DOOM LOOP. A third fix to one file within ten changes stops here until the reason
    it keeps breaking is written down, with the file's name, where every session reads."""
    base = _git("merge-base", "HEAD", "origin/main").strip()
    is_fix = any(FIX.match(t) for t in _titles(base))
    patterns = (ROOT / "docs" / "FAILURE_PATTERNS.md").read_text(encoding="utf-8")
    unnamed = {p: n for p, n in _churned(base, is_fix).items() if f"`{p}`" not in patterns}
    assert not unnamed, (
        f"fixed {FIXES} or more times in its last {WINDOW} changes, and no mechanism named: "
        f"{unnamed}. Stop fixing; find why it keeps breaking (CANON A2) and add a pattern to "
        "docs/FAILURE_PATTERNS.md naming the file in backquotes. A lane cannot: it writes "
        "the finding under 'Found, not fixed' in its STATUS section and its session ends."
    )
