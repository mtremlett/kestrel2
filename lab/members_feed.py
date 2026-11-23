"""members_feed - THE FTSE REVIEWS READ IN: a quarterly review's announced joiners and leavers
(FTSE Russell's text) and the members of a Wikipedia list page in the revision either side of
it (the MediaWiki API's JSON), handed to `members.reconcile`, which names every disagreement.

Announcement text: a line `Joiners: A, B` and a line `Leavers: C`, tickers as the page writes
them. Page text: the wikitext table `constituents` (or the first table), rows split on `|-`, the
ticker the second cell of each row, one line (`|Co|| EPIC || Sector`) or one cell a line. Nothing
here dials out except `fetch`, one fixed public address family; parsing takes text, so every
test runs on committed fixtures. The shape of the live answers is read once from the first
real fetch; a shape that differs raises, never guesses. First real fetch, 23 Nov 2026: the pages
"FTSE 100 Index" and "FTSE 250 Index" read through `revision_url` give 100 and 250 tickers at
2025-03-25, 2026-06-01 and 2026-09-22; FTSE Russell's own site offers no stable machine-readable
announcement, so `announced` still reads text handed to it."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import date, timedelta
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from lab import members, universe
from lab.members import Change

API = "https://en.wikipedia.org/w/api.php"  #: keyless, public


def revision_url(page: str, day: date) -> str:
    """The question for the last revision of the page made on or before the end of day."""
    return API + "?" + urlencode(
        {
            "action": "query", "prop": "revisions", "titles": page, "rvlimit": 1,
            "rvstart": f"{day.isoformat()}T23:59:59Z", "rvdir": "older",
            "rvprop": "content", "rvslots": "main", "format": "json", "formatversion": 2,
        }
    )  # fmt: skip


def fetch(url: str) -> str:
    """The text answered at a url built here."""
    asking = Request(url, headers={"User-Agent": "research-desk/1.0 (public list reader)"})  # noqa: S310
    with urlopen(asking, timeout=60) as answer:  # noqa: S310 - API above, one fixed public host
        return str(answer.read().decode("utf-8"))  # bounded: one API answer for one revision


def page_members(answer: str) -> frozenset[str]:
    """The tickers in a revision's table: the second cell of each row."""
    pages = json.loads(answer)["query"]["pages"]
    if len(pages) != 1 or not pages[0].get("revisions"):
        raise ValueError(f"expected one page with a revision, got {len(pages)} pages")
    text = pages[0]["revisions"][0]["slots"]["main"]["content"]
    start = text.find('id="constituents"')
    table = text[max(start, 0) :].split("\n|}")[0]
    tickers = set()
    for row in table.split("\n|-")[1:]:
        cells = [c.strip() for c in row.strip().removeprefix("|").replace("\n|", "||").split("||")]
        if len(cells) >= 2 and not cells[0].startswith("!"):
            tickers.add(cells[1])
    return frozenset(tickers)


def announced(day: date, text: str) -> tuple[Change, ...]:
    """The joiners and leavers an announcement names, from day."""
    made: list[Change] = []
    for line in text.splitlines():
        head, _, names = line.partition(":")
        if head.strip() in ("Joiners", "Leavers"):
            joined = head.strip() == "Joiners"
            made += [Change(day, n.strip(), joined) for n in names.split(",") if n.strip()]
    return tuple(made)


def review(day: date, text: str, before: str, after: str) -> tuple[Change, ...]:
    """One review's changes, the announcement joined to the page's two revisions; a
    `members.Disagreement` where they differ."""
    return members.reconcile(day, announced(day, text), page_members(before), page_members(after))


def fetch_review(
    page: str, day: date, text: str, get: Callable[[str], str] = fetch
) -> tuple[Change, ...]:
    """One review read from the page's last revision the day before and on day; `get` is
    `fetch`, or a fixture's answer in tests."""
    before = get(revision_url(page, day - timedelta(days=1)))
    return review(day, text, before, get(revision_url(page, day)))


PAGES = ("FTSE 100 Index", "FTSE 250 Index")
UNMEASURED = (
    "unmeasured: FTSE review announcements, the funds' past members and a 2010-2014 second"
    " source (no free feed)"
)


def _name(ticker: str) -> str:
    """A page's EPIC as the archive names it: AV. is AV, BT.A is BT-A."""
    return ticker.rstrip(".").replace(".", "-")


def drift(day: date, get: Callable[[str], str] = fetch) -> str:
    """The nightly line: the FTSE 100 and 250 pages' members on day set beside the research
    list's FTSE 350, each side's extras named, and what no free source measures."""
    page = {_name(t) for p in PAGES for t in page_members(get(revision_url(p, day)))}
    ours = {line.symbol for line in universe.FTSE350}
    return (
        f"members: FTSE pages {len(page)}, list {len(ours)}; page only {sorted(page - ours)}, "
        f"list only {sorted(ours - page)}; {UNMEASURED}"
    )
