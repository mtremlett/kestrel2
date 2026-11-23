"""The one price store: what enters it is clean, and a line it cannot clean is parked."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import replace
from datetime import date
from decimal import Decimal

import pytest

from desk import store, venues
from desk.lines import Line
from desk.store import Bar, Refused

US, UK = Line("AAA", "US", "USD", 1), Line("BBB", "LSE", "GBP", 1)
DAY = date(2025, 11, 17)  #: a Monday; the last session before it is Friday the 14th
LONG = date(2025, 6, 2)  #: more than sixty sessions before DAY on both venues


def _bars(line: Line, first: date = date(2025, 11, 3)) -> tuple[Bar, ...]:
    days = venues.sessions(line.venue, first, date(2025, 11, 14))
    return tuple(
        Bar(d, Decimal(50 + n % 3), Decimal(52 + n % 3), Decimal(49 + n % 3), Decimal(51), 900)
        for n, d in enumerate(days)
    )


Judged = tuple[tuple[Bar, ...], list[str], list[str]]  #: kept bars, faults listed, park reasons


def _run(
    bars: Sequence[Bar] | Refused, line: Line = US, rates: store.Rates = store.NO_RATES
) -> Judged:
    """What the one judgement keeps of a line's bars, every fault it lists, and its park reason."""
    kept, faults, park = store.judge(line, bars, DAY, rates)
    return tuple(kept), [f.what for f in faults], [park.reason] if park else []


def _parked(bars: Sequence[Bar], line: Line = US) -> list[str]:
    return _run(bars, line)[2]


def test_a_clean_line_is_kept_exactly_and_not_parked() -> None:
    for line, first in ((US, date(2025, 11, 3)), (UK, date(2025, 11, 3)), (US, LONG)):
        assert _run(_bars(line, first), line) == (_bars(line, first), [], [])


BAD_BARS: dict[str, Callable[[Bar], Bar]] = {
    "the high is below the low": lambda b: replace(b, high=b.low - 1),
    "the close is far above the range": lambda b: replace(b, close=b.high * Decimal("1.04")),
    "the open is far below the range": lambda b: replace(b, open=b.low * Decimal("0.96")),
    "a price is not positive": lambda b: replace(b, low=Decimal(0)),
    "the volume is negative": lambda b: replace(b, volume=-1),
    "the price is in the wrong unit": lambda b: _scaled(b, Decimal(100)),
    "a price is not a number": lambda b: replace(b, high=Decimal("NaN")),
    "a price is infinite": lambda b: replace(b, high=Decimal("Infinity")),
}


@pytest.mark.parametrize(
    "near",
    [
        lambda b: replace(b, close=b.high * Decimal("1.029")),
        lambda b: replace(b, open=b.low * Decimal("0.971")),
    ],
    ids=["a close just above the high", "an open just below the low"],
)
def test_an_auction_price_just_outside_the_range_stretches_it(near: Callable[[Bar], Bar]) -> None:
    """His ruling of 13 November: London records its auctions apart from the day's trading."""
    bars = list(_bars(US))
    bars[4] = near(bars[4])
    kept, listed, reasons = _run(tuple(bars))
    assert reasons == []
    noted = [f for f in listed if "stretched" in f]
    assert len(noted) == 1 and noted[0].startswith(f"{bars[4].day} ")
    stretched = kept[4]
    assert (stretched.open, stretched.close) == (bars[4].open, bars[4].close)
    assert (stretched.low, stretched.high) == (
        min(bars[4].low, bars[4].open),
        max(bars[4].high, bars[4].close),
    )


def _scaled(bar: Bar, by: Decimal) -> Bar:
    return replace(
        bar, open=bar.open * by, high=bar.high * by, low=bar.low * by, close=bar.close * by
    )


