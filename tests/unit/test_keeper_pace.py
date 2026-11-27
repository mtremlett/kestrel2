"""The keeper's polling ramp: a refusal halves it, a clean round raises it."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from desk import bars, keeper, live, paper
from desk.lines import Line
from desk.spans import Timed


@pytest.mark.parametrize(
    ("minutes", "rate", "refusals", "expected"),
    [(5, 27, 0, 33), (5, 100, 1, 50), (5, 30, 3, 27), (5, 270, 0, 270), (60, 324, 0, 405)],
)
def test_pace(minutes: int, rate: int, refusals: int, expected: int) -> None:
    """A refusal halves to the floor at least; a clean round rises to the ceiling at most."""
    assert keeper.pace(minutes, rate, refusals) == expected


def test_a_polled_run_keeps_its_rate_between_runs(tmp_path: Path) -> None:
    """The first run asks the floor; a clean round raises the rate kept for the next."""
    now = datetime(2026, 11, 17, 10, tzinfo=bars.EPOCH.tzinfo)

    def ask(_line: Line, when: datetime) -> tuple[Timed, ...]:
        price = Decimal(5)
        return (Timed("1m", when - timedelta(minutes=1), price, price, price, price, 1),)

    keeper.polled(tmp_path, now, 5, ask)
    assert (tmp_path / "polled_5.rate").read_text() == "33"


@pytest.mark.parametrize("minutes", [5, 15, 60])
def test_a_polled_round_opens_its_own_client_never_the_live_one(
    minutes: int, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Each interval's door starts as POLLED_CLIENTS[minutes]: never keeper-live's 226."""
    opened: list[int] = []
    real = paper.Door

    def door(client: int) -> paper.Door:
        opened.append(client)
        return real(client)

    monkeypatch.setattr(paper, "Door", door)
    monkeypatch.setattr(keeper, "polled", lambda *_: "polled")
    now = datetime(2026, 11, 17, 10, tzinfo=bars.EPOCH.tzinfo)
    keeper.main(tmp_path, now, ["--polled", str(minutes)])
    assert opened == [live.POLLED_CLIENTS[minutes]] and live.CLIENT not in opened
