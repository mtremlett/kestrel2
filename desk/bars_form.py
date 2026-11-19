"""bars_form - THE ONE FORM a bar enters the fast store in, split from desk/bars.py (B4): every
price is rounded once, half to even, to PLACES decimals and kept as that text, so the archive's
float (760.0700073242188) and the broker's text (760.0700) are one bar. A held day is changed only
when its prices or volume differ as numbers; the same answer given twice changes nothing."""

from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any

from desk.bars_parts import HOLDING, NOTE

PLACES = Decimal("0.0001")  #: the store's one price grid: a ten-thousandth of the currency

Row = tuple[str, str, str, str, int]  #: open, high, low, close as text, and the volume


def form(price: Decimal) -> str:
    """A price in the store's one form."""
    return str(price.quantize(PLACES, ROUND_HALF_EVEN))


def same(held: Sequence[str | int], given: Row) -> bool:
    """A held bar's prices and volume are the given bar's, whatever form the held text is in."""
    prices = [Decimal(p).quantize(PLACES, ROUND_HALF_EVEN) for p in held[:4]]
    return prices == [Decimal(p) for p in given[:4]] and held[4] == given[4]


def restated(
    held: sqlite3.Connection,
    source: str,
    key: tuple[str, str, str],
    prices: list[tuple[int, Row]],
    rows: list[tuple[Any, ...]],
) -> list[tuple[Any, ...]]:
    """The rows of a daily write that change something. A held day whose prices or volume differ
    is copied into `correction`; one the same under the same source is not written at all."""
    ats = [at for at, _ in prices]
    now = {r[0]: r for r in held.execute(HOLDING, (*key, min(ats, default=0), max(ats, default=0)))}
    moved = [at for at, price in prices if at in now and not same(now[at][1:6], price)]
    held.executemany(NOTE, ((source, *key, at) for at in moved))
    return [r for r in rows if r[3] in moved or r[3] not in now or now[r[3]][6] != r[-1]]
