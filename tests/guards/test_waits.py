"""A WAIT NAMES A REAL REQUEST (failure pattern 20, a gate that can never open): every request
id an open box in docs/PLAN.md waits on is a request line in docs/STATUS.md, open or done
(`- [ ] R-X-n` or `- [x] R-X-n`), so the runner can see it close. A wait on a request no line
holds never lifts: rungs-reproduce waited on two requests done on 16 and 19 Nov but never
written as lines, and money-restop on one never written at all (seat 44, 22 Nov)."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BOX = re.compile(r"^- \[ \] (.*(?:\n[ \t]+\S.*)*)", re.MULTILINE)
WAITS = re.compile(r"waits:([^;}]*)")
REQUEST = re.compile(r"R-[A-Z]+-\d+")


def test_every_request_a_box_waits_on_is_a_request_line() -> None:
    plan = (ROOT / "docs" / "PLAN.md").read_text(encoding="utf-8")
    status = (ROOT / "docs" / "STATUS.md").read_text(encoding="utf-8")
    lines = set(re.findall(r"^\s*- \[[ x]\] (R-[A-Z]+-\d+)\b", status, re.MULTILINE))
    waited = {
        rid for box in BOX.findall(plan) for w in WAITS.findall(box) for rid in REQUEST.findall(w)
    }
    assert sorted(waited - lines) == [], (
        "a box waits on a request with no line in docs/STATUS.md, so its wait never lifts: "
        f"{sorted(waited - lines)}. Write the request as '- [ ] R-X-n ...' (or '- [x]' if done)."
    )
