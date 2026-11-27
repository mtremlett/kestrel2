"""Spec parity: every row of `lab/catalogue.toml` decides, on every day of every fixture series,
exactly as its Python rule in `desk/eponymous_*.py` while that file stands, and as its pinned
fingerprint always, so a twin can be deleted with its trades still held; every rule has a row."""

from __future__ import annotations

import hashlib
import random
import tomllib
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from desk.store import Bar
from desk.strategy import Rule, _run
from lab import rulebook
from lab.spec import Spec, SpecRule, ratio_bars

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


def _twin(name: str, counts: dict[date, tuple[int, int]]) -> Rule:
    """The row's Python twin; Zweig's reads the day's breadth, imported only while it stands."""
    if BOOK[name]["entry"] != "breadth_thrust":
        return RULES[name]()
    from desk.eponymous_zweig_breadth_thrust import Breadth  # noqa: PLC0415

    return RULES[name]({day: Breadth(*pair) for day, pair in counts.items()})  # type: ignore[call-arg]


# Each row's decisions on the five fixture series, hashed: the proof of identical trades that
# outlives its Python twin (rungs-rows-as-rules). A changed hash is a changed rule (B5, DECISIONS).
PINNED: dict[str, str] = {
    "bollinger_squeeze": "17ee5331ac438f40",
    "clenow_momentum": "445d61ba0c4fa625",
    "connors_percent_b": "c0a6ebcfcd27e3f4",
    "connors_rsi2": "e49cc20b59ae9a43",
    "connors_three_day_high_low": "3355b32f1df9f7a3",
    "dan_zanger_breakout": "cdfb37b7a054f3e2",
    "darvas_box": "e53f80e7166e342d",
    "demark_sequential": "b15e955c6a91dd3d",
    "donchian_channel_breakout": "688d2e50ba73e28d",
    "donchian_fade_chop": "2a2ae783512a0be7",
    "dual_momentum": "2553c4ba7cffd393",
    "faber_tactical": "e3e740cd7dc9a946",
    "kell_breakout": "6524f0498454f29a",
    "keltner_channel_trend": "740e0378cdb11415",
    "mansfield_rs_momentum": "91df48c7a44471e5",
    "minervini_breakout": "89b5f189c037b8a0",
    "raschke_swing": "a90ea8d722dbccf4",
    "weekly_reversal_jegadeesh": "a99c155880d7c216",
    "weinstein_stage": "3377a7d485b98347",
    "williams_r": "1cbc06de44c8d404",
    "zweig_breadth_thrust": "bab612f0aa487836",
}


@pytest.mark.parametrize("name", sorted(BOOK.keys() | RULES))
def test_each_spec_decides_as_its_python_rule_and_its_pin_on_every_day(name: str) -> None:
    assert name in BOOK, f"{name}: a desk rule with no catalogue row"
    spec, seen, print_ = Spec.parse({"name": name, **BOOK[name]}), set(), hashlib.sha256()
    for seed in range(5):
        bars, draw = _bars(seed), random.Random(seed)  # noqa: S311 - a test draw
        counts = {b.day: (draw.randint(1, 99), draw.randint(1, 99)) for b in bars}
        breadth = BOOK[name]["entry"] == "breadth_thrust"  # the row reads the breadth ratio
        mine = tuple(_run(name, SpecRule(spec), "X", ratio_bars(counts) if breadth else bars))
        if name in RULES:
            theirs = tuple(_run(name, _twin(name, counts), "X", _bars(seed)))
            assert mine == theirs, f"{name} seed {seed}: the spec differs from the rule"
        seen |= {d.action.name for d in mine}
        print_.update(repr(mine).encode())
    assert seen >= {"BUY", "SELL"}, f"{name}: the five fixture series never buy and sell"
    assert PINNED.get(name) == print_.hexdigest()[:16], f"{name}: {print_.hexdigest()[:16]}"
