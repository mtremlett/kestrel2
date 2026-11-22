"""collector - THE FREE COLLECTOR: `python -m desk.collector`, run once a day (R-RUNNER-15). It
asks the free tiers the desk already holds a key for, a few dozen calls a day, and keeps
what they say before any use is made of it, because history a free tier does not keep cannot
be bought back (BIC-06, DAT-01). Four kinds of fact land in the one store (the long database
of desk.bars): a PRICE second opinion on each US line's last session (Massive, Tiingo; EODHD one
London line a day), MACRO series (FRED, BLS, BEA, EIA), EARNINGS dates (Finnhub) and NEWS with
the moment each was published (Finnhub, Marketaux, GNews). Every answer is also kept raw and
timestamped, under its source and subject.

A key is read from the environment as <NAME>_API_KEY and goes into an address and nowhere
else: nothing prints or stores an address. A source with no key is skipped, saying which; one
that fails is told by name and kind of fault, and the others carry on. The command ends 0 if
every source with a key was kept, 1 with the reason otherwise or if no source had a key.
NewsAPI and Trading 212 are never asked."""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from collections.abc import Callable, Iterator, Mapping
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from http.client import HTTPException
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from desk import bars
from desk.lines import LINES

Ask = Callable[[str], bytes]
PRICE, MACRO, EARNINGS, NEWS = "price", "macro", "earnings", "news"
SCHEMA = (
    "CREATE TABLE IF NOT EXISTS raw (source TEXT NOT NULL, subject TEXT NOT NULL,"
    " fetched TEXT NOT NULL, body BLOB NOT NULL)",
    "CREATE TABLE IF NOT EXISTS fact (kind TEXT NOT NULL, source TEXT NOT NULL,"
    " subject TEXT NOT NULL, at TEXT NOT NULL, value TEXT NOT NULL,"
    " PRIMARY KEY (kind, source, subject, at, value)) WITHOUT ROWID",
)
SERIES = ("DGS10", "DGS2", "T10Y2Y", "VIXCLS", "BAMLH0A0HYM2", "FEDFUNDS", "CPIAUCSL", "UNRATE")
BLS_SERIES = ("CUUR0000SA0", "LNS14000000", "CES0000000001")  #: CPI, unemployment, payrolls
AHEAD = timedelta(days=14)  #: how far ahead earnings dates are asked for
US = tuple(line.symbol for line in LINES if line.venue == "US")
LONDON = tuple(line.symbol for line in LINES if line.venue == "LSE")


@dataclass(frozen=True)
class Fact:
    """One thing a vendor said: its kind, what it is about, when (a day or a UTC moment) and
    the value, the headline's words for news."""

    kind: str
    subject: str
    at: str
    value: str


@dataclass(frozen=True)
class Source:
    """A vendor's service: its name, its key's name, the kind of fact it gives, the questions
    it is asked for a day (a subject and an address, given the key) and how an answer is read."""

    name: str
    key: str
    asks: Callable[[str, date], Iterator[tuple[str, str]]]
    read: Callable[[str, Any, date], Iterator[Fact]]


def _utc(moment: str | int) -> str:
    if isinstance(moment, int):
        return datetime.fromtimestamp(moment, UTC).isoformat()
    when = datetime.fromisoformat(moment)
    if when.tzinfo is None:
        raise ValueError(f"a moment in no time zone: {moment}")
    return when.astimezone(UTC).isoformat()


def _massive(key: str, day: date) -> Iterator[tuple[str, str]]:
    address = "https://api.massive.com/v2/aggs/grouped/locale/us/market/stocks/"
    yield "grouped", f"{address}{day}?adjusted=true&apiKey={key}"


def _massive_read(_: str, answer: Any, day: date) -> Iterator[Fact]:
    for row in answer.get("results", []):  # absent on a day the market was shut
        if row["T"] in US:
            yield Fact(PRICE, row["T"], str(day), str(row["c"]))


def _tiingo(key: str, day: date) -> Iterator[tuple[str, str]]:
    for symbol in US:
        address = f"https://api.tiingo.com/tiingo/daily/{symbol}/prices?startDate={day}"
        yield symbol, f"{address}&endDate={day}&token={key}"


def _tiingo_read(symbol: str, answer: Any, _: date) -> Iterator[Fact]:
    for row in answer:
        yield Fact(PRICE, symbol, row["date"][:10], str(row["close"]))


