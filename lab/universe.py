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

import hashlib
import os
import sys
from collections.abc import Callable, Iterable, Sequence
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

from desk import archive, bars, store
from desk import bars as database
from desk.bars import Source
from desk.lines import LINES, NO_TAX, STAMP_DUTY, Line
from desk.store import Bar, Fault, Parked
from lab import universe_history
from lab.universe_parts import HEAVY as HEAVY
from lab.universe_parts import USUAL as USUAL
from lab.universe_parts import History as History
from lab.universe_parts import breadth as breadth
from lab.universe_parts import matrix as matrix
from lab.universe_parts import read as read


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
#: The S&P MidCap 400 and, below it, the S&P SmallCap 600 as Wikipedia listed them on 22 November
#: 2026 (the 13 November ruling: the full list comes after the grid's first pass). Members today
#: only, like the lists above; a ticker on two lists is one line.
MIDCAP400 = _lines(
    "US",
    "USD",
    """
    AA AAL AAON ACI ACM ADC AEIS AFG AGCO AGNC AHR AIT ALGM ALK ALLY ALSN ALV AM AMG AMH AMKR AN
    ANF APG APPF AR ARMK ARW ARWR ASB ASH ATI ATR AVAV AVNT AVT AVTR AXTA AYI BAH BBWI BC BCO
    BDC BHF BILL BIO BJ BMRN BRKR BROS BRX BSY BTSG BURL BWA BWXT BYD CACI CAR CART CAVA CBSH
    CBT CCK CDE CDP CELH CFR CG CGNX CHDN CHE CHH CHRD CHWY CHYM CLF CLH CMC CNH CNM CNO CNX
    COKE COLB COLM CORT CR CRBG CROX CRS CRUS CSL CTRE CTVA CUBE CUZ CVLT CW CXT CYTK DAR DBX
    DCI DINO DKS DLB DOCN DOCS DOCU DT DTM DUOL DY EAT EEFT EGP EHC ELAN ELF ELS ENS ENSG ENTG
    EPR EQH ESAB ESNT EVR EWBC EXEL EXLS EXP EXPO FAF FBIN FCFS FCN FFIN FHI FHN FIVE FLG FLR
    FLS FN FNB FND FNF FORM FOUR FR FTI G GAP GATX GBCI GEF GGG GHC GKOS GLPI GME GMED GNTX GPK
    GWRE GXO H HAE HALO HGV HIMS HL HLI HLNE HOG HOMB HQY HR HRB HUBS HWC HXL HZN IBOC IDA IDCC
    IESC INGR IPGP IRT ITT JAZZ JEF JHX JLL KBH KBR KD KEX KNF KNSL KNX KRC KRG KRYS KTOS LAD
    LAMR LEA LECO LFUS LIVN LNTH LOPE LPX LSCC LSTR M MANH MAT MEDP MIDD MKSI MLI MMS MOG-A MOH
    MORN MP MSA MSM MTDR MTG MTN MTSI MTZ MUR MUSA MZTI NBIX NEU NFG NJR NLY NNN NOV NOVT NTNX
    NVST NVT NXST NXT NYT OC OGE OGS OHI OLED OLLI ONB ONTO OPCH ORA ORI OSK OVV OZK PAG PATH PB
    PBF PCTY PEGA PEN PFGC PII PINS PK PLNT PNFP POR POST PPC PR PRI PSN PVH QLYS R RBA RBC REXR
    RGA RGEN RGLD RH RLI RMBS RNR ROIV RPM RRC RRX RS RYAN RYN SAIA SAIC SANM SARO SBRA SCI SEIC
    SF SFM SGI SHC SIGI SIRI SITM SLAB SLGN SLM SMG SMTC SN SNX SOLS SON SPXC SR SSB SSD ST STAG
    STRL STWD SUI SWX SYNA TCBI TEX THC THG THO TKR TLN TNL TOL TOST TREX TRU TTC TTEK TTMI TXNM
    TXRH UBSI UFPI UGI ULS UMBF UNM USFD UTHR VAL VC VFC VIAV VICR VLY VMI VNO VNOM VNT VOYA VVV
    WAL WCC WEX WFRD WH WHR WING WLK WMG WMS WPC WSO WTFC WTRG WTS WWD XPO XRAY YETI ZION
    """,
)
SMALLCAP600 = _lines(
    "US",
    "USD",
    """
    AAMI AAP AAT ABCB ABG ABM ABR ACA ACAD ACHC ACIW ACLS ACMR ACT ADAM ADEA ADIG ADMA ADNT ADT
    ADUS AEO AESI AGNT AGO AGX AGYS AHCO AIN AIR AKR ALG ALGT ALHC ALKS ALRM AMN AMPH AMR AMRX
    AMSF AMTM ANDE ANIP AORT AOSL APAM APLE APOG ARCB ARLO AROC ARR ASO ASTE ASTH ATEN ATMU AUB
    AVA AWI AWR AX AZTA AZZ BANC BANF BANR BBT BCC BCPC BFAM BFH BFS BGC BHE BJRI BKE BKU BL
    BLFS BLKB BMI BNL BOH BOOT BOX BRC BTU BXMT CACC CAG CAKE CALM CALX CALY CARG CASH CATY CBRL
    CBU CC CCOI CCS CE CENT CENTA CENX CERT CFFN CHCO CHEF CLSK CNK CNMD CNR CNS CNXC CNXN COCO
    COHU COLL CON CORT COTY CPB CPF CPK CRC CRGY CRI CRK CRSR CRVL CSR CSW CTS CUBI CURB CVBF
    CVCO CVI CVSA CWEN CWEN-A CWK CWST CWT CXM CXW CZR DAN DAVE DBD DCH DCOM DEA DEI DFH DFIN
    DGII DIOD DLX DMC DNOW DORM DRH DV DXC DXPE EAT EBC ECG ECPG EFC EFOR EGBN EIG EMN ENOV ENPH
    ENR ENVA EPAC EPAM EPC EPRT ESE ESI ETSY EVTC EXTR EYE EZPW FA FBK FBNC FBP FBRT FCF FCPT
    FELE FFBC FG FHB FIBK FIVN FIZZ FLO FMC FORM FOXF FRPT FSS FTDR FTRE FUL FULT FUN GBX GEO
    GFF GIII GKOS GNL GNW GO GOLF GPI GPOR GRBK GSHD GT GTES GTM GTY GVA HAFC HASI HAYW HCC HCI
    HCSG HE HFWA HIW HLIT HLX HMN HNI HOPE HP HRMY HSTM HTH HTLD HTO HUBG HWKN HZO IART IBP ICHR
    ICUI IIPR INDB INDV INSP INSW INVA INVX IOSP IPAR IRDM ITGR ITRI IVT JBGS JBLU JBSS JBTM
    JJSF JOE JXN KAI KALU KFY KGS KLIC KMPR KMT KMX KN KNTK KOP KRMN KSS KTB KWR LAUR LAZ LBRT
    LCII LEG LEU LFST LGIH LIF LGND LKFN LKQ LMAT LNC LNN LPG LQDA LQDT LRN LTC LTH LUMN LW LXP
    LYFT LZ LZB MAC MAN MARA MATW MATX MBC MBGL MBIN MC MCRI MCY MD MDU MFP MGEE MGY MHK MHO MIR
    MKTX MLKN MMI MMSI MPT MRCY MRP MRTN MSEX MSGK MTCH MTH MTRN MTUS MTX MWA MXL MYRG NABL NATL
    NAVI NBHC NBTB NE NEO NEOG NGVT NHC NHI NIC NMIH NOG NPK NPO NSIT NSP NSSC NTCT NTST NWBI
    NWL NWN NX NXRT OFG OGN OI OII OMCL OPLN OSIS OSW OTTR OUT PAHC PARR PAYC PAYO PATK PBH PBI
    PCRX PDFS PEB PECO PENG PENN PFBC PFS PGNY PHIN PI PIPR PJT PLAB PLMR PLUS PLXS PMT POOL
    POWI POWL PPLI PRDO PRG PRGO PRGS PRIM PRK
    PRKS PRLB PRSU PRVA PSMT PTCT PTEN PTGX PTON PZZA QDEL QNST QRVO QTWO RAMP RAL RCUS RDN RDNT
    RELY RES REYN REX REZI RHI RHP RITM RNG RNST ROAD ROCK ROG RRR RSI RUN RUSHA RXO SAFE SABR
    SAFT SAH SBCF SBH SBSI SCHL SCL SCSC SDGR SEDG SEI SEZL SFBS SFNC SHAK SHEN SHO SHOO SIG SKT
    SKY SKYW SLG SLVM SM SMP SMPL SNDR SNEX SONO SPHR SPNT SPSC SRPT STAA STBA STC STEP STRA
    SUPN SXI SXT TALO TBBK TDC TDS TDW TFIN TFX TGTX THRM TILE TMDX TMP TNC TNDM TPC
    TR TRIP TRMK TRN TRNO TRST TRUP UA UAA UCB
    UCTT UE UFCS UFPT UNF UNFI UNIT UPBD UPWK URBN USLM USPH UTI UTL UVV VAC VCEL VCTR VCYT VECO
    VGNT VIR VIRT VRRM VRTS VSAT VSEC VSH VSNT VSTS VSXY VTOL VVX VYX WABC WAFD WAY WD WDFC WEN
    WERN WGO WHD WINA WKC WLY WOR WRBY WRLD WS WSBC WSC WSFS WT WU WWW XHR XNCR XPEL YELP YOU ZD
    ZWS
    """,
)
#: London's yardstick, the iShares FTSE 100, which the ladder sets a London line beside: studied,
#: never traded here (it is also a trading line, so the instrument master's own line).
YARDSTICKS = _lines("LSE", "GBP", "ISF")
#: Every ticker once: a share on two lists (most of the Nasdaq 100) is one line.
UNIVERSE = tuple(
    dict.fromkeys(SP500 + NASDAQ100 + MIDCAP400 + SMALLCAP600 + FTSE350 + ETFS + YARDSTICKS)
)
#: SPY, studied as the S&P 500's own history from its first session, 29 January 1993, and never
#: traded: a reference series (R-RUNGS-5, R-PAPER-16), kept apart from the traded bars above.
REFERENCE = tuple(line for line in ETFS if line.symbol == "SPY")


