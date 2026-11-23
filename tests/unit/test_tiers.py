"""Tiers: claims fill tier A to the allowance, breadth by venue, moves, one adapter per tier."""

from __future__ import annotations

import pytest

from desk.lines import Line
from desk.tiers import Feeds, Placement, Tier, moves, place

A, B, C = Placement(Tier.A, "1m"), Placement(Tier.B, "1m"), Placement(Tier.C, "1d")
LONDON = Placement(Tier.B, "5m")
UNIVERSE = [Line("AAA", "US", "USD", 1), Line("BBB", "US", "USD", 1), Line("VUAG", "LSE", "GBP", 1)]


class Fake:
    def __init__(self, name: str) -> None:
        self.name = name

    def bars(self, symbol: str, timeframe: str) -> list[object]:
        return [self.name, symbol, timeframe]


def test_claims_fill_a_in_order_held_signalled_watched_to_the_allowance() -> None:
    got = place(UNIVERSE, held=["BBB"], signalled=["AAA"], watched=["VUAG"], allowance=2)
    assert got == {"AAA": A, "BBB": A, "VUAG": LONDON}


def test_breadth_is_daily_for_us_until_bought_and_five_minutes_for_london() -> None:
    assert place(UNIVERSE) == {"AAA": C, "BBB": C, "VUAG": LONDON}
    assert place(UNIVERSE, us_breadth_bought=True)["AAA"] == B


def test_a_name_that_gains_a_position_moves_up_and_only_it() -> None:
    before = place(UNIVERSE)
    after = place(UNIVERSE, held=["AAA", "UNKNOWN"])
    assert moves(before, after) == {"AAA": (C, A)}
    assert moves({}, after)["BBB"] == (None, C)


def test_each_tier_is_served_by_its_own_feed_and_unbought_breadth_is_loud() -> None:
    feeds = Feeds(Fake("a"), None, Fake("lon"), Fake("c"))
    plan = place(UNIVERSE, held=["AAA"])
    served = {
        s.symbol: feeds.for_placement(s, plan[s.symbol]).bars(s.symbol, "x")[0] for s in UNIVERSE
    }
    assert served == {"AAA": "a", "BBB": "c", "VUAG": "lon"}
    with pytest.raises(LookupError, match="AAA"):
        feeds.for_placement(UNIVERSE[0], B)