def _eodhd(key: str, day: date) -> Iterator[tuple[str, str]]:
    """The London audit sample: one line a day, the lines taking turns, so all are audited."""
    symbol = LONDON[day.toordinal() % len(LONDON)]
    address = f"https://eodhd.com/api/eod/{symbol}.LSE?fmt=json&from={day}&to={day}"
    yield symbol, f"{address}&api_token={key}"


def _eodhd_read(symbol: str, answer: Any, _: date) -> Iterator[Fact]:
    for row in answer:
        yield Fact(PRICE, symbol, row["date"], str(row["close"]))


def _alpha(key: str, day: date) -> Iterator[tuple[str, str]]:
    """A second London audit line a day, the turn after EODHD's, so each day two are audited."""
    symbol = LONDON[(day.toordinal() + 1) % len(LONDON)]
    address = "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&outputsize=compact"
    yield symbol, f"{address}&symbol={symbol}.LON&apikey={key}"


def _alpha_read(symbol: str, answer: Any, day: date) -> Iterator[Fact]:
    row = answer["Time Series (Daily)"].get(str(day))  # absent on a day the exchange was shut
    if row:
        yield Fact(PRICE, symbol, str(day), row["4. close"])


def _fred(key: str, _: date) -> Iterator[tuple[str, str]]:
    address = "https://api.stlouisfed.org/fred/series/observations?file_type=json&limit=5"
    for series in SERIES:
        yield series, f"{address}&sort_order=desc&series_id={series}&api_key={key}"


def _fred_read(series: str, answer: Any, _: date) -> Iterator[Fact]:
    for row in answer["observations"]:
        if row["value"] != ".":  # FRED's mark for a day with no figure
            yield Fact(MACRO, series, row["date"], row["value"])


def _bls(key: str, _: date) -> Iterator[tuple[str, str]]:
    for series in BLS_SERIES:
        address = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
        yield series, f"{address}{series}?registrationkey={key}"


def _bls_read(series: str, answer: Any, _: date) -> Iterator[Fact]:
    for row in answer["Results"]["series"][0]["data"]:
        if row["period"] != "M13":  # the year's average, not a month
            yield Fact(MACRO, series, f"{row['year']}-{row['period'][1:]}", row["value"])


def _eia(key: str, _: date) -> Iterator[tuple[str, str]]:
    address = "https://api.eia.gov/v2/petroleum/pri/spt/data/?frequency=daily&data[0]=value"
    sort = "sort[0][column]=period&sort[0][direction]=desc&length=5"
    yield "RWTC", f"{address}&facets[series][]=RWTC&{sort}&api_key={key}"


def _eia_read(series: str, answer: Any, _: date) -> Iterator[Fact]:
    for row in answer["response"]["data"]:
        yield Fact(MACRO, series, row["period"], str(row["value"]))


def _bea(key: str, day: date) -> Iterator[tuple[str, str]]:
    address = "https://apps.bea.gov/api/data/?method=GetData&datasetname=NIPA&TableName=T10101"
    years = f"{day.year - 1},{day.year}"
    yield "T10101", f"{address}&Frequency=Q&Year={years}&ResultFormat=JSON&UserID={key}"


def _bea_read(table: str, answer: Any, _: date) -> Iterator[Fact]:
    for row in answer["BEAAPI"]["Results"]["Data"]:
        if row["LineNumber"] == "1":  # real GDP, percent change on the quarter
            yield Fact(MACRO, f"{table}-GDP", row["TimePeriod"], row["DataValue"])


def _earnings(key: str, day: date) -> Iterator[tuple[str, str]]:
    address = "https://finnhub.io/api/v1/calendar/earnings"
    yield "calendar", f"{address}?from={day}&to={day + AHEAD}&token={key}"


def _earnings_read(_: str, answer: Any, _day: date) -> Iterator[Fact]:
    for row in answer["earningsCalendar"]:
        if row["symbol"] in US:
            yield Fact(EARNINGS, row["symbol"], row["date"], row.get("hour") or "")


def _finnhub_news(key: str, _: date) -> Iterator[tuple[str, str]]:
    yield "general", f"https://finnhub.io/api/v1/news?category=general&token={key}"


def _finnhub_news_read(_: str, answer: Any, _day: date) -> Iterator[Fact]:
    for row in answer:
        yield Fact(NEWS, "finnhub", _utc(row["datetime"]), row["headline"])


