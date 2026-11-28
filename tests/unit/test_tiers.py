"""The tiers contract: the allowance fills held first, the rest fall by venue, and a name moves
with its position; Tier B is a loud refusal until its vendor is bought."""

from __future__ import annotations

import pytest

from desk import tiers
from desk.bars_schema import Source
from desk.tiers import Tier


def test_held_then_signalled_then_watched_fill_the_allowance_and_the_overflow_falls() -> None:
    names = ["AAA", "BBB", "CCC", "DDD", "EEE", "ZZZ"]
    got = tiers.place(
        names, held=["BBB"], signalled=["AAA", "CCC"], watched=["DDD"], london=["CCC"], allowance=2
    )
    assert [got[n].tier for n in names] == [Tier.A, Tier.A, Tier.C, Tier.C, Tier.C, Tier.C]
    assert got["AAA"].feed == tiers.TIER_FEEDS[Tier.A]  # signalled, name order after the held
    assert got["BBB"].feed.span == "1m" and got["BBB"].tier is Tier.A
    assert got["CCC"].feed == tiers.LONDON_FEED  # over the allowance, listed in London: 15 minutes
    assert (
        got["DDD"].feed == tiers.TIER_FEEDS[Tier.C] == got["ZZZ"].feed
    )  # watched, not London: daily


def test_a_name_moves_tier_when_its_position_goes() -> None:
    assert tiers.place(["AAA"], held=["AAA"])["AAA"].tier is Tier.A
    assert tiers.place(["AAA"])["AAA"].tier is Tier.C


def test_a_stray_name_and_the_unbought_vendor_are_refused() -> None:
    with pytest.raises(ValueError, match="ZZZ"):
        tiers.place(["AAA"], held=["ZZZ"])
    with pytest.raises(NotImplementedError, match="A-GATE"):
        tiers.feed_of(Tier.B)
    with pytest.raises(ValueError, match="unknown span"):
        tiers.Feed(Source.IBKR, "7m")
