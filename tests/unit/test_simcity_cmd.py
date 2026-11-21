"""simcitycmd: the worlds' time follows the number of worlds asked, one named allowance each."""

from __future__ import annotations

import sys
import time
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from desk import command, simcity, simcitycmd
from desk.orders import Settings

sys.path.insert(0, str(Path(__file__).parents[1] / "scenes"))  #: the scenes' rehearsal data
from rehearsal import CLEAN, SESSIONS  # noqa: E402  the path above comes first

RUNNER_JOB = 6 * 3600.0  #: the hours the runner gives the weekend's deep job


def test_the_worlds_time_follows_their_number_and_a_world_fits_its_allowance(
    tmp_path: Path,
) -> None:
    """--full's hundred worlds get more than the old flat two hours and end inside the runner's
    six; the weekday twenty keep a real limit; one world on the fixture fits its allowance."""
    assert simcitycmd.allowance(simcity.WORLDS) > 7200.0
    assert simcitycmd.allowance(simcity.WORLDS) < RUNNER_JOB
    assert simcitycmd.allowance(simcitycmd.QUICK) * 5 == simcitycmd.allowance(simcity.WORLDS)
    saved = {x: tuple(b for b in bars if b.day <= SESSIONS[50]) for x, bars in CLEAN.items()}
    rates = {"GBP": Decimal(1), "USD": Decimal("0.79")}
    began = time.monotonic()
    simcity.run(
        tmp_path,
        saved,
        Settings(command.CAPITAL),
        rates,
        datetime(2025, 11, 17, tzinfo=UTC),
        range(1),
    )
    assert time.monotonic() - began < simcitycmd.PER_WORLD