def keep_reference(
    root: Path,
    day: date,
    ask: Callable[..., tuple[Bar, ...]] = archive.fetch,
) -> dict[Line, tuple[Fault, ...]]:
    """Fetch each reference series from the archive's reach back to its first session, before
    day, and keep it in the long database beside the live file at root as traded, with the
    faults found."""
    return {
        line: archive.keep_reference(
            root / bars.LIVE, line, ask(line, day, since=archive.REFERENCE_SINCE)
        )
        for line in REFERENCE
    }


def _older(path: Path, line: Line) -> tuple[Bar, ...]:
    """The bars the database holds for the line, to stand under the archive's: a day the
    archive no longer gives, or never did, keeps the bar it entered with."""
    try:
        return database.daily(path, line)
    except (LookupError, FileNotFoundError):
        return ()


def keep(
    path: Path,
    day: date,
    lines: Iterable[Line] = UNIVERSE,
    ask: Callable[[Line, date], tuple[Bar, ...]] = archive.fetch,
    second: Callable[[Line, date], tuple[Bar, ...]] | None = None,
) -> dict[Line, Parked]:
    """Fetch each ticker's bars before day, judge them by the one store's checks and let the
    sound ones into the history database at path through its one writer, one ticker at a time,
    so the whole list is never held at once. A day only the second source gives enters under
    its own source. A ticker whose bars hold a fault the store parks for is parked with its
    reason, its sound bars kept; one the archive refuses today adds nothing, so none from an
    earlier day is read as today's. The rest carry on."""
    parked: dict[Line, Parked] = {}
    for line in lines:
        answer = archive.gather([line], day, ask)[line]
        given = set() if isinstance(answer, store.Refused) else {bar.day for bar in answer}
        shelf = _older(path, line) if second is None else second(line, day)
        under = [bar for bar in shelf if bar.day not in given]
        kept, _, park = store.judge(line, answer, day, shelf=under)
        lower = [bar for bar in kept if bar.day not in given]
        universe_history.fill(path, line, Source.MATRIX_DAILY, lower)
        universe_history.fill(path, line, Source.ARCHIVE, (b for b in kept if b.day in given))
        if park:
            parked[line] = park
    return parked


