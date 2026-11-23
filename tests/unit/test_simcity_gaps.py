"""simcity_gaps: a world's days open away from the close before by the line's own gaps, the
same seed the same gaps, and a gap through a resting stop sells at the open below it."""

from __future__ import annotations

import random
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest
from test_simcity import MARKET, busy

from desk import simcity
from desk.simcity import THROUGH, _through, history
from desk.store import Bar


def test_a_worlds_opens_differ_from_the_prior_closes_by_the_lines_own_gaps_and_by_its_seed() -> (
    None
):
    def gapped(bar: Bar, at: int) -> Bar:  #: opens 1% over the close before it, every other day
        return replace(bar, open=bar.open * Decimal("1.01"), high=bar.high * 2) if at % 2 else bar

    saved = {x: [gapped(b, at) for at, b in enumerate(bars)] for x, bars in MARKET.items()}
    one, same, other = (simcity._market(saved, random.Random(s)) for s in (1, 1, 2))  # noqa: S311
    assert one == same != other, "the same seed did not give the same gaps"
    for line, made in one.items():
        ratios = {b.open / a.close for a, b in zip(made, made[1:], strict=False)}
        assert len(ratios) > 1, "no gap overnight in the world"
        assert max(ratios) < Decimal("1.02") > min(ratios) > Decimal("0.99"), "not the line's own"
        assert history(saved[line]), "no history"
        assert all(b.low <= min(b.open, b.close) <= b.high for b in made)


def test_a_gap_through_a_resting_stop_sells_at_the_open_below_it_and_is_counted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(simcity, "EVENTS", ((THROUGH, _through),))
    night = busy(monkeypatch, tmp_path, (0, 1))
    assert THROUGH in {s for ran in night.census.values() for s in ran}, "no scenario counted"
    assert not [b for b in night.broken if "gap through a stop" in b or "never happened" in b]
