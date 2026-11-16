"""second - THE SECOND SOURCE'S ONE RULE, at the store's one writer (desk/store.py calls it).
Yahoo's bars come first. Stooq's fill a session inside Yahoo's span that its cleaned bars
lack (cleaned again with them, by every rule of the store), and where both hold a session their closes must agree within
AGREE, else the session is a recorded fault and kept from neither: never decided silently by
either. Stooq's prices may be in pence: its unit is the one in which most of the closes both
hold agree, and none doing so leaves it unused, in a note that parks nothing."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import replace
from datetime import date
from decimal import Decimal

from desk.store import Bar, Fault, Refused

AGREE = Decimal("0.02")  #: how far apart two sources' closes for one session may be, as a share
_PRICES = ("open", "high", "low", "close")
UNITS = (Decimal(1), Decimal("0.01"), Decimal(100))  #: Stooq's price in the store's: as is, pence


def unit(kept: Sequence[Bar], other: Sequence[Bar]) -> Decimal | None:
    """The factor that brings the other source's closes to the store's: the one in which most
    of the closes both hold agree; none unless that is more than half of them."""
    held = {bar.day: bar.close for bar in kept}
    pairs = [(held[bar.day], bar.close) for bar in other if bar.day in held]
    agreeing = {u: sum(abs(b * u / a - 1) <= AGREE for a, b in pairs) for u in UNITS}
    best = max(UNITS, key=lambda u: agreeing[u])
    return best if 2 * agreeing[best] > len(pairs) else None


def blend(
    kept: list[Bar],
    faults: list[Fault],
    other: Sequence[Bar] | Refused,
    bars: Sequence[Bar],
    day: date,
    clean: Callable[[Sequence[Bar]], tuple[list[Bar], list[Fault]]],
) -> tuple[list[Bar], list[Fault]]:
    """Yahoo's cleaned bars and faults with the second source's: what it fills, what it
    disputes. `clean` cleans bars as the store does: Yahoo's `bars`, again, with the filled ones."""
    factor = None if isinstance(other, Refused) else unit(kept, other)
    if isinstance(other, Refused) or factor is None:
        why = other.reason if isinstance(other, Refused) else "its closes agree in no unit"
        return kept, [*faults, Fault(day, f"second source unused: {why}", parks=False)]
    held = {bar.day: bar for bar in kept}
    scaled = [replace(b, **{f: getattr(b, f) * factor for f in _PRICES}) for b in other]
    apart = {
        b.day for b in scaled if b.day in held and abs(b.close / held[b.day].close - 1) > AGREE
    }
    filled = [b for b in scaled if b.day not in held and kept[0].day < b.day < kept[-1].day]
    notes = [Fault(d, f"{d} the two sources disagree: none kept") for d in sorted(apart)]
    if filled:
        given = {b.day for b in filled}
        kept, faults = clean([*(b for b in bars if b.day not in given), *filled])
        what = f"{len(filled)} sessions offered by the second source"
        notes.append(Fault(filled[0].day, what, parks=False))
    return [b for b in kept if b.day not in apart], [*faults, *notes]
