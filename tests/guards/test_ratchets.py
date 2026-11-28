"""THE RATCHETS. A number about the code that may fall and never rise, measured against
main on every change, so no session has to keep a count up to date by hand:

- the public definitions in `desk/` and `lab/` with no docstring. A session reading a
  module it did not write learns what a function is for from its docstring, or not at all.
- the suppressions (a lint `noqa` or a typing `type: ignore`) in tracked Python, and those
  of them that give no reason on their line after the codes they name. Each is a rule set
  aside; one with no reason cannot be judged by the next session to read it.
- the whole-file reads in `desk/` and `lab/`: `read_bytes()`, `read_text()`, `readlines()`
  and a bare `read()`. EPON's results file grew to 1.2 GB and the ladder read and parsed
  all of it on every start: 12.8 GB held, the machine swapping, nothing judged for nine
  hours (21 November 2026). A file that grows is read a line at a time. A file that
  cannot grow (a source file, a small marker or config) says why on the same line:
  `# bounded: <why>`; a mark with no reason after it counts.
- the file replaces in `desk/` and `lab/`: `path.replace(new)`, `path.rename(new)`,
  `os.replace` and `os.rename`. On Windows a file replaced while another process reads it
  refuses ("Access denied"): the store's daily files, a grid file and the runner's list on
  16 November (failure pattern 19). Each shared file gets one locked writer; until then a
  new writer reuses an old one, never adds a replace of its own.

Approved in the after-first-light queue, 14 November 2026 (docs/DECISIONS.md); the
suppression ratchet, 15 November 2026 (docs/DECISIONS.md).
"""

from __future__ import annotations

import ast
import io
import re
import subprocess
import tokenize
from collections.abc import Callable, Sized
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


#: what swaps one file for another: a path's replace or rename, and the os module's
MOVES = frozenset({"replace", "rename"})


def _replaces(source: str) -> list[tuple[int, int]]:
    """Each call that replaces a file, by (line, column): `x.replace(y)` or `x.rename(y)` with
    one argument (a text's replace takes two, a time's takes names), or `os.replace(a, b)`."""
    return sorted(
        (node.lineno, node.col_offset)
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in MOVES
        and not node.keywords
        and (
            len(node.args) == 1
            or (isinstance(node.func.value, ast.Name) and node.func.value.id == "os")
        )
    )


def test_file_replaces_never_rise() -> None:
    """A FILE REPLACED WHILE IT IS READ (failure pattern 19; design L16). Windows refuses the
    swap while any reader holds the file, so each new replace is a new place for a live job to
    fail. A change may route a writer through another's; it may not add a replace."""
    before, now = _count(_base(), _replaces), _count_tree(_replaces)
    grown = {p: (before.get(p, 0), n) for p, n in now.items() if n > before.get(p, 0)}
    assert sum(now.values()) <= sum(before.values()), (
        f"file replaces rise from {sum(before.values())} on main to {sum(now.values())}; "
        f"files that grew (main, now): {grown}. Write through the file's existing writer."
    )


#: the smallest function body, in syntax nodes, whose copy counts as a duplicate
DUPLICATE_NODES = 25
#: where a name defined in desk/ or lab/ may be used
USED_IN = ("desk", "lab", "tests", "check.py")


def _sources(ref: str | None, dirs: tuple[str, ...] = ROOT_DIRS) -> dict[str, str]:
    """Each Python file under dirs, at a commit, or in the working tree when ref is None."""
    if ref is not None:
        listed = _git("ls-tree", "-r", "--name-only", ref, "--", *dirs).splitlines()
        return {p: _git("show", f"{ref}:{p}") for p in listed if p.endswith(".py")}
    tracked = _git("ls-files", "--cached", "--others", "--exclude-standard", "--", *dirs)
    paths = [ROOT / p for p in tracked.splitlines() if p.endswith(".py")]
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


#: a ticked box of docs/PLAN.md, up to the next box or heading; its id from its braces
TICKED = re.compile(r"^- \[x\] .*?(?=^- \[[ x]\] |^#|\Z)", re.MULTILINE | re.DOTALL)
BOX_ID = re.compile(r"\{id: ([a-z0-9-]+)")


def _ticked_with_remains(plan: str) -> list[str]:
    """The ticked boxes whose note still says what remains: a tick its check did not earn."""
    return [
        m.group(1) if (m := BOX_ID.search(box)) else box[:60]
        for box in TICKED.findall(plan)
        if "Remains:" in box
    ]


def test_ticked_boxes_that_say_remains_never_rise() -> None:
    """PROGRESS COUNTED IN ACTIVITY (failure pattern 3): a box ticked while its note says what
    remains (money-simcity-withdrawn-day, 26 November: 'Remains: read the next deep run's
    verdict', and the deep run never gave one) is counted as progress before its check passed.
    A change may untick one or finish what remains; it may not tick another."""
    _never_rise(
        "ticked boxes in docs/PLAN.md whose note says Remains:",
        _ticked_with_remains(_git("show", f"{_base()}:docs/PLAN.md")),
        _ticked_with_remains((ROOT / "docs" / "PLAN.md").read_text(encoding="utf-8")),
        "Leave the box unticked until its check passes, or finish what remains and drop the line.",
    )
