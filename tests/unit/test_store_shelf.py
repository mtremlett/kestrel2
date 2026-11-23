"""The store's shelf: older bars joined to the archive's, and what they replace."""

from __future__ import annotations

from dataclasses import replace
from datetime import date
from decimal import Decimal

import pytest
from test_store import DAY, LONG, UK, US, _bars, _run

from desk import store, venues
from desk.store import Bar


def test_shelved_older_bars_join_the_archives() -> None:
    every = _bars(UK, LONG)
    assert store.judge(UK, every[3:], DAY, shelf=every[:5])[::2] == (list(every), None)


@pytest.mark.parametrize("shelf", [(8, 20), (12, 15), (0, 5)], ids=["all", "part", "none of it"])
def test_a_frozen_run_the_archive_filled_is_replaced_by_shelved_bars_never_by_its_own_filler(
    shelf: tuple[int, int],
) -> None:
    """VUAG, 23 May to 18 June 2019: the archive repeats one price for 27 sessions."""
    every = [replace(b, volume=900 + n) for n, b in enumerate(_bars(UK, LONG))]
    c = every[9].close
    archive = (*every[:10], *[Bar(b.day, c, c, c, c, 0) for b in every[10:17]], *every[17:])
    assert _run(archive, UK)[0] == (*every[:10], *every[17:])  # dropped, as ever
    kept, faults, _ = store.judge(UK, archive, DAY, shelf=every[shelf[0] : shelf[1]])
    first, last = max(shelf[0], 10), min(shelf[1], 17)  # the old desk's own prices fill it
    assert kept == [*every[:10], *every[first:last], *every[17:]]
    assert bool(faults) is (shelf != (8, 20))


def test_a_session_the_archive_lacks_is_filled_and_one_both_hold_must_agree() -> None:
    """R-RUNNER-189: the archive first; a shelved bar fills a hole (2MU, 8 January 2021) and
    is no fault; two closes further apart than AGREE are a recorded fault, never settled."""
    every = list(_bars(UK, LONG))
    kept, faults, park = store.judge(UK, [*every[:30], *every[31:]], DAY, shelf=every)
    assert (kept, faults, park) == (every, [], None)
    far = replace(every[-10], close=every[-10].close * Decimal("1.05"), high=every[-10].high * 2)
    kept, _, park = store.judge(UK, (*every[:-10], far, *every[-9:]), DAY, shelf=every)
    assert park and f"{far.day} close" in park.reason and "(shelf)" in park.reason
    assert {b.day: b.close for b in kept}[far.day] == far.close


def test_the_brokers_bars_stand_first_over_the_archives_and_a_disagreement_is_a_fault() -> None:
    """R-RUNNER-189: broker, then archive; the broker fills a hole, names both where they differ."""
    every = list(_bars(UK, LONG))
    hole = [*every[:30], *every[31:]]
    kept, faults, park = store.judge(UK, hole, DAY, broker=every)
    assert (kept, faults, park) == (every, [], None)
    far = replace(every[-10], close=every[-10].close * Decimal("1.05"), high=every[-10].high * 2)
    kept, faults, _ = store.judge(UK, [*every[:-10], far, *every[-9:]], DAY, broker=every)
    assert kept == every and [
        f.what for f in faults if "(broker)" in f.what and "(archive)" in f.what
    ]
    assert store.judge(UK, store.Refused("no route"), DAY, broker=every)[0] == every


_PRICES = ("open", "high", "low", "close")


def test_a_shelf_a_hundredth_of_archive_and_broker_is_a_named_unit_fault_put_right_once() -> None:
    """R-RUNNER-272, IB1T: the head start shelved a dollar-quoted line at 1/100 (0.058445 for
    5.8445 on 2026-08-24). Not parked, no step: put right by the factor, each bar named."""
    every = list(_bars(UK, LONG))
    shelf = [replace(b, **{k: getattr(b, k) / 100 for k in _PRICES}) for b in every[:40]]
    for broker in (None, every[20:]):  # the archive alone, then the broker beside it
        kept, faults, park = store.judge(UK, every[20:], DAY, shelf=shelf, broker=broker)
        assert kept == every and park is None
        put = [f for f in faults if "unit fault" in f.what]
        assert len(put) == 40 and all(f.noted for f in put)
    assert store.judge(UK, every[20:], DAY, shelf=shelf[:23])[2] is not None  # too few sessions


def test_a_shelf_a_hundredth_on_the_clear_majority_is_put_right_and_the_odd_days_named() -> None:
    """R-RUNNER-307, IB1T: 250 of 255 shared days a hundredth, five of the archive's own bad
    days: put right, five named faults, not parked. Only half the days: not rescaled, parked."""
    every = list(_bars(UK, LONG))
    shelf = [replace(b, **{k: getattr(b, k) / 100 for k in _PRICES}) for b in every]
    odd = {every[-3].day, every[-30].day}
    archive = [
        replace(b, **{k: getattr(b, k) * Decimal("1.1") for k in _PRICES}) if b.day in odd else b
        for b in every
    ]
    kept, faults, park = store.judge(UK, archive, DAY, shelf=shelf)
    assert park is None and len(kept) == len(every)
    assert sum("(shelf)" in f.what for f in faults) == len(odd)
    half = [b if n % 2 else replace(b, close=b.close / 7) for n, b in enumerate(shelf)]
    assert store.judge(UK, every, DAY, shelf=half)[0] == every
    assert store.judge(UK, every, DAY, shelf=half)[2] is not None


def test_bars_from_before_2010_are_kept_for_the_calendar_knows_their_sessions() -> None:
    days = venues.sessions("US", date(2005, 6, 1), date(2005, 6, 30))
    old = tuple(replace(_bars(US)[n % 9], day=d) for n, d in enumerate(days))
    kept, faults, _ = store.judge(US, old, DAY)
    assert kept == list(old) and not [f for f in faults if f.day < days[-1]]
