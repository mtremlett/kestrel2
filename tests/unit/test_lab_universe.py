"""The research list: four published lists' members, kept apart from the twenty trading
lines, and their bars kept through the one store's checks."""

from __future__ import annotations

import re
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from desk import store, venues
from desk.lines import LINES, Line
from desk.store import Bar
from lab import universe

DAY = date(2026, 11, 13)


def _ask(line: Line, day: date) -> tuple[Bar, ...]:
    """A clean history, priced by its venue so that two venues' bars can be told apart."""
    base = Decimal(100 if line.venue == "US" else 200)
    days = venues.sessions(line.venue, day - timedelta(120), day - timedelta(1))
    return tuple(
        Bar(d, base + n % 7, base + n % 7 + 1, base + n % 7 - 1, base + n % 7, 1000 + n)
        for n, d in enumerate(days)
    )


def test_the_research_list_is_the_four_lists_of_the_ruling_each_on_its_own_venue() -> None:
    parts = (universe.SP500, universe.NASDAQ100, universe.FTSE350, universe.ETFS)
    assert (
        [len(part) for part in parts] == [len(set(part)) for part in parts] == [503, 101, 347, 200]
    )
    american = universe.SP500 + universe.NASDAQ100 + universe.ETFS
    assert {(line.venue, line.currency) for line in american} == {("US", "USD")}
    assert {line.venue for line in universe.FTSE350} == {"LSE"}
    dollars = {line.symbol for line in universe.FTSE350 if line.currency == "USD"}
    assert dollars == {"BPCR", "CPG", "IHG", "MNTN", "RTW"}
    named = [(line.symbol, line.venue) for line in universe.UNIVERSE]
    assert len(named) == len(set(named)) == len(set(american + universe.FTSE350)) == 1065
    assert all(re.fullmatch("[A-Z0-9]+(-[A-Z])?", symbol) for symbol, _ in named)


def test_a_ticker_that_is_also_a_trading_line_is_the_masters_own_line() -> None:
    master = {(line.symbol, line.venue): line for line in LINES}
    shared = [line for line in universe.UNIVERSE if (line.symbol, line.venue) in master]
    assert {"AAPL", "SPY", "MSTR"} <= {line.symbol for line in shared}
    assert all(line is master[line.symbol, line.venue] for line in shared)
    assert universe._lines("LSE", "GBP", "AAPL")[0] is not master["AAPL", "US"]
    for currency, entry in (("USD", "QQQ:3"), ("GBP", "QQQ")):
        with pytest.raises(ValueError, match="QQQ: the research list and the instrument master"):
            universe._lines("US", currency, entry)


def test_only_a_fund_built_to_multiply_its_market_is_leveraged_and_says_by_how_much() -> None:
    leveraged = {line: line.leverage for line in universe.UNIVERSE if line.leverage != 1}
    assert set(leveraged) <= set(universe.ETFS)
    assert {line.symbol: times for line, times in leveraged.items()} == {
        **dict.fromkeys(("TQQQ", "SOXL", "UPRO", "SPXL", "TNA", "TECL", "TMF", "UDOW"), 3),
        **dict.fromkeys(("SSO", "QLD"), 2),
    }
    with pytest.raises(ValueError, match="invalid literal"):
        universe._lines("US", "USD", "SOXL:")


def test_one_symbol_is_two_companies_so_each_venue_keeps_its_own_folder(tmp_path: Path) -> None:
    both = [line for line in universe.UNIVERSE if line.symbol == "BA"]
    assert {line.venue for line in both} == {"US", "LSE"}
    assert universe.keep(tmp_path, DAY, both, _ask) == {}
    assert store.read(tmp_path / "US", "BA")[-1].close < 150
    assert store.read(tmp_path / "LSE", "BA")[-1].close > 150


def test_a_refused_ticker_is_parked_by_line_and_keeps_no_bars_and_the_rest_are_kept(
    tmp_path: Path,
) -> None:
    def refuse_london(line: Line, day: date) -> tuple[Bar, ...]:
        if line.venue == "LSE":
            raise TimeoutError("the archive did not answer")
        return _ask(line, day)

    both = [line for line in universe.UNIVERSE if line.symbol in ("BA", "COST")]
    london = [line for line in both if line.venue == "LSE"]
    assert len(both) == 4
    assert universe.keep(tmp_path, DAY, both, _ask) == {}
    parked = universe.keep(tmp_path, DAY, both, refuse_london)
    assert list(parked) == london
    assert all(
        p.reason.endswith("TimeoutError: the archive did not answer") for p in parked.values()
    )
    assert all(p.day == DAY for p in parked.values())
    assert [store.read(tmp_path / "LSE", line.symbol) for line in london] == [(), ()]
    assert all(len(store.read(tmp_path / "US", symbol)) > 60 for symbol in ("BA", "COST"))
