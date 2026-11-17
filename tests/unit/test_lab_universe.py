"""The research list: four published lists' members, kept apart from the twenty trading
lines, and their bars kept through the one store's checks."""

from __future__ import annotations

import re
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from decimal import ROUND_CEILING, Decimal
from pathlib import Path
from statistics import median

import numpy as np
import pytest

from desk import store, venues
from desk.lines import LINES, NO_TAX, STAMP_DUTY, Line
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
    sizes = [len(part) for part in parts]
    assert sizes == [len(set(part)) for part in parts] == [503, 101, 347, 200]
    american = universe.SP500 + universe.NASDAQ100 + universe.ETFS
    assert {(line.venue, line.currency) for line in american} == {("US", "USD")}
    assert {line.venue for line in universe.FTSE350} == {"LSE"}
    #: a London share pays stamp duty on a purchase; no US ticker, share or fund, pays UK tax
    assert {line.uk_tax for line in universe.FTSE350} == {STAMP_DUTY}
    assert {line.uk_tax for line in american} == {NO_TAX}
    dollars = {line.symbol for line in universe.FTSE350 if line.currency == "USD"}
    assert dollars == {"BPCR", "CPG", "IHG", "MNTN", "RTW"}
    named = [(line.symbol, line.venue) for line in universe.UNIVERSE]
    assert len(named) == len(set(named)) == len(set(american + universe.FTSE350)) + 1 == 1066
    #: ISF, London's yardstick, is studied so that the store holds LSE/ISF.csv for the ladder
    assert [x.symbol for x in universe.YARDSTICKS] == ["ISF"]
    assert all(re.fullmatch("[A-Z0-9]+(-[A-Z])?", symbol) for symbol, _ in named)


def test_a_ticker_that_is_also_a_trading_line_is_the_masters_own_line() -> None:
    master = {(line.symbol, line.venue): line for line in LINES}
    shared = [line for line in universe.UNIVERSE if (line.symbol, line.venue) in master]
    assert {"AAPL", "MU", "MSTR"} <= {line.symbol for line in shared}
    #: GLD left the master for a London line: research's GLD is a ticker of its own again
    assert ("GLD", "US") not in master and "GLD" in {line.symbol for line in universe.ETFS}
    assert all(line is master[line.symbol, line.venue] for line in shared)
    assert universe._lines("LSE", "GBP", "AAPL")[0] is not master["AAPL", "US"]
    for currency, entry in (("USD", "AMD:3"), ("GBP", "AMD")):
        with pytest.raises(ValueError, match="AMD: the research list and the instrument master"):
            universe._lines("US", currency, entry)
    with pytest.raises(ValueError, match="ISF: the research list and the instrument master"):
        universe._lines("LSE", "GBP", "ISF", STAMP_DUTY)


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


def test_a_refresh_writes_londons_yardstick_where_the_ladder_reads_it(tmp_path: Path) -> None:
    assert universe.keep(tmp_path, DAY, universe.YARDSTICKS, _ask) == {}
    assert (tmp_path / "LSE" / "ISF.csv").is_file()


def test_a_yardstick_with_a_missing_day_is_named_and_filled_from_a_second_source(
    tmp_path: Path,
) -> None:
    yard = universe.YARDSTICKS
    whole = _ask(yard[0], DAY)
    lost = whole[40].day

    def holed(line: Line, day: date) -> tuple[Bar, ...]:
        return tuple(b for b in _ask(line, day) if b.day != lost)

    told = universe.refresh(tmp_path, DAY, yard, holed)
    assert told.endswith(f"1 parked; yardstick ISF has no bar on {lost}")
    #: the second source is the old desk's Stooq matrices: London, in pence, only that day wanted
    folder = tmp_path / "matrix"
    folder.mkdir()
    rows = np.array([[float(x) * 100 for x in (b.open, b.high, b.low, b.close, 0)] for b in whole])
    rows[:, 4] = [b.volume for b in whole]
    stamps = [
        int(datetime(b.day.year, b.day.month, b.day.day, tzinfo=UTC).timestamp() * 1000)
        for b in whole
    ]
    np.save(folder / "ISF.UK_1d_ohlcv.npy", rows.T)
    np.save(folder / "ISF.UK_1d_ts.npy", np.array(stamps))
    second = universe.matrix(folder)
    assert second(universe.UNIVERSE[0], DAY) == ()
    assert universe.refresh(tmp_path, DAY, yard, holed, second).endswith("0 parked")
    assert lost in {b.day for b in store.read(tmp_path / "LSE", "ISF")}
    #: shelved, so the next refresh with the archive still short keeps the filled day
    assert universe.refresh(tmp_path, DAY, yard, holed).endswith("0 parked")


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
    for p in parked.values():
        assert p.day == DAY and p.reason.endswith("TimeoutError: the archive did not answer")
    assert [store.read(tmp_path / "LSE", line.symbol) for line in london] == [(), ()]
    assert all(len(store.read(tmp_path / "US", symbol)) > 60 for symbol in ("BA", "COST"))


