"""The rung registry: a `rung_*` module that declares its rung is found by its name and judged
by the ladder with no edit of `lab/ladder.py`; one that declares none is named unrun."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from test_lab_ladder import EDGE, ISF, NOISE, VUSA, _door, _rows, _set

from lab import ladder, rung

PLANTED = """
from lab.rung import Answer, Rung


def judge(first):
    return Answer.PASS, f"planted: {len(first.trades)} trades"


RUNG = Rung("planted", "any trades at all", judge)
"""


def _scratch(root: Path, extra: dict[str, str], name: str) -> str:
    pkg = root / name
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    for module, text in extra.items():
        (pkg / f"{module}.py").write_text(text)
    sys.path.insert(0, str(root))
    return name


def test_the_ladders_rows_are_those_the_verdict_gives_while_no_module_declares_a_rung(
    tmp_path: Path,
) -> None:
    declared, waiting = rung.found()
    assert [one.name for one in declared] == ["ci", "costs", "cpcv"] and "lab.rung_beta" in waiting
    ladder.run(tmp_path, _door({VUSA: EDGE, ISF: NOISE}), {}, _set(VUSA, ISF))
    assert all(not ({"planted"} & set(row["rungs"])) for row in _rows(tmp_path))
    assert all(set(row["rungs"]) >= {"first", "market", "folds"} for row in _rows(tmp_path))


def test_a_planted_rung_module_is_found_and_judged_with_no_edit_of_the_ladder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plain = tmp_path / "plain"
    ladder.run(plain, _door({VUSA: EDGE, ISF: NOISE}), {}, _set(VUSA))
    package = _scratch(tmp_path, {"rung_planted": PLANTED, "rung_waits": "X = 1\n"}, "planted_pkg")
    monkeypatch.setattr(ladder, "RUNGS", package)
    declared, waiting = rung.found(package)
    assert [one.name for one in declared] == ["planted"] and waiting == (f"{package}.rung_waits",)
    home = tmp_path / "planted"
    ladder.run(home, _door({VUSA: EDGE, ISF: NOISE}), {}, _set(VUSA))
    (was,), (now,) = _rows(plain), _rows(home)
    assert now["rungs"]["planted"][0] == "PASS" and now["rungs"]["planted"][1].startswith(
        "planted:"
    )
    assert {k: v for k, v in now["rungs"].items() if k != "planted"} == {
        k: v
        for k, v in was["rungs"].items()
        if k not in ("costs", "ci", "cpcv")  #: the real package's own rung
    }
    assert now["key"] != was["key"], "a declared rung is part of what keeps a cell"
    assert now["answer"] == was["answer"] and now["trials"] == was["trials"]
    assert json.loads(json.dumps(now)) == now


def test_two_rungs_of_one_name_or_a_rung_that_is_not_one_are_refused(
    tmp_path: Path,
) -> None:
    twice = _scratch(tmp_path, {"rung_a": PLANTED, "rung_b": PLANTED}, "twice_pkg")
    with pytest.raises(ValueError, match="same rung name"):
        rung.found(twice)
    other = tmp_path / "other"
    other.mkdir()
    bad = _scratch(other, {"rung_c": "RUNG = 3\n"}, "bad_pkg")
    with pytest.raises(TypeError, match="not a rung.Rung"):
        rung.found(bad)
