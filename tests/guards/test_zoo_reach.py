"""EVERY DESK RULE IS REACHED (G27, coordinator 96, 22 Nov): a module of desk/ that declares a
rule is either found by the ladder's rulebook (it is named eponymous_*, which lab/rulebook.py
globs) or imported by desk/intraday.py, the zoo's paper path. A rule nothing reaches is code
that never trades, even as a machinery test: desk/grimes.py landed (#1693, #1694) so."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ZOO = ROOT / "desk" / "intraday.py"
DECLARES = "Decl" + "ared"  #: built from pieces, so this file never matches itself


def _imports(path: Path) -> set[str]:
    """The desk modules a file imports, by their short name."""
    names = set[str]()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.ImportFrom) and node.module == "desk":
            names |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom) and (node.module or "").startswith("desk."):
            names.add(node.module.removeprefix("desk."))  # type: ignore[union-attr]
    return names


def _declares(path: Path) -> bool:
    """True when the module imports the strategy's rule declaration."""
    return any(
        isinstance(node, ast.ImportFrom)
        and node.module == "desk.strategy"
        and any(a.name == DECLARES for a in node.names)
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
    )


def test_every_desk_rule_is_reached_by_the_rulebook_or_the_zoo() -> None:
    zoo = _imports(ZOO)
    strays = [
        path.relative_to(ROOT).as_posix()
        for path in sorted((ROOT / "desk").glob("*.py"))
        if _declares(path) and not path.stem.startswith("eponymous_") and path.stem not in zoo
    ]
    assert not strays, f"rules nothing reaches (wire them into desk/intraday.py's zoo): {strays}"