@pytest.mark.parametrize("at", [0, 4, -1], ids=["the first bar", "a middle bar", "the last bar"])
@pytest.mark.parametrize("fault", sorted(BAD_BARS))
def test_a_bad_bar_never_enters_and_its_line_is_parked(fault: str, at: int) -> None:
    bars = list(_bars(US))
    bars[at] = BAD_BARS[fault](bars[at])
    kept, listed, reasons = _run(tuple(bars))
    assert len(reasons) == 1 and str(bars[at].day) in reasons[0]
    assert kept == tuple(b for b in _bars(US) if b.day != bars[at].day)


@pytest.mark.parametrize("first", [date(2025, 11, 3), LONG], ids=["recent", "old"])
def test_a_step_in_the_price_parks_the_line_and_keeps_every_bar_until_recorded_real(
    first: date,
) -> None:
    """A step parks however old it is, for it makes every bar before it wrong."""
    bars = (*_bars(US, first)[:5], *(_scaled(b, Decimal("0.5")) for b in _bars(US, first)[5:]))
    kept, listed, reasons = _run(bars)
    assert len(reasons) == 1 and str(bars[5].day) in reasons[0] and "split" in reasons[0]
    assert kept == bars
    line = replace(US, real_moves=frozenset({(bars[5].day, bars[5].close)}))
    assert _parked(bars, line) == []
    assert kept == bars


def test_two_bars_out_of_line_are_both_kept_for_no_one_can_tell_which_is_wrong() -> None:
    bars = (*_bars(US)[-2:-1], _scaled(_bars(US)[-1], Decimal(100)))
    kept, listed, reasons = _run(bars)
    assert len(reasons) == 1 and str(bars[1].day) in reasons[0] and "split" in reasons[0]
    assert kept == bars


@pytest.mark.parametrize("at", [5, -1], ids=["a middle bar", "the newest bar"])
def test_a_recorded_real_move_lets_through_only_its_own_close(at: int) -> None:
    bars = list(_bars(US))
    line = replace(US, real_moves=frozenset({(bars[at].day, bars[at].close / 2)}))
    bars[at] = _scaled(bars[at], Decimal(100))
    kept, listed, reasons = _run(tuple(bars), line)
    assert len(reasons) == 1 and str(bars[at].day) in reasons[0]
    assert bars[at] not in kept


def test_a_bar_on_a_day_not_yet_traded_parks_its_line_and_is_not_kept() -> None:
    unknown = replace(_bars(US)[0], day=date(2028, 1, 4))
    kept, _, reasons = _run((*_bars(US), unknown))
    assert len(reasons) == 1 and "2028-01-04" in reasons[0] and kept == _bars(US)


def test_a_refused_line_is_parked_with_its_reason_and_no_bars() -> None:
    why = "the archive refused it: HTTP Error 404"
    assert _run(Refused("HTTP Error 404")) == ((), [why], [why])


@pytest.mark.parametrize("differently", [False, True], ids=["the same", "differently"])
def test_one_date_given_twice_parks_its_line_and_keeps_it_once_or_not_at_all(
    differently: bool,
) -> None:
    bars = _bars(US)
    kept, listed, reasons = _run((*bars, replace(bars[2], close=bars[2].close + int(differently))))
    assert len(reasons) == 1 and "2025-11-05" in reasons[0]
    assert kept == tuple(b for b in bars if not (differently and b is bars[2]))


@pytest.mark.parametrize(
    ("line", "on"),
    [(US, date(2025, 11, 8)), (US, date(2025, 11, 27)), (UK, date(2025, 12, 26)), (US, DAY)],
    ids=["a Saturday", "a US holiday", "a UK holiday", "the day not yet traded"],
)
def test_a_bar_on_a_day_the_venue_was_shut_is_refused(line: Line, on: date) -> None:
    bars = _bars(line)
    kept, listed, reasons = _run((*bars, replace(bars[0], day=on)), line)
    assert len(reasons) == 1 and str(on) in reasons[0]
    assert kept == bars


def test_a_uk_holiday_is_no_gap_in_a_us_line() -> None:
    us, uk = _bars(US, date(2025, 8, 20)), _bars(UK, date(2025, 8, 20))
    assert date(2025, 8, 25) in [b.day for b in us]
    assert date(2025, 8, 25) not in [b.day for b in uk]
    assert _run(us)[2] == [] and _run(uk, UK)[2] == []


