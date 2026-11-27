"""The rung map in `lab/ladder.py`'s docstring (L2): the plan's eleven rungs and easing 4's
twelfth, each named once to its module and its test, and every file named either there or
marked unbuilt."""

from __future__ import annotations

import json
import re
from importlib import import_module
from pathlib import Path

from lab import ladder

ROOT = Path(__file__).parents[2]
MODULE, TEST = r"lab/\w+\.py", r"tests/unit/test_lab_\w+\.py"
#: `n name: module, test`, either file followed by ` (unbuilt)`, then ` - what it still owes`
ENTRY = re.compile(rf" *(\d+) ([^:]+): ({MODULE})( \(unbuilt\))?, ({TEST})( \(unbuilt\))?( - .+)?")


def test_the_map_names_its_rungs_once_each_to_files_there_or_marked_unbuilt() -> None:
    doc = ladder.__doc__ or ""
    assert "THE RUNG MAP" in doc, "lab/ladder.py's docstring holds no rung map"
    paragraph = doc[doc.index("THE RUNG MAP") :].split("\n\n")[0]
    lines = [line for line in paragraph.splitlines() if line.lstrip()[:1].isdigit()]
    found = [ENTRY.fullmatch(line) for line in lines]
    unread = [line for line, entry in zip(lines, found, strict=True) if entry is None]
    assert not unread, f"not `n name: module, test`: {unread}"
    rungs = [entry.groups() for entry in found if entry is not None]
    assert [int(rung[0]) for rung in rungs] == list(range(1, 15)), "fourteen rungs, 1 to 14, once"
    for what, column in (("name", 1), ("test", 4)):
        seen = [rung[column] for rung in rungs]
        twice = sorted({one for one in seen if seen.count(one) > 1})
        assert not twice, f"two rungs with one {what}: {twice}"
    named = [pair for rung in rungs for pair in (rung[2:4], rung[4:6])]
    missing = sorted(
        {path for path, unbuilt in named if not unbuilt and not (ROOT / path).is_file()}
    )
    assert not missing, f"named as built and not there (build it, or mark it unbuilt): {missing}"


def test_a_row_is_built_exactly_when_its_module_declares_a_rung_and_the_count_reads_that() -> None:
    """A row owes `no RUNG` exactly when its module declares none, so the map says built or not
    as the code does; the count is the modules that declare one (`lab/folds.py` counted as built
    while declaring none until 22 November)."""
    doc = (ladder.__doc__ or "").split("THE RUNG MAP")[1].split("\n\n")[0]
    rows = re.findall(r"lab/(\w+)\.py, \S+( - no RUNG)?", doc)
    wrong = [m for m, owed in rows if hasattr(import_module(f"lab.{m}"), "RUNG") == bool(owed)]
    assert not wrong, f"the map's built-or-not disagrees with the module's RUNG: {wrong}"
    assert ladder.rungs_built() == (6, 14)  #: costs, ci, regimes, cpcv, liquidity, fit


def test_the_index_holds_offsets_only_and_a_cut_line_is_cut_off(tmp_path: Path) -> None:
    results = tmp_path / "r.jsonl"
    lines = [{"cell": ["a"], "n": 1}, {"cell": ["b"], "n": 2}, {"cell": ["a"], "n": 3}]
    body = b"".join(json.dumps(x).encode() + b"\n" for x in lines)
    results.write_bytes(body + b'{"cell": ["c"')
    kept = ladder.Kept(results)
    assert kept.end == len(body)
    assert [r["n"] for r in kept.rows()] == [3, 2] and kept.get(("c",)) is None
    assert all(isinstance(v, tuple) for v in kept.at.values())
    assert ladder.Kept(tmp_path / "none").end == 0
