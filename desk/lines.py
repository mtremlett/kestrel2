"""lines - THE INSTRUMENT MASTER. Facts about a line come from here, never from its name."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from desk import venues


@dataclass(frozen=True)
class Line:
    symbol: str
    venue: str  #: "LSE" or "US"; each venue keeps its own calendar
    currency: str  #: the currency its prices are quoted in: "GBP" or "USD"
    leverage: int  #: how many times its market's daily move the line makes; 1 when plain
    #: Closes that moved further than the store believes a market moves, recorded as real,
    #: by day: a crash or a jump, confirmed, never a split (the archive must adjust those).
    real_moves: frozenset[tuple[date, Decimal]] = field(default_factory=frozenset)
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
        for day in sorted(self.suspended):
            if venues.sessions(self.venue, day, day) != (day,):
                raise ValueError(f"{self.symbol}: {day} is no {self.venue} session to suspend")


#: The twenty frozen lines, by the operator's ruling of 13 November 2026 (docs/DECISIONS.md).
#: Each with its leverage: 3LGO, 2MU and 5QQQ make three, two and five times their market's
#: daily move.
LINES = tuple(
    Line(symbol, venue, currency, int(leverage))
    for venue, currency, symbols in (
        ("LSE", "GBP", "3LGO:3 2MU:2 SMGB:1 IITU:1 VHYG:1 5QQQ:5 IB1T:1 ISF:1 VUSA:1 SGLN:1"),
        ("US", "USD", "AAPL:1 TSLA:1 NVDA:1 SPCX:1 MSTR:1 AMD:1 SPY:1 QQQ:1 MU:1 GLD:1"),
    )
    for symbol, leverage in (entry.split(":") for entry in symbols.split())
)