def test_a_refresh_gives_a_line_with_no_file_one_counts_it_and_adds_nothing_the_second_time(
    tmp_path: Path,
) -> None:
    line = universe.YARDSTICKS
    bars = len(_ask(line[0], DAY))
    first = universe.refresh(tmp_path, DAY, line, _ask)
    assert first == f"research refresh: 1 lines refreshed, {bars} bars added, 0 parked"
    assert universe.refresh(tmp_path, DAY, line, _ask).endswith(
        "1 lines refreshed, 0 bars added, 0 parked"
    )


def test_the_nightly_refresh_clears_out_a_ticker_that_left_and_writes_the_day_and_list(
    tmp_path: Path,
) -> None:
    home = tmp_path / "grid" / "store"
    (home / "US" / "history").mkdir(parents=True)
    for name in ("OLD.csv", "OLD.faults.csv", "history/OLD.csv"):
        (home / "US" / name).write_text("x", encoding="utf-8")
    said = universe.nightly(tmp_path, DAY, (universe.SP500[0],), _ask)
    assert said.endswith("; 3 cleared out")
    assert sorted(p.name for p in (home / "US").iterdir()) == [
        "MMM.csv",
        "MMM.faults.csv",
        "history",
    ]
    note = (home / "REFLECTS.txt").read_text(encoding="utf-8").splitlines()
    sizes = " ".join(f"{k}={len(v)}" for k, v in universe.LISTS.items())
    assert note[:2] == [f"day {DAY}", f"lines 1 {sizes}"]
    assert note[3] == "cleared US:OLD US:OLD US:OLD"


MMM = universe.SP500[0]
AT = 60


def _scaled(bar: Bar, by: Decimal | int) -> Bar:
    return replace(
        bar, open=bar.open * by, high=bar.high * by, low=bar.low * by, close=bar.close * by
    )


def _stepped(by: Decimal | int, at: int = AT, bars: tuple[Bar, ...] | None = None) -> list[Bar]:
    """A history whose every price from bar `at` on is `by` times what it was."""
    bars = _ask(MMM, DAY) if bars is None else bars
    return [bar if n < at else _scaled(bar, by) for n, bar in enumerate(bars)]


def _read(tmp_path: Path, bars: list[Bar], line: Line = MMM) -> universe.History:
    parked = universe.keep(tmp_path, DAY, [line], lambda *_: tuple(bars))
    read = universe.read(tmp_path, line)
    #: research's rule loosens nothing: the store parks the ticker for every move it finds
    assert list(parked) == ([line] if read.moves or read.rescaled else [])
    assert all(f"{day} moved" in parked[line].reason for day in read.moves + read.rescaled)
    return read


def _heavy(bars: list[Bar], at: int = AT) -> int:
    """The fewest shares that make bar `at` heavy trading: 2.5 times its usual value traded."""
    usual = median(bar.close * bar.volume for bar in bars[max(0, at - 20) : at])
    return int((Decimal("2.5") * usual / bars[at].close).to_integral_value(ROUND_CEILING))


def test_a_clean_ticker_is_read_whole_with_no_move(tmp_path: Path) -> None:
    bars = list(_ask(MMM, DAY))
    assert _read(tmp_path, bars) == universe.History(tuple(bars), (), ())


