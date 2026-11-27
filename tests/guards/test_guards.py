"""THE GUARDS. Every one of these fails loudly, and each is proven by breaking it.

These are the mechanical answers to the three things that wrecked the first desk:
sprawl (code in places nobody owns), bloat (code that only grows) and doom looping
(fixes on fixes, tests set aside, guards loosened to get green).

Nothing here reads the operator's machine, his data or a broker. The whole check runs
on a clean computer with no access to any of it, which is WHY a test cannot quietly
start depending on live state.
"""

from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PRODUCT_DIRS = ("desk", "lab")
LAB_DIR = "lab"

#: a file named after the session that wrote it: k1803_dqtomb, k205_box
SESSION_NAME = re.compile(r"k\d")

#: The complete document set. A file outside it fails, so "a summary of what I did"
#: has nowhere to land. The first desk reached 728 documents this way.
ALLOWED_DOCS = {
    "README.md",
    "CLAUDE.md",
    "CANON.md",
    "docs/SCENES.md",
    "docs/PLAN.md",
    "docs/STATUS.md",
    "docs/SCOREBOARD.md",
    "docs/ARCHITECTURE.md",
    "docs/DECISIONS.md",
    "docs/FAILURE_PATTERNS.md",
}


#: Assembled from pieces, never spelt out: a guard that names the thing it forbids
#: flags its own source, and the cure for that must never be a whole-file excuse.
MACHINE_MARKS = (
    "C:" + "\\",
    "C:" + "/",
    "/c/" + "Users",
    "PYTHON/" + "kestrel",
    "mt" + "rem",
)


def _product() -> list[Path]:
    return sorted(p for d in PRODUCT_DIRS for p in (ROOT / d).rglob("*.py"))


def _tests() -> list[Path]:
    return sorted((ROOT / "tests").rglob("*.py"))


def _lines(paths: list[Path]) -> int:
    return sum(len(p.read_bytes().splitlines()) for p in paths)


def _tracked() -> list[str]:
    out = subprocess.run(  # noqa: S603
        ["git", "ls-files"],  # noqa: S607
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in out.stdout.splitlines() if line]


def _budget() -> dict[str, Any]:
    data: dict[str, Any] = json.loads((ROOT / "BUDGET.json").read_text(encoding="utf-8"))
    return data


