"""The FTSE review feed: an announcement joined to the page either side of it."""

from __future__ import annotations

import json
from datetime import date

import pytest

from lab import members, members_feed, universe

DAY = date(2026, 9, 21)


def _page(*tickers: str) -> str:
    rows = "".join(f"|-\n| [[Co {t}]]\n| {t}\n| x\n" for t in tickers)
    content = "{|\n! Company\n! Ticker\n! Sector\n" + rows + "|}"
    page = {"revisions": [{"slots": {"main": {"content": content}}}]}
    return json.dumps({"query": {"pages": [page]}})


BEFORE, AFTER = _page("AV.", "BP.", "OLD"), _page("AV.", "BP.", "NEW")
TEXT = "Review of 2026\nJoiners: NEW\nLeavers: OLD\n"


def test_the_announcement_and_the_page_agree_on_joiners_and_leavers() -> None:
    got = members_feed.review(DAY, TEXT, BEFORE, AFTER)
    assert got == (members.Change(DAY, "NEW", True), members.Change(DAY, "OLD", False))


def test_a_planted_disagreement_is_a_named_fault_and_the_url_asks_for_the_day() -> None:
    with pytest.raises(members.Disagreement, match=r"only the announcement has \['-OLD'\]"):
        members_feed.review(DAY, TEXT, BEFORE, _page("AV.", "BP.", "OLD", "NEW"))
    with pytest.raises(ValueError, match="one page"):
        members_feed.page_members('{"query": {"pages": []}}')
    assert "rvstart=2026-09-21T23%3A59%3A59Z" in members_feed.revision_url("FTSE 100", DAY)


def test_the_live_pages_one_line_rows_are_read() -> None:
    rows = ['{| id="constituents"', "|-", "!|Company|| EPIC", "|-", "|[[3i]]||III||FS"]
    rows += ["|-", "|[[A]] || ADM || N", "|}", "|-", "|x||NO||y"]
    content = "\n".join(rows)
    page = {"revisions": [{"slots": {"main": {"content": content}}}]}
    got = members_feed.page_members(json.dumps({"query": {"pages": [page]}}))
    assert got == {"III", "ADM"}


def test_a_fetched_review_asks_for_the_day_before_and_the_day() -> None:
    asked: list[str] = []

    def get(url: str) -> str:
        asked.append(url)
        return BEFORE if len(asked) == 1 else AFTER

    got = members_feed.fetch_review("FTSE 100", DAY, TEXT, get)
    assert len(got) == 2 and "2026-09-20T23" in asked[0] and "2026-09-21T23" in asked[1]


def test_the_nightly_line_sets_the_pages_beside_the_list_and_names_the_unmeasured() -> None:
    names = [line.symbol for line in universe.FTSE350]
    page = _page("AV.", "BT.A", names[0], "ZZZ")
    line = members_feed.drift(DAY, lambda _: page)
    assert "page only ['ZZZ']" in line and "list only" in line and "unmeasured: FTSE" in line
    assert "BT-A" not in line.split("page only")[1].split("list only")[0]
