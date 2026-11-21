"""THE RATCHETS. A number about the code that may fall and never rise, measured against
main on every change, so no session has to keep a count up to date by hand:

- the public definitions in `desk/` and `lab/` with no docstring. A session reading a
  module it did not write learns what a function is for from its docstring, or not at all.
- the whole-file reads in `desk/` and `lab/`: `read_bytes()`, `read_text()`, `readlines()`
  and a bare `read()`. EPON's results file grew to 1.2 GB and the ladder read and parsed
  all of it on every start: 12.8 GB held, the machine swapping, nothing judged for nine
  hours (21 November 2026). A file that grows is read a line at a time. A file that
  cannot grow (a source file, a small marker or config) says why on the same line:
  `# bounded: <why>`; a mark with no reason after it counts.

Approved in the after-first-light queue, 14 November 2026 (docs/DECISIONS.md).
"""

from __future__ import annotations

import ast
import re
import subprocess
from collections.abc import Callable, Sized
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROOT_DIRS = ("desk", "lab")


def _git(*args: str) -> str:
    return subprocess.run(  # noqa: S603
        ["git", *args],  # noqa: S607
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    ).stdout


def _base() -> str:
    """Main's commit this change starts from. No main to compare with is a failure."""
    return _git("merge-base", "HEAD", "origin/main").strip()


#: what a top-level statement holds: statements, an except's body, a match's cases
BLOCK = (ast.stmt, ast.excepthandler, ast.match_case)


def _undocumented(source: str) -> list[str]:
    """The public functions, classes and methods of public classes with no docstring,
    those under a top-level `if`, `try` or `with` too; never one inside a function."""
    names: list[str] = []
    todo: list[ast.AST] = list(ast.parse(source).body)
    while todo:
        node = todo.pop()
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            todo += [c for c in ast.iter_child_nodes(node) if isinstance(c, BLOCK)]
            continue
        if node.name.startswith("_"):
            continue
        if ast.get_docstring(node) is None:
            names.append(node.name)
        if isinstance(node, ast.ClassDef):
            todo += node.body
    return names


#: what a ratchet counts in one file's source
Measure = Callable[[str], Sized]

#: what reads a whole file into memory at once
WHOLE = frozenset({"read_bytes", "read_text", "readlines"})
#: the same-line reason that a file cannot grow; it must be followed by words
BOUNDED = re.compile(r"#\s*bounded:\s*\S+\s+\S+")


def _whole_reads(source: str) -> list[tuple[int, int]]:
    """Each call that reads a whole file at once, by (line, column), with no reason on
    any of its lines that the file is bounded."""
    lines = source.replace("
", "
").replace("", "
").split("
")
    return sorted(
        (node.lineno, node.col_offset)
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and (node.func.attr in WHOLE or (node.func.attr == "read" and not node.args))
        and not any(
            BOUNDED.search(lines[n - 1])
            for n in range(node.lineno, (node.end_lineno or node.lineno) + 1)
        )
    )


def _count(ref: str, measure: Measure = _undocumented) -> dict[str, int]:
    """Each product file at a commit, with how many things `measure` finds in it."""
    files = _git("ls-tree", "-r", "--name-only", ref, "--", *ROOT_DIRS).splitlines()
    return {
        path: len(measure(_git("show", f"{ref}:{path}"))) for path in files if path.endswith(".py")
    }


def _count_tree(measure: Measure = _undocumented) -> dict[str, int]:
    """Each product file in the working tree, as the change stands."""
    files = _git("ls-files", "--cached", "--others", "--exclude-standard", "--", *ROOT_DIRS)
    paths = [ROOT / p for p in files.splitlines() if p.endswith(".py")]
    return {
        p.relative_to(ROOT).as_posix(): len(measure(p.read_text(encoding="utf-8")))
        for p in paths
        if p.exists()  # a file this change deletes counts nothing
    }


def test_undocumented_public_definitions_never_rise() -> None:
    """BLOAT, of a kind no line count sees: code nobody can read without reading all of
    it. A change may document what it touches; it may not add to what is undocumented."""
    before, now = _count(_base()), _count_tree()
    grown = {p: (before.get(p, 0), n) for p, n in now.items() if n > before.get(p, 0)}
    assert sum(now.values()) <= sum(before.values()), (
        f"undocumented public definitions rise from {sum(before.values())} on main to "
        f"{sum(now.values())}; files that grew (main, now): {grown}. Give each new public "
        "function, class and method a docstring saying what it is for."
    )


def test_whole_file_reads_never_rise() -> None:
    """BLOAT, of memory: a file read whole is fine at a kilobyte and fatal at a gigabyte,
    and nothing notices the day it crosses. A change may stream what it touches; it may
    not add a whole-file read of a file that can grow."""
    before, now = _count(_base(), _whole_reads), _count_tree(_whole_reads)
    grown = {p: (before.get(p, 0), n) for p, n in now.items() if n > before.get(p, 0)}
    assert sum(now.values()) <= sum(before.values()), (
        f"whole-file reads rise from {sum(before.values())} on main to {sum(now.values())}; "
        f"files that grew (main, now): {grown}. Read a file that grows a line at a time; "
        "for one that cannot grow, say why on the same line: `# bounded: <why>`."
    )
