"""book_diff - THE BOOK AGAINST A BROKER: the one comparison of the desk's book with a broker's
holdings or resting stops, and the difference it names; desk.book gives both to its callers."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Difference:
    """One entry of a broker's that is not the desk's book."""

    name: str  #: what is held, in the words the book and the broker's entries share
    broker: Decimal | int  #: the shares the broker's entry gives; 0 when it gives no entry
    book: int  #: the shares the desk's book holds of it; 0 when it holds none


def differences(
    held: Mapping[str, int], entries: Iterable[tuple[str, Decimal | int]]
) -> tuple[Difference, ...]:
    """THE BOOK AGAINST A BROKER: the one comparison of its holdings or resting stops. held is
    the book; entries are the broker's (name, shares), which must be the book's own: shares in
    two entries are never one line. A name the book holds and the broker omits has no shares;
    one listed at none is not held. None named: they agree."""
    rows = list(entries)
    places = Counter(name for name, shares in rows if shares)
    rows += [(name, 0) for name in held.keys() - {name for name, _ in rows}]
    return tuple(
        Difference(name, shares, held.get(name, 0))
        for name, shares in sorted(rows)
        if shares != held.get(name, 0) or (shares and places[name] > 1)
    )
