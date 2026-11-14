"""Every eponymous module names its rules in EPONYMOUS, so the lab can find them."""

from __future__ import annotations

import importlib
from pathlib import Path

DESK = Path(__file__).resolve().parents[2] / "desk"
MODULES = sorted(p.stem for p in DESK.glob("eponymous_*.py"))


def test_every_eponymous_module_declares_unique_runnable_rules() -> None:
    names: list[str] = []
    for module in MODULES:
        mapping = getattr(importlib.import_module(f"desk.{module}"), "EPONYMOUS", None)
        assert mapping, f"desk.{module} declares no EPONYMOUS"
        for name, rule in mapping.items():
            assert hasattr(rule, "declared") and hasattr(rule, "step"), f"{module}: {name}"
            names.append(name)
    assert len(names) == len(set(names)), "a rule name is used twice"