@pytest.mark.parametrize(
    ("kept", "named"),
    [
        (_bars(US)[:-1], "2025-11-14"),
        ((), "every session"),
    ],
    ids=["stale: the last session missing", "no bars at all"],
)
def test_a_line_missing_a_session_is_parked(kept: tuple[Bar, ...], named: str) -> None:
    kept, listed, reasons = _run(kept)
    assert len(reasons) == 1 and "missing" in reasons[0] and named in reasons[0]


HOLE = (*_bars(US)[:3], *_bars(US)[4:])  #: Thursday 6 November left out


def test_only_a_session_the_line_is_recorded_as_suspended_may_be_missing() -> None:
    (reason,) = _parked(HOLE)
    assert "2025-11-06" in reason and "suspension" in reason
    suspended = replace(US, suspended=frozenset({date(2025, 11, 6)}))
    assert _run(HOLE, suspended) == (HOLE, [], [])
    (reason,) = _parked(_bars(US), suspended)
    assert "2025-11-06" in reason and "suspended" in reason


@pytest.mark.parametrize(
    ("spoil", "named"),
    [
        (lambda b: (*b[:5], _scaled(b[5], Decimal(100)), *b[6:]), "2025-06-09"),
        (lambda b: (*b[:5], *b[6:]), "2025-06-09"),
        (lambda b: (*b, replace(b[0], day=date(2025, 6, 19))), "2025-06-19"),
    ],
    ids=["a bar in the wrong unit", "a session missing", "a bar on a US holiday"],
)
def test_an_old_bad_day_is_dropped_and_listed_but_does_not_park(
    spoil: Callable[[tuple[Bar, ...]], tuple[Bar, ...]], named: str
) -> None:
    """His ruling of 13 November: only the last sixty sessions can hold a line back."""
    bars = _bars(US, LONG)
    kept, listed, reasons = _run(spoil(bars))
    assert reasons == []
    assert date.fromisoformat(named) not in [b.day for b in kept]
    listed = listed
    assert listed and all(named in fault for fault in listed)


@pytest.mark.parametrize("unit", ["100", "0.01"], ids=["pence", "pounds"])
@pytest.mark.parametrize("days", [2, 5], ids=["two days", "five days"])
@pytest.mark.parametrize(("at", "parks"), [(5, False), (-8, True)], ids=["old", "recent"])
def test_a_run_of_days_in_the_wrong_unit_is_bad_days_not_a_step(
    unit: str, days: int, at: int, parks: bool
) -> None:
    clean = _bars(US, LONG)
    run = range(at % len(clean), at % len(clean) + days)
    bars = tuple(_scaled(b, Decimal(unit)) if n in run else b for n, b in enumerate(clean))
    kept, listed, reasons = _run(bars)
    assert bool(reasons) is parks and not any("split" in r for r in reasons)
    assert kept == tuple(b for n, b in enumerate(clean) if n not in run)


@pytest.mark.parametrize(("back", "parks"), [(60, True), (61, False)])
def test_the_sixtieth_session_back_is_the_oldest_that_parks(back: int, parks: bool) -> None:
    bars = list(_bars(US, LONG))
    bars[-back] = _scaled(bars[-back], Decimal(100))
    assert bool(_parked(tuple(bars))) is parks


@pytest.mark.parametrize("days", [1, 5], ids=["one day", "a week"])
@pytest.mark.parametrize("at", [0, 5, -8, -1], ids=["first", "old", "recent", "newest"])
def test_a_real_crash_is_kept_and_parks_until_recorded(at: int, days: int) -> None:
    """5QQQ's low on 7 April 2025 sat 40% under the close before, and it recovered the next day:
    only a hundredfold bar is a wrong unit. Any other move parks, however old, until recorded."""
    clean, start = _bars(US, LONG), at % len(_bars(US, LONG))
    bars = tuple(
        _scaled(b, Decimal("0.6")) if 0 <= n - start < days else b for n, b in enumerate(clean)
    )
    kept, listed, reasons = _run(bars)
    assert len(reasons) == 1 and "wrong unit" not in reasons[0]
    assert kept == bars
    moved = [bars[n] for n in (start, start + days) if 0 < n < len(bars)]
    assert all(f"{b.day} moved" in reasons[0] for b in moved)
    assert store.moves(US, bars) == tuple(b.day for b in moved)
    line = replace(US, real_moves=frozenset((b.day, b.close) for b in moved))
    assert _run(bars, line)[::2] == (bars, []) and store.moves(line, bars) == ()


