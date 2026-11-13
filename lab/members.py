"""members - THE LISTS' PAST MEMBERS: who was on a published list on a past day, so that a
study of the past is not the survivors' alone. The research list (`lab/universe.py`) holds
today's members only; of the S&P 500 of January 2010, 281 of 500 are still on it.

A list on a past day is today's list with every change since undone, newest first. A member
then is either still listed today, and is today's line, whose bars the research store keeps;
or it has left, and is only a name: the free archive keeps no bars for most of them, so a
study can count them and say so, and cannot yet trade them.

The record is Wikipedia's table of each list's changes, read on 13 November 2026 and
corrected by hand where it contradicted itself or today's list (docs/DECISIONS.md, the data
lane's). It is one unofficial source, and nothing proves it complete. Three rules name a
member:

- a company is named by the last ticker it carried on the list, so a change of ticker is no
  change of member (Facebook joined as META);
- a leaver whose ticker another member carried later is named with the year it left: Q.2011
  is Qwest, not the Q of today, so no stranger's bars are read as its own;
- a change counts from its day: the joiner is a member on it, the leaver is not. The source
  sometimes gives the last day of the old member instead, so a day here can be one out.

Still owed: the FTSE 350, whose changes no free page lists, and the funds, a list this desk
measured itself on one day. Asked for either, `on` refuses."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from desk.lines import Line
from lab import universe

#: The days a list can be asked for: from the start of the record to the day of today's list.
FIRST, LAST = date(2010, 1, 1), date(2026, 11, 13)
#: The lists of `universe` whose past members are not recorded yet.
OWED = ("FTSE350", "ETFS")


@dataclass(frozen=True)
class Change:
    """One member joining a list, or leaving it, from its day on."""

    day: date
    symbol: str
    joined: bool


@dataclass(frozen=True)
class Members:
    """A list's members on one day."""

    day: date
    listed: tuple[Line, ...]  #: still on the list today, in today's order: today's lines
    left: tuple[str, ...]  #: gone since, in order of name: no line, and no bars kept


@dataclass(frozen=True)
class Record:
    """Today's list and every change that made it, newest first. One that contradicts the
    list, or itself, cannot be made: a member cannot join twice running, or leave when out."""

    today: tuple[Line, ...]
    changes: tuple[Change, ...]

    def __post_init__(self) -> None:
        self.symbols(date.min)

    def symbols(self, day: date) -> set[str]:
        """The members on day, by name: today's, with every change after day undone."""
        names = {line.symbol for line in self.today}
        for change in self.changes:
            if change.day <= day:
                break
            if change.joined != (change.symbol in names):
                does = (
                    "joins a list it is not on afterwards"
                    if change.joined
                    else "leaves a list it is on afterwards"
                )
                raise ValueError(f"{change.symbol} on {change.day}: {does}")
            names ^= {change.symbol}
        return names


def changes(text: str) -> tuple[Change, ...]:
    """The changes written as days, newest first, each followed by its joiners (+) and its
    leavers (-)."""
    made: list[Change] = []
    day = date.max
    for word in text.split():
        if word[0] in "+-":
            made.append(Change(day, word[1:], word[0] == "+"))
        elif date.fromisoformat(word) >= day:
            raise ValueError(f"{word}: a day out of order, the newest comes first")
        else:
            day = date.fromisoformat(word)
    return tuple(made)