@pytest.mark.parametrize("at", [1, 30, AT], ids=["the second bar", "early", "late"])
def test_a_fall_wholly_overnight_on_ordinary_trading_is_a_change_of_scale(
    tmp_path: Path, at: int
) -> None:
    """A split the archive did not adjust, a demerger, a special payment: research reads the
    longer run of bars, before it or after. The same fall in heavy trading is the market's."""
    bars = _stepped(Decimal("0.5"), at)
    bars[: AT - 25] = [replace(bar, volume=bar.volume * 100) for bar in bars[: AT - 25]]
    heavy = _heavy(bars, at)
    bars[at] = replace(bars[at], volume=heavy - 1)
    longer = bars[:at] if at == AT else bars[at:]
    assert _read(tmp_path, bars) == universe.History(tuple(longer), (), (bars[at].day,))
    bars[at] = replace(bars[at], volume=heavy)
    assert _read(tmp_path, bars) == universe.History(tuple(bars), (bars[at].day,), ())


def test_a_rise_wholly_overnight_is_a_change_of_scale_however_heavy_the_trading(
    tmp_path: Path,
) -> None:
    """A windfall nobody has confirmed is not counted: a disbelieved gain costs no money."""
    bars = _stepped(2, 30)
    bars[30] = replace(bars[30], volume=bars[30].volume * 500)
    assert _read(tmp_path, bars) == universe.History(tuple(bars[30:]), (), (bars[30].day,))


def test_a_move_made_within_the_day_is_the_markets_and_is_read(tmp_path: Path) -> None:
    """Listed on the day it was made and on the next, whose bar sits far from where it began."""
    for by, bars in ((Decimal("0.5"), _stepped(Decimal("0.5"))), (2, _stepped(2))):
        last = _ask(MMM, DAY)[AT - 1].close
        if by != 1:
            bars[AT] = replace(
                bars[AT], open=last, high=max(last, bars[AT].high), low=min(last, bars[AT].low)
            )
        days = (bars[AT].day, bars[AT + 1].day)
        assert _read(tmp_path, bars) == universe.History(tuple(bars), days, ())
        #: the close falls with the low: the market's, so no low is repaired
        assert not any("low repaired" in f for f in store.faults(tmp_path / MMM.venue, MMM.symbol))
    spike = list(_ask(MMM, DAY))  #: a bad low long enough ago that the line is not parked for it
    spike[10] = replace(spike[10], low=spike[10].low / 2)
    mended = replace(spike[10], low=min(spike[10].open, spike[10].close))
    assert _read(tmp_path, spike) == universe.History((*spike[:10], mended, *spike[11:]), (), ())
    assert f"{mended.day} low repaired: was {spike[10].low}" in store.faults(
        tmp_path / MMM.venue, MMM.symbol
    )


def test_a_fall_with_no_volume_to_judge_it_by_is_read_as_the_markets(tmp_path: Path) -> None:
    bars = [replace(bar, volume=0) for bar in _stepped(Decimal("0.5"))]
    assert _read(tmp_path, bars) == universe.History(tuple(bars), (bars[AT].day,), ())
    bars = _stepped(Decimal("0.5"), 30)
    bars[30] = replace(bars[30], volume=0)  #: quoted on the new scale, and nothing traded at it
    assert _read(tmp_path, bars) == universe.History(tuple(bars[30:]), (), (bars[30].day,))


def test_research_reads_the_longest_run_on_one_scale_and_lists_the_moves_inside_it(
    tmp_path: Path,
) -> None:
    bars = _stepped(Decimal("0.5"), 30, tuple(_stepped(Decimal("0.5"), 10)))
    for at in (20, 70):  #: a bad low between the two changes of scale, and one after both
        bars[at] = replace(bars[at], low=bars[at].low / 2)
    cuts = (bars[10].day, bars[30].day)
    kept = tuple(bars[30:])
    mended = replace(bars[70], low=min(bars[70].open, bars[70].close))
    assert _read(tmp_path, bars) == universe.History((*kept[:40], mended, *kept[41:]), (), cuts)
    even = _stepped(Decimal("0.5"), 43)[1:]  #: two runs as long: the later is read
    assert len(even) == 84
    assert _read(tmp_path, even) == universe.History(tuple(even[42:]), (), (even[42].day,))


def test_a_move_the_line_records_as_real_is_no_longer_a_question(tmp_path: Path) -> None:
    bars = _stepped(Decimal("0.5"))
    line = replace(MMM, real_moves=frozenset({(bars[AT].day, bars[AT].close)}))
    assert _read(tmp_path, bars, line) == universe.History(tuple(bars), (), ())