def test_a_crash_after_days_in_the_wrong_unit_is_kept() -> None:
    """Only the days a hundredfold out are dropped; the real crash after them stays."""
    by = {5: Decimal(100), 6: Decimal(100), 7: Decimal("0.4"), 8: Decimal("0.4")}
    bars = tuple(_scaled(b, by.get(n, Decimal(1))) for n, b in enumerate(_bars(US, LONG)))
    kept, _, reasons = _run(bars)
    assert "split" in reasons[0] and bars[7:9] == kept[5:7]


@pytest.mark.parametrize("volume", [0, 900], ids=["no volume", "traded"])
def test_a_bar_with_no_volume_out_of_line_with_the_bar_before_is_dropped(volume: int) -> None:
    """2MU, 24 October 2025: a flat bar of no trade, 54% above the day before."""
    bars = list(_bars(US, LONG))
    bars[-8] = replace(_scaled(bars[-8], Decimal("1.7")), volume=volume)
    kept, _, reasons = _run(tuple(bars))
    assert ("moved" in reasons[0]) is bool(volume) and (bars[-8] in kept) is bool(volume)


FREEZES: dict[str, Callable[[Bar, Bar], Bar]] = {
    "the bar before repeated": lambda bar, b: replace(b, day=bar.day, volume=0),
    "the bar before repeated whole": lambda bar, b: replace(b, day=bar.day),
    "flat at the close before": lambda bar, b: Bar(bar.day, b.close, b.close, b.close, b.close, 0),
    "flat, but traded": lambda bar, b: Bar(bar.day, b.close, b.close, b.close, b.close, 900),
}


@pytest.mark.parametrize("freeze", FREEZES.values(), ids=FREEZES.keys())
@pytest.mark.parametrize("days", [4, 5], ids=["four days", "a week"])
@pytest.mark.parametrize(
    ("at", "recent"), [(5, False), (-63, True), (-5, True)], ids=["old", "into sixty", "to today"]
)
def test_a_week_of_one_price_and_no_volume_is_a_frozen_feed(
    freeze: Callable[[Bar, Bar], Bar], days: int, at: int, recent: bool
) -> None:
    bars = [replace(b, volume=900 + n) for n, b in enumerate(_bars(US, LONG))]
    run = range(at % len(bars), at % len(bars) + days)
    for n in run:
        bars[n] = freeze(bars[n], bars[n - 1])
    frozen = days >= 5 and freeze is not FREEZES["flat, but traded"]
    kept, listed, reasons = _run(tuple(bars))
    assert bool(reasons) is (frozen and recent)
    assert any("frozen feed" in f for f in listed) is frozen
    assert kept == tuple(b for n, b in enumerate(bars) if not (frozen and n in run))


POUND = Decimal("1.5")


def _prepared(bars: tuple[Bar, ...], line: Line, rated: bool = True) -> list[str]:
    return _priced(bars, line, rated)[2]


def _priced(bars: tuple[Bar, ...], line: Line, rated: bool = True) -> Judged:
    return _run(bars, line, {b.day: POUND for b in bars} if rated else {})


