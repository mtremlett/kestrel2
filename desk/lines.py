"""lines - THE INSTRUMENT MASTER. Facts about a line come from here, never from its name."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date
from decimal import Decimal

from desk import venues

#: UK transaction tax on a purchase, by kind of instrument, the one table (NS-05); a sale
#: pays none. A fund or an exchange-traded product pays nil. A UK share pays stamp duty, half
#: of one per cent of what is paid (collected as stamp duty reserve tax when bought
#: electronically). Which a line is, is a fact recorded on it: its `uk_tax`.
NO_TAX, STAMP_DUTY = Decimal(0), Decimal("0.005")


def valid_isin(isin: str) -> bool:
    """Twelve characters, two capital letters first, the last a Luhn digit over the rest."""
    if len(isin) != 12 or not (isin[:2].isalpha() and isin.isalnum() and isin.upper() == isin):
        return False
    if not isin[-1].isdigit():
        return False
    digits = "".join(str(int(c, 36)) for c in isin)
    total = sum(
        (d := int(c)) * 2 - 9 * (d * 2 > 9) if i % 2 else int(c)
        for i, c in enumerate(reversed(digits))
    )
    return total % 10 == 0


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
    #: The market the line tracks and the reference data that says so (the issuer's factsheet, or
    #: the company itself): lines on one index share one underlying (R-RUNNER-157, canon B3).
    underlying: str = ""
    source: str = ""
    #: The ISIN, the twelve-character international id the issuer and the broker both give
    #: (R-PAPER-3); None only for a reference series that is no security.
    isin: str | None = None
    #: The first day of each change of the currency its prices are quoted in, recorded from the
    #: issuer's notice, never inferred from the bars: the step that day is the unit, not a move.
    requoted: frozenset[date] = field(default_factory=frozenset)
    #: The first day whose bars the store keeps, where the archive's older ones are in another
    #: unit than its newer: earlier bars are dropped with one fault, never rescaled by a guess.
    starts: date | None = None

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
        if self.isin is not None and not valid_isin(self.isin):
            raise ValueError(f"{self.symbol}: {self.isin!r} is not an ISIN with a good check digit")
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
#: thirteen in London and seven in the US. GLD is gone; SPY and QQQ stay only as price
#: references (REFERENCE below), never traded, until the callers outside this module read
#: REFERENCE instead of LINES (docs/PLAN.md, data-isa-twins).
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
#: moves of a leveraged line that the one-day range test cannot tell from a bad bar. 5QQQ's
#: 22 August 2024 is no consolidation (17 November 2026): Stooq's closes run on unbroken
#: from 28p in December 2022 to 111p in August 2024, and the archive's bars before the day
#: are exactly a hundredth of them, pounds where the later ones are pence; the archive's
#: jump (x489.5) is that hundred and a market that rose fivefold, over a gap of 432 sessions.
#: Scaled by 500 they stood 5 times too high; so the line starts on 22 August 2024.
#: 3LGO's history (17 November 2026): the archive's answer holds one bar, the latest, so the line
#: lives on its shelf: Stooq's daily bars from 4 June 2015, none before in any free source, and
#: 79 sessions missing in the seven months after (thin trading, volumes of hundreds; no second
#: source holds a bar on one of them, so none is recorded as a suspension). The shelf ends on the
#: day it was last made; each session since that the broker's and the archive's daily bars lack
#: is bridged from the five-minute bars the store holds (`bars.bridged`, 30 days back), else
#: it parks the line as missing, rightly. Enough has gathered when the archive's own bars alone
#: reach the ladder's `lab.verdict.MIN_BARS`; the line then needs no shelf, joined harmlessly.
#: 2MU's box (17 November 2026): the four moves below are the only ones the store parks it
#: for, and each is needed (without one, that day parks it). Stooq's closes of 26 September
#: and 19 December 2024 and 4 April 2025 are the archive's to the penny. 5 August 2024 is a
#: two-day fall: the archive dropped 2 August as a bad bar, where Stooq has it (close 20.99,
#: down 26%) and then 19.11 on the 5th. The "fifth" is 24 October 2025: the archive's bar
#: of no volume, 54% up, is dropped; Stooq has 66.50 that day, so the drop is right.
MOVES = {
    "2MU": (
        (2024, 8, 5, "19.10699951171875"),
        (2024, 9, 26, "27.74300048828125"),
        (2024, 12, 19, "17.080999755859375"),
        (2025, 4, 4, "8.165"),
    ),
    "5QQQ": ((2025, 4, 7, "0.345"), (2025, 4, 8, "0.4295000076293945")),
    "SGLN": ((2013, 4, 15, "17.870"),),  # gold's crash day: open 18.76, low 17.715, down 8%
    # 2000-2009 (17 November 2026), the archive's closes; Stooq has each day too, its closes a
    # constant factor off (dividend-adjusted: AAPL 1.19, NVDA 1.09; AMD exact): the same moves.
    "AAPL": ((2000, 9, 29, "0.4598209857940674"),),  # fell 52% on a profit warning
    "NVDA": ((2000, 4, 5, "0.19101600348949432"), (2004, 8, 6, "0.0785830020904541")),
    "AMD": ((2008, 9, 29, "4.289999961853027"), (2008, 9, 30, "5.25")),  # range 3 to 6, then up
}
#: Each line's ISIN, as the broker's contract details give it (the conformance tapes of 14
#: November 2026); IDTL's as its issuer lists it.
ISINS = dict(
    pair.split(":")
    for pair in (
        "3LGO:IE00B8HGT870 2MU:IE00BKT66K01 SMGB:IE00BMC38736 IITU:IE00B3WJKG14"
        " VHYG:IE00BK5BR626 5QQQ:XS2399364152 ISF:IE0005042456 VUSA:IE00B3XXRP09"
        " SGLN:IE00B4ND3602 VUAG:IE00BFMXXD54 EQQQ:IE0032077012 IB1T:XS2940466316"
        " IDTL:IE00BSKRJX20 AAPL:US0378331005 TSLA:US88160R1014 NVDA:US67066G1040"
        " SPCX:US84615Q1031 MSTR:US5949724083 AMD:US0079031078 MU:US5951121038"
        " SPY:US78462F1030 QQQ:US46090E1038"
        " XSPS:LU0322251520 SUK1:IE00B94QKG22 1MCS:IE00BBGBF313 LQQS:IE00BLRPRJ20"
    ).split()
)
#: Where each line's bars start, once the archive's older ones are in another unit (above).
STARTS = {"5QQQ": date(2024, 8, 22)}
#: Each line's underlying market and the factsheet (or company) that names it, never the ticker.
UNDERLYING = {
    "3LGO": ("GOLD", "WisdomTree 3x Daily Long Gold factsheet"),
    "SGLN": ("GOLD", "iShares Physical Gold ETC factsheet"),
    "2MU": ("MU", "Leverage Shares 2x Long Micron factsheet"),
    "MU": ("MU", "Micron Technology"),
    "SMGB": ("MVIS US LISTED SEMICONDUCTOR 25", "VanEck Semiconductor UCITS ETF factsheet"),
    "IITU": ("S&P 500 INFORMATION TECHNOLOGY", "iShares S&P 500 IT Sector UCITS ETF factsheet"),
    "VHYG": (
        "FTSE ALL-WORLD HIGH DIVIDEND YIELD",
        "Vanguard FTSE All-World High Div Yield factsheet",
    ),
    "5QQQ": ("NASDAQ 100", "WisdomTree NASDAQ 100 5x Daily Leveraged factsheet"),
    "EQQQ": ("NASDAQ 100", "Invesco EQQQ NASDAQ-100 UCITS ETF factsheet"),
    "QQQ": ("NASDAQ 100", "Invesco QQQ Trust factsheet"),
    "ISF": ("FTSE 100", "iShares Core FTSE 100 UCITS ETF factsheet"),
    "VUSA": ("S&P 500", "Vanguard S&P 500 UCITS ETF factsheet"),
    "VUAG": ("S&P 500", "Vanguard S&P 500 UCITS ETF Accumulating factsheet"),
    "SPY": ("S&P 500", "SPDR S&P 500 ETF Trust factsheet"),
    "IB1T": ("BITCOIN", "iShares Bitcoin ETP factsheet"),
    "IDTL": ("US TREASURIES 20+ YEAR", "iShares USD Treasury Bond 20+yr UCITS ETF factsheet"),
    "AAPL": ("AAPL", "Apple Inc."),
    "TSLA": ("TSLA", "Tesla Inc."),
    "NVDA": ("NVDA", "NVIDIA Corp."),
    "SPCX": ("SPCX", "Space Exploration Technologies Corp."),
    "MSTR": ("MSTR", "Strategy Inc."),
    "AMD": ("AMD", "Advanced Micro Devices Inc."),
    "XSPS": ("S&P 500", "Xtrackers S&P 500 Inverse Daily Swap UCITS ETF factsheet"),
    "SUK1": ("FTSE 100", "WisdomTree FTSE 100 1x Daily Short factsheet"),
    "1MCS": ("FTSE 250", "WisdomTree FTSE 250 1x Daily Short factsheet"),
    "LQQS": ("NASDAQ 100", "WisdomTree NASDAQ 100 3x Daily Short factsheet"),
}
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
        frozenset(),
        frozenset(),
        *UNDERLYING[symbol],
        isin=ISINS[symbol],
        starts=STARTS.get(symbol),
    )
    for venue, currency, isa, retail, symbols in (
        ("LSE", "GBP", True, True, "3LGO:3 2MU:2 SMGB:1 IITU:1 VHYG:1 5QQQ:5 ISF:1 VUSA:1 SGLN:1"),
        ("LSE", "GBP", True, True, "VUAG:1 EQQQ:1"),
        ("LSE", "GBP", None, None, "XSPS:1 SUK1:1 1MCS:1 LQQS:3"),  # inverse; ISA, retail unknown
        ("LSE", "GBP", False, True, "IB1T:1"),
        ("LSE", "USD", True, True, "IDTL:1"),
        ("US", "USD", True, True, "AAPL:1 TSLA:1 NVDA:1 SPCX:1 MSTR:1 AMD:1 MU:1"),
        ("US", "USD", False, False, "SPY:1 QQQ:1"),
    )
    for symbol, leverage in (entry.split(":") for entry in symbols.split())
)
#: SPY and QQQ, which a UK retail customer cannot buy (VUAG and EQQQ are their tradeable twins):
#: readable as reference series, never traded (R-PAPER-16). They sit in LINES only until the
#: callers that still take them from there (conformance, the Mansfield rule) move to this.
REFERENCE = tuple(line for line in LINES if line.retail is False)


#: The pound in dollars at the archive, kept as a reference series (never traded), and the band
#: its close must lie in, in dollars, to be trusted (R-PAPER-22). The pound stood above two dollars
#: in 2007 (the archive's own closes), so the band is one to three: a pence figure or the dollar's
#: own inverse still lies outside it.
POUND, DOLLARS = Line("GBPUSD=X", "US", "USD", 1), (Decimal(1), Decimal(3))


TAG = "-ADJUSTED"  #: ends the symbol of a reference series' dividend-adjusted twin (R-RUNGS-9)
#: Each reference series again, its prices adjusted for dividends and splits by the archive, kept
#: beside the as-traded series under its own name, never in place of it.
ADJUSTED = tuple(replace(line, symbol=line.symbol + TAG) for line in REFERENCE)


def require_traded(line: Line) -> Line:
    """The line, if the desk or the lab may trade it; a reference series is refused."""
    if line in REFERENCE or line in ADJUSTED:
        raise ValueError(f"{line.symbol}: a reference series, which no retail customer can buy")
    return line


#: What "simply holding the market" means, the one yardstick the desk's profit is set beside
#: (AG-04): VUAG, the S&P 500 in pounds with its dividends kept in, where SPY stood.
YARDSTICK = next(line for line in LINES if line.symbol == "VUAG")