def _held(path: Path, line: Line) -> int:
    """How many bars the database holds for the line; none before its first."""
    return len(_older(path, line))


def _mended(
    path: Path,
    day: date,
    line: Line,
    ask: Callable[[Line, date], tuple[Bar, ...]],
    second: Callable[[Line, date], tuple[Bar, ...]] | None,
) -> tuple[int, str]:
    """Keep a line; if it is a yardstick missing sessions, name them, and with a second source
    fill them (they enter the database, so every later refresh finds them held) and keep
    again. Returns the lines parked, and the days that stayed missing, named."""
    parked = len(keep(path, day, [line], ask))
    lost = universe_history.missing(path, line, day) if line in YARDSTICKS else ()
    if lost and second is not None:
        parked = len(keep(path, day, [line], ask, second))
        lost = universe_history.missing(path, line, day)
    return (
        parked,
        f"; yardstick {line.symbol} has no bar on {', '.join(map(str, lost))}" if lost else "",
    )


def refresh(
    path: Path,
    day: date,
    lines: Iterable[Line] = UNIVERSE,
    ask: Callable[[Line, date], tuple[Bar, ...]] = archive.fetch,
    second: Callable[[Line, date], tuple[Bar, ...]] | None = None,
) -> str:
    """Keep each line into the history database at path through the one writer, one at a time
    (a stopped run resumes by running again), and say what it did: lines refreshed, bars added
    (a line's gain on what it held; a bar is never invented or restated, so a day's second run
    adds none) and lines parked. A yardstick with a missing session is a named data fault,
    filled from the second source when one is given."""
    refreshed = added = parked = 0
    faults = ""
    for line in lines:
        before = _held(path, line)
        more, note = _mended(path, day, line, ask, second)
        parked += more
        faults += note
        added += max(0, _held(path, line) - before)
        refreshed += 1
    done = f"{refreshed} lines refreshed, {added} bars added, {parked} parked"
    return f"research refresh: {done}{faults}"