@pytest.mark.parametrize("run", [0, 1, 25], ids=["a step", "a fall that recovers", "a month of it"])
def test_a_step_as_large_as_the_pound_is_a_currency_only_if_it_lasts(run: int) -> None:
    """IITU x0.662, VUAG x0.791: a lasting step as large as the pound in dollars is a change of
    currency; 18 March 2020, a fall of 19% that recovers, is the market's move and is kept."""
    clean = _bars(US, LONG)
    mixed = [_scaled(b, 1 / POUND) for b in (clean[30 : 30 + run] if run else clean[30:])]
    bars = (*clean[:30], *mixed, *clean[30 + run :]) if run else (*clean[:30], *mixed)
    assert _prepared(bars, US, rated=False) == []  # unseen without the rate
    kept, _, reasons = _priced(bars, US)
    assert bool(reasons) is not run
    assert kept == bars  # nothing dropped: no wrong unit is claimed
    assert _prepared(bars, replace(US, leverage=3)) == []  # a real crash is as large


def test_a_dated_change_of_quote_currency_is_kept_not_refused() -> None:
    """HVPE, NBPE, VOF: the line master dates the change (R-RUNGS-20); the step day is kept."""
    clean = _bars(US, LONG)
    bars = (*clean[:30], *(_scaled(b, 1 / POUND) for b in clean[30:]))
    assert _prepared(bars, US)
    kept, _, reasons = _priced(bars, replace(US, requoted=frozenset({bars[30].day})))
    assert reasons == [] and kept == bars


def test_untraded_bars_in_another_unit_give_way_to_the_traded_bars() -> None:
    """SGLN, April to October 2011: flat bars of no volume at the pound's price in dollars, then
    the traded pound bars; no trade states no price, so the traded ones stand (R-RUNNER-274)."""
    clean = _bars(US, LONG)
    filler = tuple(
        _scaled(Bar(b.day, b.close, b.close, b.close, b.close, 0), POUND) for b in clean[:10]
    )
    kept, listed, reasons = _priced((*filler, *clean[10:]), US)
    assert reasons == [] and kept == clean[10:]
    assert sum("no volume" in f for f in listed) == 10


def test_a_leveraged_crash_as_large_as_the_pound_is_kept_not_taken_for_dollars() -> None:
    """2MU, 4 April 2025: a day's high 1.5 times the next close, and the close the pound's step."""
    clean = _bars(US, LONG)
    bars = (
        *clean[:29],
        replace(clean[29], high=Decimal(77)),
        *(_scaled(b, 1 / POUND) for b in clean[30:]),
    )
    kept, _, reasons = _priced(bars, replace(US, leverage=2))
    assert "moved" in reasons[0] and kept == bars


def test_a_recorded_split_adjusts_the_older_bars_only_by_the_ratio_the_jump_shows() -> None:
    """5QQQ x489 on 22 August 2024: adjusted only when recorded, never by a guessed ratio."""
    clean = _bars(US, LONG)
    day, ratio = clean[30].day, Decimal(500)
    old = tuple(_scaled(b, 1 / ratio) for b in clean[:30])
    bars = (*old, *clean[30:])
    assert "moved" in _parked(bars)[0]  # unrecorded: parked, bars untouched
    line = replace(US, splits=frozenset({(day, ratio)}))
    kept, _, reasons = _run(bars, line)
    assert reasons == []
    assert kept == (
        *(replace(b, volume=2) for b in clean[:30]),
        *clean[30:],
    )
    assert (
        "recorded as a split of 7"
        in _parked(bars, replace(US, splits=frozenset({(day, Decimal(7))})))[0]
    )
    assert _run(clean, line) == (clean, [], [])  # the archive adjusted it already


def test_bars_before_the_day_a_line_starts_are_dropped_with_a_fault_each() -> None:
    """5QQQ's archive quotes its first years in pounds, a hundredth of Stooq's pence: not kept."""
    clean = _bars(US, LONG)
    old = tuple(_scaled(b, Decimal(100)) for b in clean[:30])
    line = replace(US, starts=clean[30].day)
    kept, listed, reasons = _run((*old, *clean[30:]), line)
    assert reasons == [] and kept == clean[30:]
    assert len(listed) == 30  # each old bar, with why


def test_the_csv_store_is_gone_and_judge_is_the_one_door() -> None:
    gone = ("prepare", "read", "shelve", "faults", "_bar", "_FAULT", "_write", "HISTORY")
    assert not [name for name in gone if hasattr(store, name)]
