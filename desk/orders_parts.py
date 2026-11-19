"""orders_parts - THE BROKER'S FEE SCHEDULE AND THE COST ASSUMPTIONS, the lower part of
desk.orders: the numbers that price a leg. desk.orders gives them to its callers."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class _Fee:
    """A venue's commission, in the line's currency: per share plus a share of the value, no
    less than a minimum, and no more than a share of the value where there is a cap. And a
    sale's own cost, its regulators' fees: a share of the value, and an amount for each
    share sold up to the most one sale pays."""

    per_share: Decimal
    of_value: Decimal
    minimum: Decimal
    cap: Decimal | None
    sold_value: Decimal
    sold_share: Decimal
    sold_most: Decimal


#: Interactive Brokers UK, fixed pricing, read from its published schedule on 13 November
#: 2026. Dollars are bought by its automatic conversion: 0.03% on the rate, no commission.
#: With every US sale it passes on the regulators' two fees: the SEC's 20.60 dollars a
#: million sold (since 4 April 2026) and FINRA's 0.0195 cents a share, at most 9.79 dollars
#: (its 2026 rate), each read in the regulator's own notice. A London sale pays nothing more.
BROKER = "Interactive Brokers UK, fixed pricing (schedule read 13 November 2026)"
FEES = {
    "LSE": _Fee(Decimal(0), Decimal("0.0005"), Decimal(3), None, *(Decimal(0),) * 3),
    "US": _Fee(
        Decimal("0.005"),
        Decimal(0),
        Decimal(1),
        Decimal("0.01"),
        Decimal("0.0000206"),
        Decimal("0.000195"),
        Decimal("9.79"),
    ),
}
CONVERSION = Decimal("0.0003")
#: ASSUMED, not measured (docs/DECISIONS.md), until the paper account's own fills are set
#: beside them: each leg loses a twentieth of one per cent of its value to half the spread
#: and as much again to slippage, both times the line's leverage, since a line that moves
#: that many times its market is quoted that much wider. A stop sells into a falling
#: market, so its sale slips STOP_SLIPS times as far.
HALF_SPREAD = SLIPPAGE = Decimal("0.0005")
STOP_SLIPS = 3
