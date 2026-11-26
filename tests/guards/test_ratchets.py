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
    lines = source.replace("\r\n", "\n").replace("\r", "\n").split("\n")
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


#: the smallest function body, in syntax nodes, whose copy counts as a duplicate
DUPLICATE_NODES = 25
#: where a name defined in desk/ or lab/ may be used
USED_IN = ("desk", "lab", "tests", "check.py")


def _sources(ref: str | None, dirs: tuple[str, ...] = ROOT_DIRS) -> dict[str, str]:
    """Each Python file under dirs, at a commit, or in the working tree when ref is None."""
    if ref is not None:
        files = _git("ls-tree", "-r", "--name-only", ref, "--", *dirs).splitlines()
        return {p: _git("show", f"{ref}:{p}") for p in files if p.endswith(".py")}
    files = _git("ls-files", "--cached", "--others", "--exclude-standard", "--", *dirs)
    paths = [ROOT / p for p in files.splitlines() if p.endswith(".py")]
    return {
        p.relative_to(ROOT).as_posix(): p.read_text(encoding="utf-8") for p in paths if p.exists()
    }


def _duplicates(sources: dict[str, str]) -> list[str]:
    """Each function whose body, docstring aside, is node for node another's: the second
    and later copies, as path:name. Names, line numbers and the docstring never count."""
    seen: dict[str, str] = {}
    copies: list[str] = []
    for path, source in sorted(sources.items()):
        for node in ast.walk(ast.parse(source)):
            if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            body = node.body[1:] if ast.get_docstring(node) is not None else node.body
            if sum(1 for stmt in body for _ in ast.walk(stmt)) < DUPLICATE_NODES:
                continue
            key = "\n".join(ast.dump(s, annotate_fields=False) for s in body)
            if key in seen:
                copies.append(f"{path}:{node.name} (a copy of {seen[key]})")
            else:
                seen[key] = f"{path}:{node.name}"
    return copies


def _top_names(source: str) -> list[str]:
    """The names a module defines at its top level: functions, classes and assignments."""
    names: list[str] = []
    for node in ast.parse(source).body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            names.append(node.name)
        elif isinstance(node, ast.Assign | ast.AnnAssign):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            names += [t.id for t in targets if isinstance(t, ast.Name)]
    return [n for n in names if not (n.startswith("__") and n.endswith("__"))]


def _unused(ref: str | None) -> list[str]:
    """Each top-level name in desk/ and lab/ written nowhere but its own definition, in
    desk/, lab/, tests/ or check.py: code that nothing runs, as path:name."""
    product = _sources(ref)
    text = "\n".join(_sources(ref, USED_IN).values())
    words: dict[str, int] = {}
    for word in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text):
        words[word] = words.get(word, 0) + 1
    return [
        f"{p}:{n}"
        for p, s in sorted(product.items())
        for n in _top_names(s)
        if words.get(n, 0) <= 1
    ]


def _two_homes(sources: dict[str, str]) -> list[str]:
    """Each home past the first of an UPPER_CASE constant assigned at the top level of two or
    more modules: one fact with two homes (failure pattern 8), as name: path. A third home
    counts again."""
    homes: dict[str, list[str]] = {}
    for path, source in sorted(sources.items()):
        for name in set(_top_names(source)):
            if name.isupper() and len(name) > 1:
                homes.setdefault(name, []).append(path)
    return [f"{n}: {p}" for n, ps in sorted(homes.items()) for p in ps[1:]]


def _never_rise(what: str, before: list[str], now: list[str], fix: str) -> None:
    new = sorted(set(now) - set(before))
    assert len(now) <= len(
        before
    ), f"{what} rise from {len(before)} on main to {len(now)}; new: {new[:10]}. {fix}"


def test_duplicate_function_bodies_never_rise() -> None:
    """BLOAT, the copy: the same body written twice drifts apart the first time one is
    fixed. A change may merge copies; it may not add one."""
    _never_rise(
        "duplicate function bodies",
        _duplicates(_sources(_base())),
        _duplicates(_sources(None)),
        "Call the one that exists instead of writing it again.",
    )


def test_unused_definitions_never_rise() -> None:
    """BLOAT, the dead: a definition nothing uses still has to be read, kept and moved. A
    change may delete dead code; it may not add a definition that nothing uses."""
    _never_rise(
        "top-level definitions nothing uses",
        _unused(_base()),
        _unused(None),
        "Use it, or delete it: git is the archive.",
    )


def test_constants_with_two_homes_never_rise() -> None:
    """SPRAWL, the second home (failure pattern 8): the same constant name assigned in two
    modules, which then disagree. A change may merge homes; it may not add one."""
    _never_rise(
        "constants defined in two modules",
        _two_homes(_sources(_base())),
        _two_homes(_sources(None)),
        "Import the constant from the one module that owns it (manifest.toml).",
    )
