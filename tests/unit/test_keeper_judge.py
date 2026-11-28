"""R-RUNNER-511: the keeper judges every line before its round, so a round holds the lock only
while it writes."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import nullcontext
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from desk import bars, keeper, keeper_parts
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

    monkeypatch.setattr("desk.keeper_parts.scoped_judge", judge)
    day, line = date(2026, 11, 16), LINES[0]
    answer = (Bar(date(2026, 11, 13), Decimal(10), Decimal(11), Decimal(9), Decimal(10), 100),)
    keeper._kept_in(tmp_path / "hot", {line: answer}, day, {})
    assert begun == [1]


def test_a_judged_round_compares_each_held_bar_a_few_times_not_the_whole_history(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    n, line, day = 400, LINES[0], date(2026, 11, 16)
    ten = Decimal(10)
    held = tuple(Bar(date(2020, 1, 1) + timedelta(days=i), ten, ten, ten, ten, 1) for i in range(n))
    kept = [replace(b) for b in held]  # equal, never the same object
    writer = SimpleNamespace(daily=lambda *_a, **_k: None, days=lambda *_a, **_k: None)
    monkeypatch.setattr(keeper, "_held", lambda *_a: held)
    monkeypatch.setattr(keeper, "pound_closes", lambda *_a: {})
    monkeypatch.setattr(bars, "bridged", lambda *_a: None)
    monkeypatch.setattr(keeper_parts, "scoped_judge", lambda *_a, **_k: (kept, [], None))
    monkeypatch.setattr(bars, "writing", lambda *_a: nullcontext(writer))
    compares: list[int] = []
    real_eq: Any = Bar.__eq__

    def counting(self: Bar, other: object) -> bool:
        compares.append(1)
        return bool(real_eq(self, other))

    monkeypatch.setattr(Bar, "__eq__", counting)
    keeper._kept_in(tmp_path / "hot", {line: ()}, day, {})
    assert len(compares) <= 3 * n
