"""R-RUNNER-511: the keeper judges every line before its round, so a round holds the lock only
while it writes."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from desk import bars, keeper
from desk.lines import LINES
from desk.store import Bar
from desk.store_scope import judge as judged


def test_a_writer_begins_its_round_while_the_daily_refresh_is_still_judging(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real: Callable[..., Any] = judged
    begun: list[int] = []

    def judge(*args: Any, **kwargs: Any) -> Any:
        with bars.writing(tmp_path / "hot"):  # another writer, within the store's wait
            begun.append(1)
        return real(*args, **kwargs)

    monkeypatch.setattr("desk.keeper.scoped_judge", judge)
    day, line = date(2026, 11, 16), LINES[0]
    answer = (Bar(date(2026, 11, 13), Decimal(10), Decimal(11), Decimal(9), Decimal(10), 100),)
    keeper._kept_in(tmp_path / "hot", {line: answer}, day, {})
    assert begun == [1]
