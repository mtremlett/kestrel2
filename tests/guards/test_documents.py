"""DOCUMENT BLOAT, a first-desk failure pattern: records that only grow until nobody reads
them. The first desk reached 728 documents; this one holds its few documents to a size a
session reads whole. Ruled 13 November 2026 (docs/DECISIONS.md):

- docs/STATUS.md at most 300 lines, and each lane's section of it at most 60;
- each entry of docs/DECISIONS.md at most 80 lines;
- CLAUDE.md at most 80 lines (it says so itself).

A fixed item is removed from STATUS, not kept: git keeps it.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATUS_MAX, SECTION_MAX, ENTRY_MAX, CLAUDE_MAX = 300, 60, 80, 80
ENTRY = re.compile(r"^#{2,3} \d{4}-\d\d-\d\d\b", re.MULTILINE)


def _lines(path: str) -> list[str]:
    return (ROOT / path).read_text(encoding="utf-8").splitlines()


def _sections(text: str, heading: re.Pattern[str]) -> dict[str, int]:
    marks = list(heading.finditer(text))
    ends = [m.start() for m in marks[1:]] + [len(text)]
    return {
        m.group(0): len(text[m.start() : end].splitlines())
        for m, end in zip(marks, ends, strict=True)
    }


def test_status_stays_small() -> None:
    status = (ROOT / "docs" / "STATUS.md").read_text(encoding="utf-8")
    total = len(status.splitlines())
    assert (
        total <= STATUS_MAX
    ), f"docs/STATUS.md is {total} lines; at most {STATUS_MAX}. Remove what is fixed."
    lanes = {
        lane.upper()
        for lane in tomllib.loads((ROOT / "manifest.toml").read_text(encoding="utf-8"))["lanes"]
    }
    sizes = _sections(status, re.compile(r"^## (\S+)\s*$", re.MULTILINE))
    over = {name: n for name, n in sizes.items() if name[3:].strip() in lanes and n > SECTION_MAX}
    assert (
        not over
    ), f"lane sections over {SECTION_MAX} lines: {over}. Remove what is fixed; git keeps it."


def test_decisions_are_short() -> None:
    text = (ROOT / "docs" / "DECISIONS.md").read_text(encoding="utf-8")
    over = {name: n for name, n in _sections(text, ENTRY).items() if n > ENTRY_MAX}
    assert not over, f"decisions over {ENTRY_MAX} lines: {over}. Say it shorter, or split it."


def test_claude_md_is_held_to_its_limit() -> None:
    assert len(_lines("CLAUDE.md")) <= CLAUDE_MAX, f"CLAUDE.md is over {CLAUDE_MAX} lines"
