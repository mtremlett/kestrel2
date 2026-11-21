"""THE RATCHETS. A number about the code that may fall and never rise, measured against
main on every change, so no session has to keep a count up to date by hand:

- the public definitions in `desk/` and `lab/` with no docstring. A session reading a
  module it did not write learns what a function is for from its docstring, or not at all.
- the suppressions (a lint `noqa` or a typing `type: ignore`) in tracked Python, and those
  of them that give no reason on their line after the codes they name. Each is a rule set
  aside; one with no reason cannot be judged by the next session to read it.

Approved in the after-first-light queue, 14 November 2026 (docs/DECISIONS.md); the
suppression ratchet, 15 November 2026 (docs/DECISIONS.md).
"""

from __future__ import annotations

import ast
import io
import re
import subprocess
import tokenize
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROOT_DIRS = ("desk", "lab")


def _git(*args: str, ok: tuple[int, ...] = (0,)) -> str:
    """Git's answer; any exit code not in `ok` is a failure (git grep answers 1 for none)."""
    done = subprocess.run(  # noqa: S603
        ["git", *args],  # noqa: S607
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert done.returncode in ok, f"git {' '.join(args)} failed: {done.stderr}"
    return done.stdout


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


#: a suppression in a comment and the codes it names: `noqa: S603`, `type: ignore[misc]`
SUPPRESSION = re.compile(
    r"#\s*(?:noqa|type:\s*ignore)\b(?::\s*[A-Z]+\d+(?:\s*,\s*[A-Z]+\d+)*|\[[^\]]*\])?"
)
#: a reason is words, not punctuation: `- a repeatable draw, not a secret`
REASON = re.compile(r"[A-Za-z]{2,}")


def _suppressions(source: str) -> tuple[int, int]:
    """A file's suppressions, and how many of them give no reason after their codes. Only
    comments count, so a string or a docstring naming one is not one."""
    total = bare = 0
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type != tokenize.COMMENT:
            continue
        for hit in SUPPRESSION.finditer(token.string):
            total += 1
            bare += not REASON.search(SUPPRESSION.sub("", token.string[hit.end() :]))
    return total, bare


def _suppressed(ref: str | None) -> dict[str, tuple[int, int]]:
    """Each tracked Python file with a suppression, at a commit, or in the working tree
    as the change stands when `ref` is None."""
    if ref is None:
        listed = _git("ls-files", "--cached", "--others", "--exclude-standard", "--", "*.py")
        texts = {
            p: (ROOT / p).read_text(encoding="utf-8")
            for p in listed.splitlines()
            if (ROOT / p).exists()  # a file this change deletes counts nothing
        }
    else:  # only the files that name one at all, so main is not read whole on every run
        hits = _git("grep", "-l", "-E", "noqa|type: *ignore", ref, "--", "*.py", ok=(0, 1))
        paths = [line.split(":", 1)[1] for line in hits.splitlines()]
        texts = {p: _git("show", f"{ref}:{p}") for p in paths}
    counts = {p: _suppressions(text) for p, text in texts.items()}
    return {p: n for p, n in counts.items() if n[0]}


def test_suppressions_never_rise_and_unreasoned_ones_only_fall() -> None:
    """DOOM LOOP, the quiet kind: a check made to pass by telling it to look away. A change
    may remove a suppression or give one its reason; it may not add one, and a new one
    in place of an old needs its reason on the same line, after its codes."""
    before, now = _suppressed(_base()), _suppressed(None)
    for i, kind in ((0, "suppressions"), (1, "suppressions with no reason after their codes")):
        was, is_ = sum(n[i] for n in before.values()), sum(n[i] for n in now.values())
        grown = {
            p: (before.get(p, (0, 0))[i], n[i])
            for p, n in now.items()
            if n[i] > before.get(p, (0, 0))[i]
        }
        assert is_ <= was, (
            f"{kind} rise from {was} on main to {is_}; files that grew (main, now): {grown}. "
            "Fix the code the linter or the type checker named instead of silencing it; if "
            "it truly must stay, write why on the same line, after the codes."
        )
