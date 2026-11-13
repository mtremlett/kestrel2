"""universe - THE RESEARCH LIST: the tickers research may study. Being on it makes nothing
tradable: it lives in lab/, which desk/ may never import, and the desk trades only the lines of
its instrument master (ten of which are also here, to be studied).

Four published lists as they stood on 13 November 2026, by the operator's ruling of that day:
the S&P 500, the Nasdaq 100, the FTSE 350 and 200 much-traded US funds. A ticker is named as
the archive names it (BRK-B, BT-A). Every one is a member today: a study of the past on this
list sees only the survivors, and must say so.

Their bars are kept by the one store, under its checks, in a folder for each venue, because
one symbol can be two companies: BA is Boeing in New York and BAE Systems in London.

Research reads them through `read`, by a rule of its own for the large moves nobody has
confirmed. The store parks a ticker for one, as it parks a trading line, and that is not
loosened: the desk cannot import this module, so the rule can decide no trade."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path
from statistics import median

from desk import archive, store
from desk.lines import LINES, NO_TAX, STAMP_DUTY, Line
from desk.store import Bar, Parked


def _lines(venue: str, currency: str, symbols: str, tax: Decimal = NO_TAX) -> tuple[Line, ...]:
    """Each ticker as a line, a fund's leverage after a colon, its UK tax its list's. One the
    desk also trades is the instrument master's own line, so its facts have one home; the two
    may not disagree."""
    master = {(line.symbol, line.venue): line for line in LINES}
    made = []
    for entry in symbols.split():
        symbol, colon, leverage = entry.partition(":")
        line = Line(symbol, venue, currency, int(leverage) if colon else 1, tax)
        known = master.get((symbol, venue), line)
        facts = (line.currency, line.leverage, line.uk_tax)
        if (known.currency, known.leverage, known.uk_tax) != facts:
            raise ValueError(f"{symbol}: the research list and the instrument master disagree")
        made.append(known)
    return tuple(made)


SP500 = _lines(
    "US",
    "USD",
    """
    MMM AOS ABT ABBV ACN ADBE AMD AES AFL A APD ABNB AKAM ALB ARE ALGN ALLE LNT ALL GOOGL GOOG
    MO AMZN AMCR AEE AEP AXP AIG AMT AWK AMP AME AMGN APH ADI AON APA APO AAPL AMAT APP APTV
    ACGL ADM ARES ANET AJG AIZ T ATO ADSK ADP AZO AVY AXON BKR BALL BAC BAX BDX BRK-B BBY TECH
    BIIB BLK BX XYZ BE BNY BA BKNG BSX BMY AVGO BR BRO BF-B BG BXP CHRW CDNS CPT COF CAH CCL
    CARR CVNA CASY CAT CBOE CBRE CDW COR CNC CNP CF CRL SCHW CHTR CVX CMG CB CHD CIEN CI CINF
    CTAS CSCO C CFG CLX CME CMS KO CTSH COHR COIN CL CMCSA FIX COP ED STZ CEG COO CPRT GLW CPAY
    CSGP COST CRH CRWD CCI CSX CMI CVS DHR DRI DDOG DVA DECK DE DELL DAL DVN DXCM FANG DLR DG
    DLTR D DPZ DASH DOV DOW DHI DTE DUK DD ETN EBAY ECHO ECL EIX EW ELV EME EMR ETR EOG EQT EFX
    EQIX ERIE ESS EL EG EVRG P ES EXC EXE EXPE EXPD EXR XOM FFIV FDS FICO FAST FRT FDX FDXF FERG
    FIS FITB FSLR FE FISV FLEX F FTNT FTV FOXA FOX BEN FCX GRMN IT GE GEHC GEV GEN GNRC GD GIS
    GM GPC GILD GPN GL GDDY GS HAL HIG HAS HCA DOC HSIC HSY HPE HLT HD HONA HON HRL HST HWM HPQ
    HUBB HUM HBAN HII IBM IEX IDXX ITW ILMN INCY IR PODD INTC IBKR ICE IFF IP INTU ISRG IVZ INVH
    IQV IRM JBHT JBL JKHY J JNJ JCI JPM KDP KEY KEYS KMB KIM KMI KKR KLAC KHC KR LHX LH LRCX LVS
    LDOS LEN LII LLY LIN LYV LMT L LOW LULU LITE LYB MTB MPC MAR MRSH MLM MRVL MAS MA MKC MCD
    MCK MDT MRK META MET MTD MGM MCHP MU MSFT MAA MRNA MDLZ MPWR MNST MCO MS MOS MSI MSCI NDAQ
    NTAP NFLX NEM NWSA NWS NEE NKE NI NDSN NSC NTRS NOC NCLH NRG NUE NVDA NVR NXPI ORLY OXY OKTA
    ODFL OMC ON OKE ORCL OTIS PCAR PKG PLTR PANW PH PAYX PYPL PNR PEP PFE PCG PM PSX PNW PNC PPG
    PPL PFG PG PGR PLD PRU PTC PEG PSA PHM Q QCOM PWR DGX RL RJF RDDT O REG REGN RF RSG RMD RVTY
    HOOD ROK ROL ROP ROST RCL RTX SPGI CRM SNDK SBAC SLB STX SRE NOW SHW SPG SKYD SWKS SJM SW
    SNA SOLV SO LUV SWK SBUX STT STLD STE SYK SMCI SYF SNPS SYY TMUS TROW TTWO TPR TRGP TGT TEL
    TDY TER TSLA TXN TPL TXT TMO TJX TKO TSCO TT TDG TRV TRMB TFC TWLO TYL TSN USB UBER UDR ULTA
    UNP UAL UPS URI UNH UHS VLO VEEV VTR VLTO VRSN VRSK VZ VRTX VRT VTRS VICI V VST VMRK VMC
    VYLR WRB GWW WAB WMT DIS WM WAT WEC WFC WELL WST WDC WY WSM WMB WTW WDAY WYNN XEL XYL YUM
    ZBRA ZBH ZTS
    """,
)
NASDAQ100 = _lines(
    "US",
    "USD",
    """
    ADBE AMD ABNB ALNY GOOGL GOOG AMZN AEP AMGN ADI AAPL AMAT APP ARM ASML ALAB ADSK ADP AXON
    BKR BKNG AVGO CDNS CTAS CSCO CCEP CMCSA CEG CPRT CRWV COST CRWD CSX DDOG DXCM FANG DASH EXC
    FAST FER FTNT GEHC GILD HONA HON IDXX INTC INTU ISRG KDP KLAC LRCX LIN LITE MAR MRVL MELI
    META MCHP MU MSFT MSTR MRNA MDLZ MPWR MNST NBIS NFLX NVDA NXPI ORLY ODFL PCAR PLTR PANW PAYX
    PYPL PDD PEP QCOM REGN RKLB ROP ROST SNDK STX SHOP SPCX SBUX SNPS TMUS TTWO TER TSLA TXN TRI
    VRTX WMT WDC WDAY XEL
    """,
)
#: The FTSE 100 and the FTSE 250, less the three members London quotes in euros (BCG, MTLN,
#: PEY), a currency no line can state yet; then the five it quotes in dollars. Each is
#: charged a UK share's stamp duty on a purchase, an assumption not confirmed name by name:
#: a member registered outside the UK may pay none, and one registered in Ireland pays
#: Ireland's 1%, a rate no line can state yet (docs/STATUS.md, the data lane's).
FTSE350 = _lines(
    "LSE",
    "GBP",
    """
    III ABDN ADM AAF ALW AAL ANTO ABF AZN AUTO AV BAB BA BBY BARC BTRW BP BATS BLND BT-A BNZL
    BRBY CNA CCEP CCH CCC CTEC CRDA DCC DGE DPLM EZJ EDV EXPN FCIT FRES GAW GLEN GSK HLN HLMA
    HSX HWDN HSBA ICG IGG IMI IMB INF IAG ITRK INVP ITH JD BGEO KGF LAND LGEN LLOY LMP LSEG MNG
    MKS MRO NG NWG NXT PSON PSH PCT PRU RKT REL RTO RIO RR SGE SBRY SMT SGRO SVT SHEL SMIN SN
    SPX SSE STAN SDLF STJ TSCO BBOX ULVR UU VOD WEIR WTB WPP 3IN FOUR AAS ASL AEP ALFA ATT AMRQ
    AO APN ASHM AIE ASC ATYM ATG AGT AVON BME BGFD USA BNKR BAG AJB BWY BKG BHMG BYG BRGE BRSC
    BRWM BMY BOY BREE BPT BUT BYIT CLDN CGT CWR CHG CSN CTY CKN CBG CMCX COA CORD COST CWK CURY
    CVSG DLN DSCV DOM DRX DOCS DNLM EDIN EWI ELM ENOG ENQ ENT ESCT EWG FCSS FEML FEV FSV FGT FGP
    FGEN FSG FRAS FCH GFRD GAMA GCP GEN GNS DATA GSCT GDWN GFTU GRI GPE UKW GNC GRG HFD HMSO
    HANA HBR HVPE HAS HTWS HFEL HSL HRI HGT HICL HIK HILS HFG HOC BOWL HTG ICGT INCH IHP INPP
    IWG IAD IPO ITV JMAT JSG JAM JCH JEMI JMGI JEDT JEGI JGGI JFJ JUP KNOS KLR KIE LRE LWDB EMG
    MEGP MRC MRCH MNO MTRO PAGE MAB MTO GROW MNDI MNKS MONY MOON MGAM MGNS MUT MYI NCC NBPE N91
    NAIT NAS OCI OCDO OSB OXB OXIG ONT PHI PAF PINT PIN PAG PPET PNN PSN PNL PETS PTEC PLUS PCGH
    POLN PPH PFD PHP PRN QQ QLT RNK RPI RAT RSW RHIM RMV RCP ROSE ROR RS1 RICA SAFE SAGA SVS ATR
    SDP SOI SAIN SEIT SEQI SSIT SRP SHC SHAW SRE SCT SPI SSPG SUPR SYNC THRL TATE TW TBCG TEP
    TMPL TEM TRIG THG TCAP TRN TPK TRY TRST TFIF UTG UEM VSVS VCT VEIL VOF VTY VLX FAN WOSG JDW
    SMWH WIX WIZZ WKP WWH XPP XPS YNGA ZIG
    """,
    STAMP_DUTY,
) + _lines("LSE", "USD", "BPCR CPG IHG MNTN RTW", STAMP_DUTY)
#: The 200 with the highest median value traded a day over sixty sessions to 12 November 2026,
#: from a field of 330 plain funds and funds built to make two or three times their market's
#: daily move. Not in the field: a fund that moves against its market (a line's leverage is
#: one or more), one whose multiple has changed, one on a single share, one tracking volatility.
ETFS = _lines(
    "US",
    "USD",
    """
    SPY QQQ SOXL:3 IWM VOO IVV SOXX SMH TQQQ:3 HYG GLD LQD TLT EWY SGOV XLE IBIT GDX XLF DIA RSP
    XLV XLK XBI EEM XLI EFA EWZ VTI MUB XLU AGG KRE VTEB XLP SPYM BIL IEF SLV VCIT IGV QQQM IEMG
    IEFA SCHD USO BITO XLY BND EMB VEA XLC ETHA IYR VTV FXI XLB XOP IJH IWF GDXJ VUG USHY VGT
    EWT SPXL:3 BOXX VCSH IJR VXUS MDY IWD VWO ARKK VNQ MBB VT IAU GLDM QLD:2 JPST IBB KWEB EWJ
    JEPQ ACWI SHY VGIT SHV SCHX JNK XRT USFR VGSH SPTL SCHB XLRE UPRO:3 SCHG MTUM TNA:3 MAGS
    SPMO SPYG GOVT JEPI INDA VIG SCHF IUSB UNG BKLN FBTC ITOT SSO:2 ARKG SPIB TIP IVW IEI VEU
    BNDX COPX ITB QUAL VO TLH CIBR XHB BSV VGK ITA IGSB VGLT VTWO VYM USMV IWB XME MINT IGIB
    AVUV CGDV SCHP IYW ACWX IWR IWO TMF:3 VB BIV VTIP SPLV DYNF IXUS SPDW IVE URA IWN UDOW:3 EFV
    IHI SCHA CGGR SPYV VONG HDV DGRO SCHE FLOT SPMD JETS KBE OIH TECL:3 ICLN SGOL SCHV USIG BNO
    SCHO STIP ASHR EDV VMBS TFLO GBTC SILJ PFF PDBC VLUE SPSB TBIL EWC MCHI SIVR VDE QYLD SPHQ
    IUSG
    """,
)
#: Every ticker once: a share on two lists (most of the Nasdaq 100) is one line.
UNIVERSE = tuple(dict.fromkeys(SP500 + NASDAQ100 + FTSE350 + ETFS))


def keep(
    root: Path,
    day: date,
    lines: Iterable[Line] = UNIVERSE,
    ask: Callable[[Line, date], tuple[Bar, ...]] = archive.fetch,
) -> dict[Line, Parked]:
    """Fetch each ticker's bars before day and clean them into the research store at root, in
    its venue's folder: one ticker at a time, so the whole list is never held at once. A
    ticker whose bars hold a fault the store parks for is parked with its reason, its sound
    bars kept; one the archive refuses today keeps no bars, as in the desk's own store, so
    none from an earlier day is read as today's. The rest carry on."""
    parked: dict[Line, Parked] = {}
    for line in lines:
        for found in store.prepare(root / line.venue, archive.gather([line], day, ask), day):
            parked[line] = found
    return parked