def _read(path: str, at: str) -> str:
    """A file of the tree: from the commit `at` when given, else from the working tree."""
    if not at:
        return (ROOT / path).read_text(encoding="utf-8")
    return subprocess.run(  # noqa: S603
        ["git", "show", f"{at}:{path}"],  # noqa: S607
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def _fragments(at: str) -> list[str]:
    """Every file in manifest/, at the commit `at` when given, untracked ones too if not."""
    if not at:
        return sorted(p.name for p in (ROOT / "manifest").iterdir())
    names = subprocess.run(  # noqa: S603
        ["git", "ls-tree", "--name-only", f"{at}:manifest"],  # noqa: S607
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return sorted(names.split())


def manifest(at: str = "") -> dict[str, Any]:
    """THE ONE LOADER of the manifest: manifest.toml (packages, lanes, the package markers)
    and one manifest/<lane>.toml per lane holding only that lane's [modules]. It returns them
    merged, with `owner`, each lane module's lane: the file it sits in. It fails loudly on a
    file in manifest/ not named for a lane, a lane without its file, a fragment holding more
    than [modules], a lane module in manifest.toml, and a module listed twice."""
    data: dict[str, Any] = tomllib.loads(_read("manifest.toml", at))
    lanes, modules = data["lanes"], dict(data["modules"])
    owner: dict[str, str] = {}
    loose = sorted(m for m in modules if Path(m).name != "__init__.py")
    assert not loose, f"manifest.toml lists lane modules {loose}: move each to its lane's file"
    names = _fragments(at)
    want = sorted(f"{lane}.toml" for lane in lanes)
    assert names == want, f"manifest/ holds {names}; exactly one file per lane: {want}"
    for name in names:
        lane, part = name.removesuffix(".toml"), tomllib.loads(_read(f"manifest/{name}", at))
        assert set(part) == {"modules"}, f"manifest/{name} holds {sorted(part)}; only [modules]"
        twice = sorted(set(part["modules"]) & set(modules))
        assert not twice, f"manifest/{name} lists {twice}, listed already: one home each"
        modules |= part["modules"]
        owner |= dict.fromkeys(part["modules"], lane)
    return {**data, "modules": modules, "owner": owner}


# ---------------------------------------------------------------- bloat


def test_the_tree_is_inside_this_phases_ceiling() -> None:
    """BLOAT. The ceiling was agreed before the phase started, so no build negotiates room."""
    spec = _budget()
    phase = str(spec["phase"])
    phases = spec["phases"]
    assert isinstance(phases, dict)
    assert phase in phases, f"BUDGET.json phase {phase!r} is not one of {sorted(phases)}"
    ceiling = phases[phase]

    core = [p for p in _product() if p.relative_to(ROOT).parts[0] != LAB_DIR]
    lab = [p for p in _product() if p.relative_to(ROOT).parts[0] == LAB_DIR]

    assert _lines(core) <= ceiling["product_lines"], (
        f"desk/ is {_lines(core)} lines, ceiling {ceiling['product_lines']} for {phase}. "
        "Delete something or ask the operator to raise the ceiling on the pull request."
    )
    assert (
        _lines(lab) <= ceiling["lab_lines"]
    ), f"lab/ is {_lines(lab)} lines, ceiling {ceiling['lab_lines']} for {phase}."


def test_no_file_is_a_monolith() -> None:
    cap = int(_budget()["max_lines_per_file"])
    too_big = {
        str(p.relative_to(ROOT)): len(p.read_bytes().splitlines())
        for p in _product() + _tests()
        if len(p.read_bytes().splitlines()) > cap
    }
    assert not too_big, f"over {cap} lines: {too_big}. Split it; one file, one job."


def test_no_function_is_a_monolith() -> None:
    cap = int(_budget()["max_lines_per_function"])
    long_ones: dict[str, int] = {}
    for path in _product():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                span = (node.end_lineno or node.lineno) - node.lineno + 1
                if span > cap:
                    long_ones[f"{path.relative_to(ROOT)}::{node.name}"] = span
    assert not long_ones, f"functions over {cap} lines: {long_ones}"


def test_tests_never_outgrow_the_product() -> None:
    """The first desk had 400,000 lines of test against 438,000 of product, and 2,221
    of those tests were set aside as known failures. Tests are code we carry too.

    What grows one test per bug is the unit tests, so they are what is held to the
    product, from the first line. The guards and the seven scenes are fixed in number
    and change only with the operator's approval. Counting them too turned this guard
    red the moment the scenes were written before their code, as the canon requires.
    Ruled by the operator, 13 November 2026 (docs/DECISIONS.md)."""
    ratio = float(_budget()["unit_test_lines_per_product_line"])  #: 1.5, his ruling, 13 Nov
    product, unit = _lines(_product()), _lines(sorted((ROOT / "tests" / "unit").rglob("*.py")))
    assert unit <= ratio * product, f"unit tests {unit} lines > {ratio} x product {product}"


def test_the_rulebooks_stay_short() -> None:
    """BLOAT, in the rules. CLAUDE.md and CANON.md each promise a limit, and the first desk
    shows what a promise in prose is worth: 56 lessons and 64 deny rules that nobody read.
    A new rule replaces or merges an old one, or becomes a check like this one."""
    caps: dict[str, int] = _budget()["max_lines_per_rulebook"]
    assert set(caps) == {
        "CLAUDE.md",
        "CANON.md",
        "docs/FAILURE_PATTERNS.md",
    }, f"the rulebooks capped: {sorted(caps)}"
    over = {
        name: lines
        for name, cap in caps.items()
        if (lines := len((ROOT / name).read_bytes().splitlines())) > cap
    }
    assert not over, (
        f"over their limits {caps}: {over}. Merge a rule into another, or make it a check; "
        "never delete one to make room."
    )


# ---------------------------------------------------------------- sprawl


def test_every_module_is_registered_in_the__manifest() -> None:
    """SPRAWL. Register the module, then write it. 'No new file without a search and a
    removal' was prose on the first desk; here the check refuses the file."""
    listed = set(manifest()["modules"])
    actual = {str(p.relative_to(ROOT)).replace("\\", "/") for p in _product()}
    assert actual - listed == set(), (
        f"not in the manifest: {sorted(actual - listed)}. "
        "Add it and the one thing it owns to manifest/<lane>.toml, in the same change."
    )
    assert listed - actual == set(), f"in the manifest but absent: {sorted(listed - actual)}"


#: a fragment's name: a module cut by size, not by what it owns (failure pattern 6)
FRAGMENT = re.compile(r"_(?:parts?|more|extra|rest|bits|helpers?|misc|aux)\d*$|[a-z]\d$")


def _git_out(*args: str) -> str:
    return subprocess.run(  # noqa: S603
        ["git", *args],  # noqa: S607
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def test_every_desk_module_has_one_owner_and_one_job() -> None:
    """SPRAWL, held by ownership, not a file count (his 'Yes, all of it', 27 Nov). Each desk/
    module is a row of one lane's manifest file, saying the one thing it owns; a module two
    lanes list fails the loader."""
    spec = manifest()
    unowned = sorted(
        name
        for name in (str(p.relative_to(ROOT)).replace("\\", "/") for p in _product())
        if name.startswith("desk/")
        and Path(name).name != "__init__.py"
        and not (spec["owner"].get(name) and str(spec["modules"].get(name, "")).strip())
    )
    assert not unowned, (
        f"desk/ modules with no lane or no stated job: {unowned}. Each is a row of "
        'manifest/<lane>.toml: "desk/x.py" = "the one thing it owns".'
    )


def test_no_fragment_names_are_added() -> None:
    """SPRAWL, by name. A module split off because its parent is full (`book_parts.py`,
    `orders_parts2.py`) owns no concept of its own. Those on main may only fall; a change may
    add none: name the new module for what it owns."""
    base = _git_out("merge-base", "HEAD", "origin/main").strip()
    was = set(_git_out("ls-tree", "-r", "--name-only", base, "--", *PRODUCT_DIRS).split())
    added = sorted(
        name
        for name in (str(p.relative_to(ROOT)).replace("\\", "/") for p in _product())
        if FRAGMENT.search(Path(name).stem) and name not in was
    )
    assert not added, (
        f"fragment names added: {added}. Name a module for the one thing it owns, never its "
        "parent's name plus a suffix (failure pattern 6)."
    )


def _imports(path: Path) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            names |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and not node.level and node.module:
            names.add(node.module.split(".")[0])
    return names


def test_the_wall_holds() -> None:
    """SPRAWL. desk/ sees the standard library and nothing else; it may never import
    lab/. This is the exact leak that absorbed the first desk's clean core back into
    352,000 lines: its day runner was put OUTSIDE the walled folder."""
    packages = manifest()["packages"]
    assert isinstance(packages, dict)
    breaches: dict[str, set[str]] = {}
    for path in _product():
        package = path.relative_to(ROOT).parts[0]
        rules = packages[package]
        allowed = set(sys.stdlib_module_names) | {package}
        if "desk" in rules["may_import"]:
            allowed.add("desk")
        allowed |= set(rules["allowed_third_party"])
        outside = _imports(path) - allowed
        if outside:
            breaches[str(path.relative_to(ROOT))] = outside
    assert not breaches, (
        f"imports outside the wall: {breaches}. Either it belongs inside, or the "
        "manifest's allowed_third_party needs the operator's approval."
    )


def test_no_versioned_copies_and_no_session_named_files() -> None:
    """SPRAWL. _v2, _new, _fixed, backup, and files named after the session that wrote
    them. The first desk carried 1,218 test files named test_k<number>."""
    bad = [
        name
        for name in _tracked()
        if any(
            mark in Path(name).stem.lower()
            for mark in ("_v2", "_v3", "_new", "_old", "_fixed", "_backup", "_copy", "-copy")
        )
        or SESSION_NAME.match(Path(name).stem.lower())
    ]
    assert not bad, f"versioned or session-named: {bad}. Edit the original; git is the archive."


def _lane_docs() -> set[str]:
    """One document per lane the manifest knows, for its own decisions: docs/lanes/<lane>.md."""
    return {f"docs/lanes/{lane}.md" for lane in manifest()["lanes"]}


def test_the_document_set_is_fixed() -> None:
    allowed = ALLOWED_DOCS | _lane_docs()
    docs = {n for n in _tracked() if n.endswith(".md") and not n.startswith("docs/archive/")}
    assert docs <= allowed, (
        f"documents outside the fixed set: {sorted(docs - allowed)}. "
        "Findings go in docs/STATUS.md, decisions in docs/DECISIONS.md or the lane's own."
    )


def test_each_lane_document_is_read_whole() -> None:
    """BLOAT, in the documents. A lane's decisions are read by every session of the lane;
    past a size nobody reads them whole, and a decision nobody reads is not one. Full, the
    scribe folds the oldest settled entries into a summary; git keeps every word."""
    cap = int(_budget()["max_lines_per_lane_doc"])
    over = {
        name: lines
        for name in sorted(_lane_docs())
        if (path := ROOT / name).exists() and (lines := len(path.read_bytes().splitlines())) > cap
    }
    assert not over, f"lane documents over {cap} lines: {over}. Fold the oldest entries."


def test_no_data_is_committed() -> None:
    """This repository is PUBLIC. Prices, positions and account records never enter it."""
    leaked = [
        n
        for n in _tracked()
        if (n.startswith("data/") or n.endswith((".parquet", ".csv")))
        and not n.startswith("tests/fixtures/")
    ]
    assert not leaked, f"data in a public repository: {leaked}"


# ---------------------------------------------------------------- doom loops


def test_no_test_is_skipped_or_expected_to_fail() -> None:
    """DOOM LOOP. There is no known-failing list. A red test blocks everything, which is
    the only reason a red test ever gets fixed. The first desk set aside 2,221 of them."""
    offenders: dict[str, list[str]] = {}
    for path in _tests():
        text = path.read_text(encoding="utf-8")
        hits = [
            mark
            for mark in ("mark." + "skip", "mark." + "xfail", "skip" + "if", "pytest." + "skip(")
            if mark in text
        ]
        if hits:
            offenders[str(path.relative_to(ROOT))] = hits
    assert not offenders, f"set-aside tests: {offenders}"


def test_nothing_reaches_the_operators_machine() -> None:
    """DOOM LOOP. A test that reads live state is honestly green and proves nothing, and
    it is why the first desk's checks could not run anywhere but his PC."""
    offenders: dict[str, list[str]] = {}
    for path in _tests() + _product():
        text = path.read_text(encoding="utf-8")
        hits = [mark for mark in MACHINE_MARKS if mark in text]
        if hits:
            offenders[str(path.relative_to(ROOT))] = hits
    assert not offenders, f"machine-specific paths: {offenders}"


def test_live_trading_cannot_be_reached() -> None:
    """The broker's live port is 4001 and its paper port is 4002. Nothing in this tree
    may name 4001 only on a line that also says NEVER, in capitals. THIS GUARD WAS
    MISSED THE FIRST TIME IT WAS DRIVEN: it excused any file holding the word never
    anywhere, and the core package says it in ordinary prose. A whole-file escape
    hatch is not a guard."""
    offenders: dict[str, list[int]] = {}
    for path in _product():
        text = path.read_text(encoding="utf-8")
        bad = [
            number
            for number, line in enumerate(text.splitlines(), 1)
            if "4001" in line and "NEVER" not in line
        ]
        if bad:
            offenders[str(path.relative_to(ROOT))] = bad
    assert not offenders, f"the live port is named without a refusal: {offenders}"
