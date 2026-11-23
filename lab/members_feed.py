"""members_feed - THE FTSE REVIEWS READ IN: a quarterly review's announced joiners and leavers
(FTSE Russell's text) and the members of a Wikipedia list page in the revision either side of
it (the MediaWiki API's JSON), handed to `members.reconcile`, which names every disagreement.

Announcement text: a line `Joiners: A, B` and a line `Leavers: C`, tickers as the page writes
them. Page text: wikitext table rows (`|-`), the ticker the second cell of each row. Nothing
here dials out except `fetch`, one fixed public address family; parsing takes text, so every
test runs on committed fixtures. The shape of the live answers is read once from the first
real fetch; a shape that differs raises, never guesses."""

from __future__ import annotations

import json
from datetime import date
from urllib.parse import urlencode
from urllib.request import urlopen

from lab import members
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
    with urlopen(url, timeout=60) as answer:  # noqa: S310 - API above, one fixed public host
        return str(answer.read().decode("utf-8"))  # bounded: one API answer for one revision


def page_members(answer: str) -> frozenset[str]:
    """The tickers in a revision's table: the second cell of each row."""
    pages = json.loads(answer)["query"]["pages"]
    if len(pages) != 1 or not pages[0].get("revisions"):
        raise ValueError(f"expected one page with a revision, got {len(pages)} pages")
    text = pages[0]["revisions"][0]["slots"]["main"]["content"]
    tickers = set()
    for row in text.split("|-")[1:]:
        cells = [c.strip() for c in row.split("\n|") if c.strip()]
        if len(cells) >= 2:
            tickers.add(cells[1].split("||")[0].strip())
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
