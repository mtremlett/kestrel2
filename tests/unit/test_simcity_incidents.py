"""simcity_incidents: the night of 16 November (a held line with no bar for a session) lived as
a scenario of its own: green when the desk refuses the day naming the line, red without that."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from test_simcity import NOW, RATES, ROOM, SHORT

from desk import (
    bars,
    book,
    conformance_parts,
    day,
    day_money,
    gateway,
    keeper,
    keeper_live,
    paper,
    simcity,
    simcity_incidents,
    simcity_parts,
    store,
    venues,
    watch,
)
from desk.lines import YARDSTICK
from desk.simcity_incidents import (
    CANCELLED,
    DEAF,
    DROPPED,
    HALTED,
    HOLE,
    LEFT,
    LIVE,
    LOCKED,
    NAMED,
    OUTSIDE,
    PARKED,
    PROMISE,
    REFUSED,
    SHUT,
    SILENT,
    SLOW,
    SOLD,
    STALE,
    STOP_SILENT,
    UNBARRED,
    UNHELD,
    beside,
    cancelled,
    deaf,
    dropped,
    gateway_silent,
    halted,
    hole,
    locked,
    minutes,
    outside,
    parked,
    silent,
    slow,
    stale,
    unbarred,
    unheld,
)
from desk.store import Bar


def night(patch: pytest.MonkeyPatch, root: Path) -> simcity.Night:
    patch.setattr(simcity, "EVENTS", ((HOLE, hole),))
    patch.setattr(simcity, "EVENTFUL", 1)
    return simcity.run(root, SHORT, ROOM, RATES, NOW, (1, 2, 3))


def test_a_held_line_with_no_bar_refuses_the_day_by_name_and_the_census_counts_it(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    result = night(monkeypatch, tmp_path)
    assert not any(PROMISE in broken for broken in result.broken)
    assert HOLE in result.census["day.run"]


def test_without_the_refusal_the_scenario_is_red(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(day_money, "close", lambda a, line, _upto: a[line][-1].close)
    assert any(PROMISE in broken for broken in night(monkeypatch, tmp_path).broken)


def test_a_holed_line_sold_before_the_close_keeps_the_promise_and_without_the_sale_is_red(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(day_money, "close", lambda a, line, _upto: a[line][-1].close)
    sold = SimpleNamespace(positions=lambda _desk: {})  #: the held line left the book that day
    monkeypatch.setattr(simcity_incidents, "book", sold)
    assert not any(PROMISE in broken for broken in night(monkeypatch, tmp_path / "sold").broken)
    monkeypatch.undo()
    monkeypatch.setattr(day_money, "close", lambda a, line, _upto: a[line][-1].close)
    assert any(PROMISE in broken for broken in night(monkeypatch, tmp_path / "held").broken)


def test_shares_beside_the_book_under_a_stop_are_sold_with_it_and_the_census_counts_it(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(simcity, "EVENTS", ((LEFT, beside),))
    monkeypatch.setattr(simcity, "EVENTFUL", 1)
    result = simcity.run(tmp_path, SHORT, ROOM, RATES, NOW, (1, 2, 3))
    assert not any(SOLD in broken for broken in result.broken)
    assert LEFT in result.census["day.run"]


def test_without_taking_the_shares_in_the_scenario_is_red(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(book, "adopt", lambda *_a: None)  #: no sale of shares the book lacks
    monkeypatch.setattr(simcity, "EVENTS", ((LEFT, beside),))
    monkeypatch.setattr(simcity, "EVENTFUL", 1)
    result = simcity.run(tmp_path, SHORT, ROOM, RATES, NOW, (1, 2, 3))
    assert any(SOLD in broken for broken in result.broken)


def cancelled_night(patch: pytest.MonkeyPatch, root: Path) -> simcity.Night:
    patch.setattr(simcity, "EVENTS", ((CANCELLED, cancelled),))
    patch.setattr(simcity, "EVENTFUL", 1)
    return simcity.run(root, SHORT, ROOM, RATES, NOW, (1, 2, 3))


def test_orders_the_broker_cancels_unfilled_are_named_and_the_census_counts_it(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    result = cancelled_night(monkeypatch, tmp_path)
    assert not any(NAMED in broken for broken in result.broken)
    assert CANCELLED in result.census["day.run"]


def test_without_naming_the_cancelled_orders_the_scenario_is_red(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(day, "_answer", lambda _root, _day, sent: sent)  #: no list is written
    assert any(NAMED in broken for broken in cancelled_night(monkeypatch, tmp_path).broken)


@pytest.mark.parametrize(
    ("words", "scenario"),
    [
        (HALTED, halted),
        (DROPPED, dropped),
        (OUTSIDE, outside),
        (PARKED, parked),
        (STALE, stale),
        (UNHELD, unheld),
        (UNBARRED, unbarred),
        (LOCKED, locked),
        (LIVE, minutes),
        (SILENT, silent),
        (SLOW, slow),
        (STOP_SILENT, gateway_silent),
    ],
)
def test_a_halt_a_line_outside_an_isa_and_a_parked_yardstick_are_lived_and_kept(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, words: str, scenario: Any
) -> None:
    monkeypatch.setattr(simcity, "EVENTS", ((words, scenario),))
    monkeypatch.setattr(simcity, "EVENTFUL", 1)
    result = simcity.run(tmp_path, SHORT, ROOM, RATES, NOW, (1, 2, 3))
    assert not any(words in broken for broken in result.broken)
    assert words in result.census["day.run"]


def test_without_refusing_a_gapped_yardstick_the_scenario_is_red(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(day_money, "close", lambda a, line, _upto: a[line][-1].close)
    monkeypatch.setattr(simcity, "EVENTS", ((PARKED, parked),))
    monkeypatch.setattr(simcity, "EVENTFUL", 1)
    result = simcity.run(tmp_path, SHORT, ROOM, RATES, NOW, (1, 2, 3))
    assert any(PARKED in broken for broken in result.broken)


def test_a_store_a_session_short_is_refused_and_without_the_refusal_is_red(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(simcity, "EVENTS", ((STALE, stale),))
    monkeypatch.setattr(simcity, "EVENTFUL", 1)
    assert not any(
        REFUSED in b for b in simcity.run(tmp_path, SHORT, ROOM, RATES, NOW, (1,)).broken
    )
    monkeypatch.setattr(keeper, "_short", lambda *_a: False)
    monkeypatch.setattr(bars, "daily", lambda _hot, _line: ())
    red = simcity.run(tmp_path / "red", SHORT, ROOM, RATES, NOW, (1,))
    assert any(REFUSED in b for b in red.broken)


def test_a_market_unheard_is_told_once_in_each_hour_and_without_the_telling_is_red(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(simcity, "EVENTS", ((DEAF, deaf),))
    monkeypatch.setattr(simcity, "EVENTFUL", 1)
    kept = simcity.run(tmp_path / "a", SHORT, ROOM, RATES, NOW, (1, 2, 3))
    assert not any(DEAF in broken for broken in kept.broken) and DEAF in kept.census["day.run"]
    monkeypatch.setattr(watch.Look, "blind", property(lambda _self: None))
    assert any(
        DEAF in b for b in simcity.run(tmp_path / "b", SHORT, ROOM, RATES, NOW, (1, 2, 3)).broken
    )


def test_lines_whose_minute_just_ended_are_not_stale_and_with_a_zero_grace_all_are(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(simcity, "EVENTS", ((LIVE, minutes),))
    monkeypatch.setattr(simcity, "EVENTFUL", 1)
    kept = simcity.run(tmp_path / "a", SHORT, ROOM, RATES, NOW, (1, 2, 3))
    assert not any(LIVE in broken for broken in kept.broken) and LIVE in kept.census["day.run"]
    monkeypatch.setattr(keeper_live, "LATE", timedelta(seconds=-1))
    red = simcity.run(tmp_path / "b", SHORT, ROOM, RATES, NOW, (1, 2, 3))
    assert any(LIVE in b for b in red.broken)


def test_unheld_minute_bars_are_named_stale_and_without_starting_the_lines_it_is_red(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(simcity, "EVENTS", ((UNHELD, unheld),))
    monkeypatch.setattr(simcity, "EVENTFUL", 1)
    kept = simcity.run(tmp_path / "a", SHORT, ROOM, RATES, NOW, (1, 2, 3))
    assert not any(UNHELD in broken for broken in kept.broken)
    monkeypatch.setattr(bars.Round, "timed", lambda *_a: 0)  #: no line is started, none kept
    red = simcity.run(tmp_path / "b", SHORT, ROOM, RATES, NOW, (1, 2, 3))
    assert any(UNHELD in broken for broken in red.broken)


def test_a_plan_with_no_bar_of_the_session_before_is_red_when_it_sizes_from_an_older_one(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(simcity, "EVENTS", ((UNBARRED, unbarred),))
    monkeypatch.setattr(simcity, "EVENTFUL", 1)
    monkeypatch.setattr(
        conformance_parts,
        "_last",
        lambda _x, day_, _h: store.Bar(day_, *(Decimal(1),) * 4, 1),
    )
    red = simcity.run(tmp_path, SHORT, ROOM, RATES, NOW, (1, 2, 3))
    assert any(UNBARRED in broken for broken in red.broken)


def test_without_the_refusal_by_name_a_locked_store_scenario_is_red(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(simcity, "EVENTS", ((LOCKED, locked),))
    monkeypatch.setattr(simcity, "EVENTFUL", 1)
    monkeypatch.setattr(bars, "NoRound", type("Quiet", (Exception,), {}))
    red = simcity.run(tmp_path, SHORT, ROOM, RATES, NOW, (1,))
    assert red.deaths or any(LOCKED in b for b in red.broken)


def test_without_the_kill_switch_a_silent_broker_scenario_is_red(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(simcity, "EVENTS", ((SILENT, silent),))
    monkeypatch.setattr(simcity, "EVENTFUL", 1)
    monkeypatch.setattr(book, "turn", lambda *_a: None)  #: the switch is never written
    red = simcity.run(tmp_path, SHORT, ROOM, RATES, NOW, (1, 2, 3))
    assert any(SILENT in b for b in red.broken)


def test_with_each_order_waiting_too_long_the_slow_broker_scenario_is_red(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(simcity, "EVENTS", ((SLOW, slow),))
    monkeypatch.setattr(simcity, "EVENTFUL", 1)
    monkeypatch.setattr(paper, "FILL_SECONDS", 3600)  #: the 19 November wait, made past the step
    red = simcity.run(tmp_path, SHORT, ROOM, RATES, NOW, (1, 2, 3))
    assert any(SLOW in b for b in red.broken)


def test_without_putting_the_account_back_a_silent_gateway_scenario_is_red(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(simcity, "EVENTS", ((STOP_SILENT, gateway_silent),))
    monkeypatch.setattr(simcity, "EVENTFUL", 1)
    monkeypatch.setattr(conformance_parts, "_leave", lambda _side, _run: "left")
    red = simcity.run(tmp_path, SHORT, ROOM, RATES, NOW, (1, 2, 3))
    assert red.deaths or any(STOP_SILENT in b for b in red.broken)


def test_a_closed_gateway_port_is_refused_by_name_and_without_the_refusal_is_red(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(simcity, "EVENTFUL", 10**9)  #: the closed port is lived beside the draw
    kept = simcity.run(tmp_path / "a", SHORT, ROOM, RATES, NOW, (1,))
    assert not any(SHUT in broken for broken in kept.broken) and SHUT in kept.census["day.run"]
    monkeypatch.setattr(gateway, "known", lambda *_a, **_k: gateway.Known(gateway.State.READY, ""))
    with pytest.raises(ConnectionRefusedError, match="4002"):  #: the run goes on to a dead door
        simcity.run(tmp_path, SHORT, ROOM, RATES, NOW, (1,))


def test_a_session_the_store_withdrew_is_no_end_of_the_world(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    gone = sorted({b.day for bs in SHORT.values() for b in bs})[20:40:2]
    archive = {x: [b for b in bs if x != YARDSTICK or b.day not in gone] for x, bs in SHORT.items()}
    monkeypatch.setattr(simcity, "EVENTFUL", 1_000_000)  # no scenario: the plain days alone
    result = simcity.run(tmp_path, archive, ROOM, RATES, NOW, (1, 2, 3))
    assert not [b for b in result.broken if "stops on" in b], result.broken


def test_a_session_the_store_withdrew_is_a_still_day_the_world_lives_past() -> None:
    sessions = venues.sessions(YARDSTICK.venue, date(2019, 5, 20), date(2019, 5, 28))
    bars_ = [Bar(d, *(Decimal(10 + i),) * 4, 5) for i, d in enumerate(sessions)]
    gone = bars_.pop(3)
    world = simcity_parts._restored(YARDSTICK, bars_)  # noqa: SLF001 - the world's own mending
    assert [b.day for b in world] == list(sessions)
    assert world[3] == Bar(gone.day, *(bars_[2].close,) * 4, 0)
    assert day_money.close({YARDSTICK: world}, YARDSTICK, sessions[-1]) == bars_[-1].close
