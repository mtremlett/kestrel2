"""The one form a bar enters the store in: a float and a text form of a day are one bar, and a
repeat writes no correction (R-RUNNER-341)."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import replace
from datetime import date
from decimal import Decimal
from pathlib import Path

from desk import bars
from desk.lines import LINES
from desk.store import Bar

LINE = LINES[0]
TEXT = Bar(
    date(2026, 11, 18),
    Decimal("760.0700"),
    Decimal("760.1200"),
    Decimal("747.8800"),
    Decimal("754.3700"),
    7,
)
FLOAT = replace(
    TEXT,
    open=Decimal(760.0700073242188),
    high=Decimal(760.1199951171875),
    low=Decimal(747.8800048828125),
    close=Decimal(754.3699951171875),
)


def _corrections(folder: Path) -> list[tuple[int]]:
    with closing(sqlite3.connect(folder / bars.HISTORY)) as raw:
        return raw.execute("SELECT volume FROM correction").fetchall()


def test_a_float_and_a_text_form_of_one_day_are_one_bar_and_a_repeat_corrects_nothing(
    tmp_path: Path,
) -> None:
    store = tmp_path / bars.LIVE
    for given in (TEXT, FLOAT, TEXT, FLOAT):
        with bars.writing(store) as round_:
            round_.daily(LINE, [given])
    assert _corrections(tmp_path) == [] and bars.daily(store, LINE) == (TEXT,)
    with bars.writing(store) as round_:
        round_.daily(LINE, [replace(TEXT, volume=8)])  # a real change is still corrected, once
    assert _corrections(tmp_path) == [(7,)]