def _marketaux(key: str, _: date) -> Iterator[tuple[str, str]]:
    yield "all", f"https://api.marketaux.com/v1/news/all?language=en&api_token={key}"


def _marketaux_read(_: str, answer: Any, _day: date) -> Iterator[Fact]:
    for row in answer["data"]:
        yield Fact(NEWS, "marketaux", _utc(row["published_at"]), row["title"])


def _gnews(key: str, _: date) -> Iterator[tuple[str, str]]:
    address = "https://gnews.io/api/v4/top-headlines?category=business&lang=en"
    yield "business", f"{address}&apikey={key}"


def _gnews_read(_: str, answer: Any, _day: date) -> Iterator[Fact]:
    for row in answer["articles"]:
        yield Fact(NEWS, "gnews", _utc(row["publishedAt"]), row["title"])


SOURCES = (
    Source("massive", "MASSIVE", _massive, _massive_read),
    Source("tiingo", "TIINGO", _tiingo, _tiingo_read),
    Source("eodhd", "EODHD", _eodhd, _eodhd_read),
    Source("alphavantage", "ALPHAVANTAGE", _alpha, _alpha_read),
    Source("fred", "FRED", _fred, _fred_read),
    Source("bls", "BLS", _bls, _bls_read),
    Source("eia", "EIA", _eia, _eia_read),
    Source("bea", "BEA", _bea, _bea_read),
    Source("finnhub", "FINNHUB", _earnings, _earnings_read),
    Source("finnhub-news", "FINNHUB", _finnhub_news, _finnhub_news_read),
    Source("marketaux", "MARKETAUX", _marketaux, _marketaux_read),
    Source("gnews", "GNEWS", _gnews, _gnews_read),
)
NAMES = tuple(dict.fromkeys(source.key for source in SOURCES))


def _last_session(now: datetime) -> date:
    """The last weekday before today: the day a price is asked for. A holiday gives no bars."""
    day = now.date() - timedelta(days=1)
    while day.weekday() >= 5:
        day -= timedelta(days=1)
    return day


def _ask(address: str) -> bytes:
    with urlopen(Request(address), timeout=30) as answer:  # noqa: S310
        return bytes(answer.read())


def _keep(
    store: sqlite3.Connection, source: Source, day: date, key: str, ask: Ask, at: str
) -> None:
    answers = [(subject, ask(address)) for subject, address in source.asks(key, day)]
    with store:  # the network is done with: one short write, all of a source's answers or none
        for subject, body in answers:
            store.execute("INSERT INTO raw VALUES (?, ?, ?, ?)", (source.name, subject, at, body))
            answer = json.loads(body, parse_float=Decimal)
            for fact in source.read(subject, answer, day):
                store.execute(
                    "INSERT OR IGNORE INTO fact VALUES (?, ?, ?, ?, ?)",
                    (fact.kind, source.name, fact.subject, fact.at, fact.value),
                )


def run(root: Path, env: Mapping[str, str], now: datetime, ask: Ask = _ask) -> int:
    """One day's collection into the store under root. Returns the command's exit code."""
    day, at = _last_session(now), now.astimezone(UTC).isoformat()
    skipped: list[str] = []
    failed: list[str] = []
    kept = 0
    with closing(sqlite3.connect(root / bars.HISTORY, timeout=bars.WAIT)) as store:
        for table in SCHEMA:
            store.execute(table)
        for source in SOURCES:
            key = env.get(f"{source.key}_API_KEY")
            if not key:
                skipped.append(f"no {source.key}_API_KEY: {source.name} skipped")
                continue
            try:
                _keep(store, source, day, key, ask, at)
                kept += 1
            except HTTPError as refusal:  # its status only: the url holds the key
                failed.append(f"{source.name}: HTTP {refusal.code}")
            except (
                OSError,
                HTTPException,
                ValueError,
                KeyError,
                TypeError,
                sqlite3.Error,
            ) as fault:
                # the fault's words may hold the address, and so the key: only its kind is told
                failed.append(f"{source.name}: {type(fault).__name__}")
    sys.stderr.write("".join(f"{line}\n" for line in skipped + failed))
    return int(not kept)


if __name__ == "__main__":
    sys.exit(run(Path(os.environ["KESTREL2_DATA"]), os.environ, datetime.now(UTC)))
