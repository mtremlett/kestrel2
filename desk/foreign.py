"""foreign - WHAT IS NOT THE DESK'S OWN. A rehearsal's orders carry the rehearsal prefix, an id the
desk never makes for itself, so a fill under one is found on the account, never traded."""

from __future__ import annotations

REHEARSAL = "rehearsal-"  #: the front of every order id a rehearsal makes


def is_foreign(order_id: str) -> bool:
    """Whether a fill's order id is a rehearsal's, not the desk's own."""
    return order_id.startswith(REHEARSAL)