#: Research's rule for a move the store parks for (docs/DECISIONS.md, the data lane's). Read
#: on the list's 406 such moves of 13 November 2026: a fall made wholly between two sessions
#: on under this many times the usual value traded looks each time like a change of scale (a
#: split the archive did not adjust, a demerger, a special payment: fifteen, the heaviest on
#: 2.3 times, none confirmed from a second source); the lightest real fall came on 2.8. Two
#: that look like changes of scale, on 2.5 and 4.4 times, are read as losses. The usual is
#: the median of the USUAL sessions before. The number was chosen looking at that one list.
HEAVY, USUAL = Decimal("2.5"), 20


@dataclass(frozen=True)
class History:
    """A ticker's bars as research reads them: its longest run on one scale of price. It
    stops short of the store's last day when a day of `rescaled` is later than its last bar:
    it is then no guide to today. Which run is longest can change as sessions gather."""

    bars: tuple[Bar, ...]  #: oldest first, none either side of a change of scale
    #: The days among them of an unconfirmed move, read as the market's. One made within a
    #: day is named on that day and on the next, whose bar sits far from where the day began.
    moves: tuple[date, ...]
    rescaled: tuple[date, ...]  #: every change of scale in what the store keeps for it


def _rescaled(before: Sequence[Bar], bar: Bar) -> bool:
    """An unconfirmed move is a change of the price's scale, not a move a holder lived
    through, when it was made wholly between two sessions and it is a rise, or a fall on
    ordinary trading. A rise is never believed unconfirmed: the desk only buys, so counting
    a false windfall flatters a study and disbelieving a real one cannot. A fall is
    disbelieved only on trading under HEAVY times a usual that is known: forgetting a real
    loss flatters every strategy, so a fall with no usual volume to judge it by is believed.
    The price of disbelief is the bars on the shorter side of the move, which go unread."""
    last = before[-1].close
    usual = median(b.close * b.volume for b in before[-USUAL:])
    quiet = bar.close * bar.volume < HEAVY * usual
    return bar.low > last * store.JUMP or (bar.high * store.JUMP < last and quiet)


def read(root: Path, line: Line) -> History:
    """A ticker's bars from the research store at root, parked or not. No trade is priced
    across a change of scale: the bars are the longest run between two (the later of two as
    long), and the unconfirmed moves inside it are named, so that a verdict can say how many
    it was held through. A ticker the archive refused has no bars to read."""
    bars = store.read(root / line.venue, line.symbol)
    at = {bar.day: n for n, bar in enumerate(bars)}
    moved = [at[day] for day in store.moves(line, bars)]
    cuts = [n for n in moved if _rescaled(bars[:n], bars[n])]
    edges = [0, *cuts, len(bars)]
    start, end = max(zip(edges, edges[1:], strict=False), key=lambda run: (run[1] - run[0], run))
    listed = tuple(bars[n].day for n in moved if start < n < end)
    return History(bars[start:end], listed, tuple(bars[n].day for n in cuts))
