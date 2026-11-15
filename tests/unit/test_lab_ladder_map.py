"""The rung map in `lab/ladder.py`'s docstring (L2): the plan's eleven rungs, each named once
to its module and its test, and every file named either there or marked unbuilt."""

from __future__ import annotations

import re
from pathlib import Path

from lab import ladder

ROOT = Path(__file__).parents[2]
MODULE, TEST = r"lab/\w+\.py", r"tests/unit/test_lab_\w+\.py"
#: `n name: module, test`, either file followed by ` (unbuilt)`, then ` - what it still owes`
ENTRY = re.compile(rf" *(\d+) ([^:]+): ({MODULE})( \(unbuilt\))?, ({TEST})( \(unbuilt\))?( - .+)?")


def test_the_map_names_eleven_rungs_once_each_to_files_there_or_marked_unbuilt() -> None:
    doc = ladder.__doc__ or ""
    assert "THE RUNG MAP" in doc, "lab/ladder.py's docstring holds no rung map"
    paragraph = doc[doc.index("THE RUNG MAP") :].split("\n\n")[0]
    lines = [line for line in paragraph.splitlines() if line.lstrip()[:1].isdigit()]
    found = [ENTRY.fullmatch(line) for line in lines]
    unread = [line for line, entry in zip(lines, found, strict=True) if entry is None]
    assert not unread, f"not `n name: module, test`: {unread}"
    rungs = [entry.groups() for entry in found if entry is not None]
    assert [int(rung[0]) for rung in rungs] == list(range(1, 12)), "eleven rungs, 1 to 11, once"
    for what, column in (("name", 1), ("test", 4)):
        seen = [rung[column] for rung in rungs]
        twice = sorted({one for one in seen if seen.count(one) > 1})
        assert not twice, f"two rungs with one {what}: {twice}"
    named = [pair for rung in rungs for pair in (rung[2:4], rung[4:6])]
    missing = sorted(
        {path for path, unbuilt in named if not unbuilt and not (ROOT / path).is_file()}
    )
    assert not missing, f"named as built and not there (build it, or mark it unbuilt): {missing}"
