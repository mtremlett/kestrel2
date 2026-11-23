"""The two registries of eponymous rules cannot drift apart: the desk's files and the book."""

from __future__ import annotations

from lab import ladder, published, rulebook
from lab.published_epon import EPONYMOUS_PUBLISHED


def test_every_eponymous_rule_is_published_and_every_publication_has_its_module() -> None:
    files, book = ladder.eponymous(), set(EPONYMOUS_PUBLISHED)
    unpublished = sorted(set(files) - book)
    assert not unpublished, f"in a desk/eponymous_*.py but not in the published book: {unpublished}"
    moduleless = sorted(book - set(rulebook.eponymous()))
    assert not moduleless, f"published as eponymous but in no desk/eponymous_*.py: {moduleless}"
    both = sorted(book & set(published.PUBLISHED))
    assert not both, f"on file in both published books: {both}"