RECORDS = {
    "SP500": Record(
        universe.SP500,
        changes(
            """
            2026-10-30 +OKTA -KVUE 2026-10-06 +TWLO -WBD -CTVA 2026-10-01 +VYLR 2026-09-21 +BE
            -TAP +P -TTD +ILMN -BLDR 2026-08-18 +RDDT -AVB 2026-08-05 +FERG -EA 2026-06-30 -CAG
            2026-06-29 +HONA 2026-06-22 +MRVL -POOL +FLEX -CPB 2026-06-02 -EPAM 2026-06-01 +FDXF
            2026-05-07 +VEEV -CTRA 2026-04-09 +CASY -HOLX 2026-03-23 +VRT -MTCH +LITE -MOH +COHR
            -LW +ECHO -PAYC 2026-02-09 +CIEN -DAY 2025-12-22 +CRH -LKQ +CVNA -SOLS +FIX -MHK
            2025-12-11 +ARES -K 2025-11-28 +SNDK -IPG 2025-11-04 -EMN 2025-11-03 +Q 2025-10-31
            -KMX 2025-10-30 +SOLS 2025-09-22 +EME -ENPH +HOOD -CZR +APP -MKTX 2025-08-28 +IBKR
            -WBA 2025-07-23 +XYZ -HES 2025-07-18 +TTD -ANSS 2025-07-09 +DDOG -JNPR 2025-05-19
            +COIN -DFS 2025-03-24 +DASH -BWA +TKO -TFX +WSM -CE +EXE -FMC 2024-12-23 +APO -QRVO
            +WDAY -AMTM +LII -CTLT 2024-11-26 +TPL -MRO 2024-10-01 -BBWI 2024-09-30 +AMTM
            2024-09-23 +PLTR -AAL +DELL -ETSY +ERIE -BIO 2024-06-24 +KKR -RHI +CRWD -CMA +GDDY
            -ILMN 2024-05-08 +VST -PXD 2024-04-03 -XRAY -VFC 2024-04-02 +GEV 2024-04-01 +SOLV
            2024-03-18 +SMCI -WHR +DECK -ZION 2023-12-18 +UBER -SEE +JBL -ALK +BLDR -SEDG
            2023-10-18 +HUBB -OGN +LULU -ATVI 2023-10-03 -DXC 2023-10-02 +VLTO 2023-09-18 +BX
            -LNC +ABNB -NWL 2023-08-25 +KVUE -AAP 2023-06-20 +PANW -DISH 2023-05-04 +AXON -FRC
            2023-03-20 +FICO -LUMN 2023-03-15 +BG -SBNY +PODD -SIVB 2023-01-05 -VNO 2023-01-04
            +GEHC 2022-12-22 +STLD -ABMD 2022-12-19 +FSLR -FBHS -MBC 2022-12-15 +MBC 2022-11-01
            +ACGL -TWTR 2022-10-12 +TRGP -NLSN 2022-10-03 +PCG -CTXS +EQT -DRE 2022-09-19 +CSGP
            -PVH +INVH -PENN 2022-06-21 -UA +KDP -UAA +ON -IPGP 2022-06-08 +VICI -CERN
            2022-04-11 +WBD -DISCA -DISCK 2022-04-04 +CPT -PBCT 2022-03-02 +MOH -INFO 2022-02-15
            +NDSN -XLNX 2022-02-03 -GPS 2022-02-02 +CEG 2021-12-20 +SBNY -LEG +SEDG -HBI +FDS
            -WU 2021-12-14 +EPAM -KSU 2021-09-20 +MTCH -PRGO +DAY -UNM +BRO -NOV 2021-08-30
            +TECH -MXIM 2021-07-21 +MRNA -ALXN 2021-06-04 -HFC 2021-06-03 +OGN 2021-05-14 +CRL
            -FLIR 2021-04-20 +PTC -VAR 2021-03-22 +NXPI -FLS +PENN -SLG +GNRC -XRX +CZR -VNT
            2021-02-12 +MPWR -FTI 2021-01-21 +TRMB -CXO 2021-01-07 +ENPH -TIF 2020-12-21 +TSLA
            -AIV 2020-10-12 -NBL 2020-10-09 +VNT 2020-10-07 +POOL -ETFC 2020-09-21 +ETSY -HRB
            +TER -COTY +CTLT -KSS 2020-06-22 +BIO -ADS +TDY -HOG +TYL -JWN 2020-05-22 +WST -HP
            2020-05-12 +DPZ -CPRI +DXCM -AGN 2020-04-06 -M -RTN 2020-04-03 +OTIS +CARR
            2020-03-03 +IR -XEC 2020-01-28 +PAYC -WCG 2019-12-23 +LYV -AMG +ZBRA -TRIP +STE -MAC
            2019-12-09 +ODFL -STI 2019-12-05 +WRB -VIAB 2019-11-21 +NOW -CELG 2019-10-03 +LVS
            -NKTR 2019-09-26 +NVR -JEF 2019-09-23 +CDW -TSS 2019-08-09 +LDOS -APC +IEX -FL
            2019-07-15 +TMUS -RHT 2019-07-01 +MKTX -LLL 2019-06-07 +AMCR -MAT 2019-06-03 +CTVA
            -FLR 2019-04-02 +DOW -BHF 2019-03-20 -TFCFA -TFCF 2019-03-19 +FOXA +FOX 2019-02-27
            +WAB -GT 2019-02-15 +ATO -NFX 2019-01-18 +TFX -PCG 2019-01-02 +FRC -SCG 2018-12-24
            +CE -ESRX 2018-12-03 +LW -COL +MXIM -AET +FANG -SRCL 2018-11-13 +JKHY -EQT
            2018-11-06 +KEYS -CA 2018-10-11 +FTNT -EVHC 2018-10-01 +ROL -ANDV 2018-09-14 +WCG
            -XL 2018-08-28 +ANET -GGP 2018-07-02 +CPRT -DPS 2018-06-20 +CPAY -TWX 2018-06-18 +BR
            -RRC +HFC -AYI 2018-06-07 +TWTR -MON 2018-06-05 +EVRG -NAVI 2018-05-31 +ABMD -WYN
            2018-04-04 +MSCI -CSRA 2018-03-19 +TTWO -SIG +SIVB -PDCO +NKTR -CHK 2018-03-07 +IPGP
            -SNI 2018-01-03 +HII -BCR 2017-10-13 +NCLH -LVLT 2017-09-18 +CDNS -SPLS 2017-09-01
            +DD -DOW.2017 +SBAC -DD.2017 2017-08-29 +IQV -WFM 2017-08-08 +BHF -AN 2017-07-26
            +DRE -RIG +AOS -BBBY +PKG -MUR +RMD -MNK +MGM -RAI 2017-07-07 +BKR -BHI 2017-06-19
            +HLT -YHOO +ALGN -TDC +ANSS -R +EG -MJN 2017-06-02 +INFO -TGNA 2017-04-05 +IT -DNB
            2017-04-04 +DXC -SWN 2017-03-20 +AMD -URBN +RJF -FTR +ARE -FSLR 2017-03-16 +SNPS
            -HAR 2017-03-13 +DISH -LLTC 2017-03-02 +REG -ENDP 2017-03-01 +CBOE -PBI 2017-02-28
            +INCY -SE 2017-01-05 +IDXX -STJ 2016-12-02 +MAA -OI +EVHC -LM 2016-09-30 +COTY -DO
            2016-09-22 +COO -HOT 2016-09-08 +CHTR -EMC 2016-09-06 +MTD -TYC 2016-07-05 +FTV
            -CPGX 2016-07-01 +LNT -GAS +ALB -TE 2016-06-22 +FBHS -CVC 2016-06-03 +TDG -BXLT
            2016-05-31 +AJG -CCE 2016-05-23 +LKQ -ARG 2016-05-18 +DLR -TWC 2016-05-13 +ALK
            -SNDK.2016 2016-05-03 +AYI -ADT 2016-04-25 +GPN -GME 2016-04-18 +ULTA -THC
            2016-04-08 +UA 2016-04-04 +FL -CAM 2016-03-30 +HOLX -POM +CNC -ESV 2016-03-07 +UDR
            -GMCR 2016-03-04 +AWK -CNX 2016-02-22 +CXO -PCL 2016-02-01 +CFG -PCP +FRT -BRCM
            2016-01-19 +EXR -ACE 2016-01-05 +WTW -FOSL 2015-12-29 +CHD -ALTR 2015-12-15 -CMCSK
            2015-12-01 +CSRA -CSC 2015-11-19 +ILMN -SIAL 2015-11-18 +SYF -GNW 2015-11-02 +HPE
            -HCBK 2015-10-07 +VRSK -JOY 2015-09-18 +CMCSK +TFCF +NWS 2015-09-02 +UAL -HSP
            2015-08-28 +ATVI -PLL 2015-07-29 +SIG -DTV 2015-07-20 +PYPL -NE 2015-07-08 +AAP -FDO
            2015-07-06 +KHC -KRFT 2015-07-02 +CPGX -ATI 2015-07-01 +JBHT -TEG +BXLT -QEP
            2015-06-11 +QRVO -LO 2015-04-07 +O -WIN 2015-03-23 +AAL -AGN.2015 +EQIX -DNR +SLG
            -NBR +HBI -AVP 2015-03-18 +HSIC -CFN 2015-03-12 +SWKS -PETM 2015-01-27 +HCA -SWY
            +ENDP -COV 2014-12-05 +RCL -BMS 2014-11-05 +LVLT -JBL 2014-09-20 +URI -BTU +UHS -GHC
            2014-08-18 +MNK -RDC 2014-08-06 +DISCK 2014-07-02 +MLM -X 2014-07-01 +AMG -FRX
            2014-06-20 +XEC -IGT 2014-05-08 +AVGO -LSI 2014-05-01 +UAA -BEAM +NAVI -SLM
            2014-04-03 +GOOG 2014-04-02 +ESS -CLF 2014-03-21 +GMCR -WPX 2014-01-24 +TSCO -LIFE
            2013-12-23 +ADS -ANF +MHK -JDSU +META -TER 2013-12-10 +GGP -MOLX 2013-12-02 +ALLE
            -JCP 2013-11-13 +CPRI -NYX 2013-10-29 +RIG -DELL.2013 2013-09-20 +VRTX -AMD +AME
            -SAI 2013-09-10 +DAL -BMC 2013-07-08 +NLSN -S 2013-07-01 +NWSA -APOL 2013-06-21 +ZTS
            -FHN 2013-06-06 +GM -HNZ 2013-05-23 +KSU -DF 2013-05-08 +MAC -CVH 2013-04-30 +REGN
            -PCS 2013-02-15 +PVH -BIG 2013-01-02 +ABBV -FII 2012-12-21 +APTV -TIE 2012-12-11
            +GRMN -RRD 2012-12-03 +DG -CBE 2012-10-10 +PETM -SUN 2012-10-02 +KRFT -ANR
            2012-10-01 +ADT -LXK +PNR -DV 2012-09-05 +LYB -SHLD 2012-07-31 +ESV -GR 2012-07-02
            +STX -PGN 2012-06-29 +MNST -SLE 2012-06-05 +LRCX -NVLS 2012-05-21 +ALXN -MMI
            2012-05-17 +KMI -EP 2012-04-23 +PSX -SVU 2012-04-03 +FOSL -MHS 2012-03-13 +CCI
            -CEG.2012 2011-12-31 +WPX -CPWR 2011-12-20 +TRIP -TLAB 2011-12-16 +BWA -AKS +PRGO
            -MWW +DLTR -WFR 2011-12-12 +GAS -GAS.2011 2011-11-18 +CBE -JNS 2011-10-31 +XYL -ITT
            2011-10-14 +TEL -CEPH 2011-09-23 +MOS -NSM 2011-07-05 +ACN -MI 2011-06-30 +MPC -RSH
            2011-06-01 +ANR -MEE 2011-04-27 +CMG -NOVL 2011-04-01 +BLK -GENZ 2011-03-31 +EW
            -Q.2011 2011-02-28 +COV -MFE 2011-02-25 +JOY -AYE 2011-01-03 +MMI -MDP 2010-12-17
            +CVC -KG +FFIV -EK +NFLX -ODP +NFX -NYT 2010-11-17 +TT -PTV 2010-08-26 +TYC -SII
            2010-07-14 +ACE -MIL 2010-06-30 +QEP -STR 2010-06-28 +KMX -XTO 2010-04-29 +CERN -BJS
            2010-03-15 +OKE -BDK 2010-02-26 +HP -RX 2010-02-16 +BRK-B -BNI 2010-01-29 +NRG -JAVA
            """
        ),
    ),
    "NASDAQ100": Record(
        universe.NASDAQ100,
        changes(
            """
            2026-10-09 +MRNA -WBD 2026-09-14 -KHC 2026-08-04 -EA 2026-07-07 +SPCX 2026-06-29
            +HONA 2026-06-22 +ALAB -CHTR +CRWV -CTSH +NBIS -INSM +RKLB -VRSK +TER -ZS 2026-05-18
            +LITE -CSGP 2026-04-20 +SNDK -TEAM 2026-01-20 +WMT -AZN 2026-01-09 -VSNT 2026-01-05
            +VSNT 2025-12-22 +ALNY -BIIB +FER -CDW +INSM -GFS +MPWR -LULU +STX -ON +WDC -TTD
            2025-11-06 -SOLS 2025-10-30 +SOLS 2025-07-28 +TRI 2025-07-17 -ANSS 2025-05-19 +SHOP
            -MDB 2024-12-23 +PLTR -ILMN +MSTR -MRNA +AXON -SMCI 2024-11-18 +APP -DLTR 2024-07-22
            +SMCI -WBA 2024-06-24 +ARM -SIRI 2024-03-18 +LIN -SPLK 2023-12-18 +CDW -ALGN +CCEP
            -EBAY +DASH -ENPH +MDB -JD +ROP -LCID +SPLK -ZM 2023-12-14 +TTWO -SGEN 2023-07-17
            +TTD -ATVI 2023-06-20 +ON -RIVN 2023-06-07 +GEHC -FI 2022-12-19 +CSGP -VRSN +RIVN
            -SWKS -NTES +WBD -SPLK +GFS -BIDU +BKR -MTCH +FANG -DOCU 2022-11-21 +ENPH -OKTA
            2022-02-22 +AZN -XLNX 2022-02-02 +CEG 2022-01-24 +ODFL -PTON 2021-12-20 +ABNB -CDW
            +FTNT -FOXA -FOX +PANW -CERN +LCID -CHKP +ZS -TCOM +DDOG -INCY 2021-08-26 +CRWD
            -MXIM 2021-07-21 +HON -ALXN 2020-12-21 +AEP -BMRN +MRVL -CTXS +MTCH -EXPE +OKTA
            -LBTYA -LBTYK +PTON -TTWO +TEAM -ULTA 2020-10-19 +KDP -WDC 2020-08-24 +PDD -NTAP
            2020-07-20 +MRNA -CSGP 2020-06-22 +DOCU -UAL 2020-04-30 +ZM -WTW 2020-04-20 +DXCM
            -AAL 2019-12-23 +ANSS -HAS +CDW -HSIC +CPRT -JBHT +CSGP -MYL +SGEN -NLOK +SPLK -WYNN
            2019-11-21 +EXC -CELG 2018-12-24 +AMD -ESRX +LULU -HOLX +NTAP -QRTEA +UAL -SHPG
            +VRSN -STX +WTW -VOD 2018-11-19 +XEL -XRAY 2018-11-05 +NXPI -CA 2018-07-23 +PEP
            -DISH 2017-12-18 +ASML -AKAM +CDNS -DISCA -DISCK +SNPS -NCLH +TTWO -TSCO +WDAY -VIAB
            2017-10-23 +ALGN -MAT 2017-06-19 +MELI -YHOO 2017-04-24 +WYNN -TRIP 2017-03-20 +IDXX
            -SBAC 2017-02-07 +JBHT -NXPI 2016-12-19 +CTAS -BBBY +HAS -NTAP +HOLX -SRCL +KLAC
            -WFM 2016-10-19 +SHPG -LLTC 2016-07-18 +MCHP -ENDP 2016-06-20 +XRAY -LMCA -LMCK
            -BATRA -BATRK 2016-04-18 +BATRA +BATRK 2016-03-16 +NTES -SNDK.2016 2016-02-16 +CSX
            -KLAC 2015-12-21 +TCOM -CHRW +ENDP -EXPD +EXPE -GMCR +MXIM -GRMN +NCLH -SPLS +TMUS
            -VIP +ULTA -WYNN -LILA -LILAK 2015-11-11 +PYPL -BRCM 2015-10-07 +INCY -ALTR
            2015-08-03 +SWKS 2015-07-31 -SIAL 2015-07-29 +JD 2015-07-27 +BMRN 2015-07-24 -DTV
            -CTRX 2015-07-02 +KHC -KRFT +LILA +LILAK 2015-03-23 +WBA -EQIX 2014-12-22 +AAL -EXPE
            +EA -FFIV +LRCX -MXIM +CMCSA +FOX +LBTYK 2014-04-03 +GOOG 2013-12-23 +DISH -FOSL
            +ILMN -MCHP +NXPI -NUAN +TRIP -SHLD +TSCO -XRAY 2013-11-18 +MAR -GOLD 2013-10-29
            +VIP -DELL 2013-08-22 +GMCR -LIFE 2013-07-25 +CHTR -BMC 2013-07-15 +TSLA -ORCL
            2013-06-06 +NFLX -PRGO 2013-06-05 +LMCA -VMED 2013-03-18 +KRFT -STRZA 2013-01-15
            +STRZA -LMCA 2012-12-24 +ADI -APOL +CTRX -EA +DISCA -FLEX +EQIX -GMCR +LBTYA -LRCX
            +LMCA -MRVL +REGN -NFLX +SBAC -RIMM +VRSK -VRSN +WDC -WCRX 2012-12-12 +META -INFY
            2012-07-23 +MDLZ -TCOM 2012-05-30 +VIAB -TEVA 2012-04-23 +TXN -FSLR 2011-12-19 +AVGO
            -FLIR +FOSL -ILMN +MNST -NIHD +NUAN -QGEN +GOLD -URBN 2011-12-06 +PRGO -JOYG
            2011-07-15 +SIRI -CEPH 2011-05-27 +GMCR -MICC 2011-04-04 +ALXN -GENZ 2010-12-20
            +AKAM -CTAS +TCOM -DISH +DLTR -FWLT +FFIV -HOLX +MU -JBHT +NFLX -LOGI +WFM -PDCO
            """
        ),
    ),
}


def on(name: str, day: date) -> Members:
    """The members of the list `universe` calls name, as they stood on day."""
    if name in OWED:
        raise NotImplementedError(f"{name}: its past members are not recorded yet")
    record = RECORDS[name]
    if not FIRST <= day <= LAST:
        raise ValueError(f"{name} on {day}: no record before {FIRST} or after {LAST}")
    names = record.symbols(day)
    listed = tuple(line for line in record.today if line.symbol in names)
    return Members(day, listed, tuple(sorted(names - {line.symbol for line in listed})))
