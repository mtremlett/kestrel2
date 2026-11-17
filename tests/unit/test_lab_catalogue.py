"""Spec parity: every strategy of the spec book (`lab/catalogue.toml`) decides, on every day of
every fixture series, exactly as the Python rule of the same name in `desk/eponymous_*.py`."""

from __future__ import annotations

import random
import tomllib
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from desk.store import Bar
from desk.strategy import _run
from lab import rulebook
from lab.spec import Spec, SpecRule

BOOK = tomllib.loads((Path(__file__).parents[2] / "lab" / "catalogue.toml").read_text("utf-8"))
RULES = rulebook.eponymous()


def _bars(seed: int, days: int = 1500) -> tuple[Bar, ...]:
    """A seeded wandering line with trends and quiet spells, so buys and sells both occur."""
    rng, close, drift, made = random.Random(seed), 100.0, 0.0, []  # noqa: S311 - a test draw
    crowd = random.Random(seed + 99)  # noqa: S311 - a test draw: the volume, apart so prices stay
    for n in range(days):
        drift = rng.uniform(-0.01, 0.01) if n % 60 == 0 else drift
        close *= 1 + drift + rng.gauss(0, 0.01)
        top, bottom = close * (1 + rng.random() * 0.01), close * (1 - rng.random() * 0.01)
        c, h, lo = (Decimal(f"{x:.4f}") for x in (close, top, bottom))
        made.append(
            Bar(date(2010, 1, 1) + timedelta(n), c, h, lo, c, int(1000 * crowd.uniform(0.5, 2.5)))
        )
    return tuple(made)


@pytest.mark.parametrize("name", sorted(BOOK))
def test_each_spec_decides_as_its_python_rule_on_every_day(name: str) -> None:
    assert name in RULES, f"{name} is no rule of desk/eponymous_*.py"
    spec = Spec.parse({"name": name, **BOOK[name]})
    for seed in range(5):
        bars = _bars(seed)
        theirs = tuple(_run(name, RULES[name](), "X", bars))
        mine = tuple(_run(name, SpecRule(spec), "X", bars))
        assert mine == theirs, f"{name} seed {seed}: the spec differs from the rule"
        assert {d.action.name for d in theirs} >= {"BUY", "SELL"}, f"{name}: fixture never trades"
