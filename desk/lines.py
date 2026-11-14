"""lines - THE INSTRUMENT MASTER. Facts about a line come from here, never from its name."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from desk import venues

#: UK transaction tax on a purchase, by kind of instrument, the one table (NS-05); a sale
#: pays none. A fund or an exchange-traded product pays nil. A UK share pays stamp duty, half
#: of one per cent of what is paid (collected as stamp duty reserve tax when bought
#: electronically). Which a line is, is a fact recorded on it: its `uk_tax`.
NO_TAX, STAMP_DUTY = Decimal(0), Decimal("0.005")


@dataclass(frozen=True)
class Line:
    symbol: str
    venue: str  #: "LSE" or "US"; each venue keeps its own calendar
    currency: str  #: the currency its prices are quoted in: "GBP" or "USD"
    leverage: int  #: how many times its market's daily move the line makes; 1 when plain
    uk_tax: Decimal = NO_TAX  #: the part of a purchase's value paid in UK tax, from the table
    #: Whether a UK stocks and shares ISA can hold the line, and whether a UK retail customer
    #: can buy it: yes or no once recorded, never assumed, and None until somebody has.
    isa: bool | None = None
    retail: bool | None = None
    #: Closes that moved further than the store believes a market moves, recorded as real,
    #: by day: a crash or a jump, confirmed, never a split (the archive must adjust those).
    real_moves: frozenset[tuple[date, Decimal]] = field(default_factory=frozenset)
    #: Splits and consolidations, confirmed by a second free source or a published notice, by
    #: the first day at the new price: the number the old price is multiplied by (500 for a
    #: consolidation of 500 to 1, 0.5 for a split of 2 to 1), outside a market's move. The
    #: store adjusts the older bars only if the bar's jump is that ratio; never a guessed one.
    splits: frozenset[tuple[date, Decimal]] = field(default_factory=frozenset)
    #: Sessions of its venue on which the line did not trade, recorded: a suspension,
    #: confirmed, so the store finds no gap there.
    suspended: frozenset[date] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if self.venue not in venues.RULES:
            raise ValueError(f"{self.symbol}: no calendar for venue {self.venue!r}")
        if self.currency not in ("GBP", "USD"):
            raise ValueError(f"{self.symbol}: no price is quoted in {self.currency!r}")
        if type(self.leverage) is not int or self.leverage < 1:
            raise ValueError(
                f"{self.symbol}: leverage {self.leverage!r} is not a whole one or more"
            )
        if type(self.uk_tax) is not Decimal or self.uk_tax not in (NO_TAX, STAMP_DUTY):
            raise ValueError(f"{self.symbol}: no UK tax on a purchase is {self.uk_tax!r}")
        if self.uk_tax and self.venue != "LSE":
            raise ValueError(f"{self.symbol}: a {self.venue} line pays no UK tax")
        if not {type(self.isa), type(self.retail)} <= {bool, type(None)}:
            raise ValueError(
                f"{self.symbol}: whether an ISA can hold it and a retail customer buy it is"
                f" yes, no or unrecorded, not {self.isa!r} and {self.retail!r}"
            )
        self._records()

    def _records(self) -> None:
        if any(not r.is_finite() or r <= 0 or r == 1 for _, r in self.splits):
            raise ValueError(f"{self.symbol}: a split's ratio must be positive and not one")
        shut = [d for d in sorted(self.suspended) if venues.sessions(self.venue, d, d) != (d,)]
        if shut:
            raise ValueError(f"{self.symbol}: {shut[0]} is no {self.venue} session to suspend")


#: The frozen lines, by the operator's rulings of 13 November 2026 (docs/DECISIONS.md). SPY,
#: QQQ and GLD, US funds a UK ISA cannot buy, leave for VUAG (the S&P 500), EQQQ (the Nasdaq
#: 100) and IDTL (US Treasuries of twenty years and more, which London prices in dollars):
#: thirteen in London and seven in the US. GLD is gone; SPY and QQQ stay, recorded as lines
#: no ISA holds, only until the ladder's tests stop naming them (docs/PLAN.md).
#: Each row records whether an ISA can hold its lines and whether a retail customer can buy
#: them. IB1T, a note on bitcoin, has been open to retail since 8 October 2025 and shut out
#: of a stocks and shares ISA since 6 April 2026. The leveraged three are as their issuers
#: say, where an ISA's platform offers them.
#: Each with its leverage: 3LGO, 2MU and 5QQQ make three, two and five times their market's
#: daily move. None pays UK tax on a purchase: the thirteen in London are eight funds (SMGB,
#: IITU, VHYG, ISF, VUSA, VUAG, EQQQ, IDTL), exempt by regulation, and five exchange-traded
#: products, debt of an issuer outside the UK (3LGO, 2MU, 5QQQ, IB1T, SGLN), nil as the law
#: reads and still to be seen on a broker's contract note (docs/DECISIONS.md, the data lane's).
#: What a second free source confirms about the archive's bars (14 November 2026): the old
#: desk's Stooq daily bars (stooq_store_matrix) give the same closes and volumes on each of
#: these days, the closes exactly as the archive gives them. 2MU's and 5QQQ's days are real
#: moves of a leveraged line that the one-day range test cannot tell from a bad bar; 5QQQ's
#: price before 22 August 2024 was in a 500-for-1 consolidation's old shares (the archive's
#: jump, x489.5, is the ratio within a day's move).
MOVES = {
    "2MU": (
        (2024, 8, 5, "19.10699951171875"),
        (2024, 9, 26, "27.74300048828125"),
        (2024, 12, 19, "17.080999755859375"),
        (2025, 4, 4, "8.165"),
    ),
    "5QQQ": ((2025, 4, 7, "0.345"), (2025, 4, 8, "0.4295000076293945")),
}
SPLITS = {"5QQQ": ((date(2024, 8, 22), Decimal(500)),)}
LINES = tuple(
    Line(
        symbol,
        venue,
        currency,
        int(leverage),
        NO_TAX,
        isa,
        retail,
        frozenset((date(*day), Decimal(close)) for *day, close in MOVES.get(symbol, ())),
        frozenset(SPLITS.get(symbol, ())),
    )
    for venue, currency, isa, retail, symbols in (
        ("LSE", "GBP", True, True, "3LGO:3 2MU:2 SMGB:1 IITU:1 VHYG:1 5QQQ:5 ISF:1 VUSA:1 SGLN:1"),
        ("LSE", "GBP", True, True, "VUAG:1 EQQQ:1"),
        ("LSE", "GBP", False, True, "IB1T:1"),
        ("LSE", "USD", True, True, "IDTL:1"),
        ("US", "USD", True, True, "AAPL:1 TSLA:1 NVDA:1 SPCX:1 MSTR:1 AMD:1 MU:1"),
        ("US", "USD", False, False, "SPY:1 QQQ:1"),
    )
    for symbol, leverage in (entry.split(":") for entry in symbols.split())
)
#: What "simply holding the market" means, the one yardstick the desk's profit is set beside
#: (AG-04): VUAG, the S&P 500 in pounds with its dividends kept in, where SPY stood.
YARDSTICK = next(line for line in LINES if line.symbol == "VUAG")