LISTS = {
    "sp500": SP500,
    "nasdaq100": NASDAQ100,
    "midcap400": MIDCAP400,
    "smallcap600": SMALLCAP600,
    "ftse350": FTSE350,
    "funds": ETFS,
}


def nightly(
    data: Path,
    day: date,
    lines: Sequence[Line] = UNIVERSE,
    ask: Callable[[Line, date], tuple[Bar, ...]] = archive.fetch,
    second: Callable[[Line, date], tuple[Bar, ...]] | None = None,
    noon: Callable[[Path], str] | None = None,
) -> str:
    """The night's work: refresh every line into the history database under data, and write
    REFLECTS.txt in data/grid/store: the day, each list's size and a fingerprint of the
    tickers, so a reader knows which day and which list the database reflects. Given `noon`, the
    pound's noon rates are let in last, and its one line is said."""
    home = data / "grid" / "store"
    said = refresh(data / bars.LIVE, day, lines, ask, second)
    names = sorted(f"{line.venue}:{line.symbol}" for line in lines)
    finger = hashlib.sha256(" ".join(names).encode()).hexdigest()[:12]
    sizes = " ".join(f"{name}={len(found)}" for name, found in LISTS.items())
    held = (f"day {day}", f"lines {len(names)} {sizes}", f"fingerprint {finger}")
    home.mkdir(parents=True, exist_ok=True)
    (home / "REFLECTS.txt").write_text(chr(10).join((*held, "")), encoding="utf-8")
    return f"{said}; {noon(data / bars.LIVE)}" if noon else said


def import_history(data: Path, day: date) -> str:
    """The ladder's pound table under data, let into the history database there; the
    yardsticks' missing sessions are named."""
    return universe_history.run(
        data / bars.LIVE,
        data / "ladder" / "pound.jsonl",
        (*YARDSTICKS, *REFERENCE),
        day,
    )


if __name__ == "__main__":
    DATA = Path(os.environ.get("KESTREL2_DATA") or sys.exit("universe: no KESTREL2_DATA"))
    TODAY = datetime.now(UTC).date()
    if sys.argv[1:] == ["history"]:
        sys.stdout.write(import_history(DATA, TODAY) + chr(10))
    elif sys.argv[1:2] == ["nightly"]:
        other = matrix(Path(sys.argv[2])) if len(sys.argv) > 2 else None
        sys.stdout.write(nightly(DATA, TODAY, second=other, noon=universe_history.noon) + chr(10))
    elif sys.argv[1:] == ["noon"]:
        sys.stdout.write(universe_history.noon(DATA / bars.LIVE) + chr(10))
    else:
        other = matrix(Path(sys.argv[2])) if len(sys.argv) > 2 else None
        sys.stdout.write(refresh(Path(sys.argv[1]), TODAY, second=other) + chr(10))
