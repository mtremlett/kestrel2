"""R-RUNNER-270: the keeper's command asks the broker first for a day the archive lacks."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from desk import archive, history, keeper, listing, paper, venues
from desk.lines import LINES, Line
from desk.store import Answer, Bar, Refused

UK = Line("BBB", "LSE", "GBP", 1)
TUE = date(2026, 11, 17)
MON = date(2026, 11, 16)
NOW = datetime(2026, 11, 16, 21, 45, tzinfo=UTC)  # both venues settled: Monday's close is owed


def _bars(line: Line, day: date) -> tuple[Bar, ...]:
    days = venues.sessions(line.venue, date(2026, 8, 3), day - timedelta(1))
    prices = [Decimal(100 + n % 5) for n in range(len(days))]
    return tuple(
        Bar(d, p, p + 1, p - 1, p, 1000 + n)
        for n, (d, p) in enumerate(zip(days, prices, strict=True))
    )


def _no_gateway(_talk: object) -> object:
    raise ConnectionRefusedError("no gateway in a test")


def _broker(lines: Sequence[Line], day: date) -> dict[Line, Answer]:
    return {line: _bars(line, day) for line in lines}


def test_a_day_the_archive_lacks_is_filled_from_the_broker_else_the_line_parks_named(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def away(address: str) -> bytes:
        raise OSError(f"no route to {address[:13]}")

    monkeypatch.setattr(archive, "_ask", away)
    monkeypatch.setattr(paper, "dial", _no_gateway)
    given, bare, one = tmp_path / "given", tmp_path / "bare", LINES[0]
    assert [keeper.main(given, NOW, [], _broker) for _ in range(3)][-1] == 0  # ROOM lines a call
    held, parked = keeper.saved(given, TUE, [one])
    assert held[one] == _bars(one, TUE) and not parked
    assert keeper.main(bare, NOW, [], history.daily(NOW)) == 1  # no broker answer: as before
    assert keeper.saved(bare, TUE, [one])[1] == {one.symbol}  # parked, and the line is named


def test_ibkr_is_asked_first_for_every_line_its_bar_stands_and_each_newest_bar_is_named(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    asked: list[list[Line]] = []

    def broker(lines: Sequence[Line], day: date) -> dict[Line, Answer]:
        asked.append(list(lines))
        return _broker(lines, day)

    def none(lines: Sequence[Line], _day: date) -> dict[Line, Answer]:
        return {line: () for line in lines}  # the broker answers, with no bar

    def no_friday(line: Line, day: date) -> tuple[Bar, ...]:  # 3LGO: a session missing mid-window
        return tuple(b for b in _bars(line, day) if b.day != date(2026, 11, 13))

    def apart(line: Line, day: date) -> tuple[Bar, ...]:  # 2MU: the archive's close is 3% off
        *rest, last = _bars(line, day)
        return (*rest, replace(last, close=last.close + 3, high=last.high + 3))

    cases: list[tuple[Callable[[Line, date], tuple[Bar, ...]], Callable[..., Any], bool, str]] = [
        (_bars, broker, False, "newest bar from IBKR: BBB"),
        (no_friday, broker, False, "newest bar from IBKR: BBB"),
        (apart, broker, False, "(archive), held"),
        (_bars, none, False, "archive (IBKR gave none): BBB"),
        (lambda ln, d: _bars(ln, d)[:-1], none, True, "0 of 1 lines clean"),
    ]
    for n, (got, ibkr, parked, said) in enumerate(cases):
        words = keeper.keep(
            tmp_path / str(n), NOW, (UK,), got, lambda *_: (), lambda: 0.0, series=(), broker=ibkr
        )[0]
        held, stuck = keeper.saved(tmp_path / str(n), TUE, [UK])
        assert bool(stuck) == parked and said in words[0], (n, words)
        assert parked or held[UK][-1] == _bars(UK, TUE)[-1], n  # the broker's last bar stands
    assert asked == [[UK]] * 3  # every line asked, though the archive lacked nothing in the first
    monkeypatch.setattr(paper, "dial", _no_gateway)
    refusal = history.daily(NOW)([UK], MON)[UK]  # no gateway here: dial refuses
    assert isinstance(refusal, Refused) and "not asked" in refusal.reason


def test_the_brokers_pence_reach_the_keeper_in_pounds_and_a_dollar_line_is_not_scaled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    isf, aapl = Line("ISF", "LSE", "GBP", 1), Line("AAPL", "US", "USD", 1)
    pence = Bar(MON, Decimal("1048.2"), Decimal("1050"), Decimal("1040"), Decimal("1048.2"), 9)
    dollars = Bar(MON, Decimal("200"), Decimal("201"), Decimal("199"), Decimal("200"), 9)
    monkeypatch.setattr(history, "gather", lambda *_: {isf: [pence], aapl: [dollars]})

    def listed(*_: object) -> dict[str, listing.Listing | listing.Unlisted]:
        steps = ((Decimal(0), Decimal("0.01")),)
        return {
            "ISF": listing.Listing(isf, "1", "LSE", 100, steps),
            "AAPL": listing.Unlisted(aapl, "none"),
        }

    monkeypatch.setattr(listing, "kept", listed)
    got = history.daily(NOW, home=tmp_path)([isf, aapl], TUE)
    assert got[isf] == [
        replace(
            pence,
            open=Decimal("10.482"),
            high=Decimal("10.50"),
            low=Decimal("10.40"),
            close=Decimal("10.482"),
        )
    ]
    assert got[aapl] == Refused("none")
    both = {aapl: [dollars]}
    monkeypatch.setattr(
        listing,
        "kept",
        lambda *_: {
            "AAPL": listing.Listing(aapl, "2", "SMART", 1, ((Decimal(0), Decimal("0.01")),))
        },
    )
    assert history.priced(tmp_path, NOW, both, paper.Door(1)) == both
