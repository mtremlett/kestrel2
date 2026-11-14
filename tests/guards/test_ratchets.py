"""THE RATCHETS. A number about the code that may fall and never rise, measured against
main on every change, so no session has to keep a count up to date by hand:

- the public definitions in `desk/` and `lab/` with no docstring. A session reading a
  module it did not write learns what a function is for from its docstring, or not at all.

Approved in the after-first-light queue, 14 November 2026 (docs/DECISIONS.md).
"""

from __future__ import annotations

import ast
import subprocess
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


def _count(ref: str) -> dict[str, int]:
    """Each product file at a commit, with its undocumented public definitions."""
    files = _git("ls-tree", "-r", "--name-only", ref, "--", *ROOT_DIRS).splitlines()
    return {
        path: len(_undocumented(_git("show", f"{ref}:{path}")))
        for path in files
        if path.endswith(".py")
    }


def _count_tree() -> dict[str, int]:
    """Each product file in the working tree, as the change stands."""
    files = _git("ls-files", "--cached", "--others", "--exclude-standard", "--", *ROOT_DIRS)
    paths = [ROOT / p for p in files.splitlines() if p.endswith(".py")]
    return {
        p.relative_to(ROOT).as_posix(): len(_undocumented(p.read_text(encoding="utf-8")))
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
