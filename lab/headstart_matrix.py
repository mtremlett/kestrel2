"""headstart_matrix - THE OLD STOOQ MATRICES' 15-MINUTE, 30-MINUTE AND HOURLY ARRAYS (R-RUNNER-10,
his ruling of 16 November 2026: history keeps every timeframe). Read-only, under Source.
MATRIX_INTRADAY. The arrays keep Stooq's clock as if UTC: a 15- or 30-minute bar is stamped by its
start, an hourly one by the hour it ends. Each bar is named by its start in UTC, must be vouched for
by its day's fresh daily bar and pass the one store's checks; a moment already held keeps its bar,
and a line whose span is already in is not read again (`python -m lab.headstart_matrix`)."""

from __future__ import annotations

import os
import sqlite3
import sys
from datetime import timedelta
from pathlib import Path

import numpy as np

from desk import bars
from desk.bars import Five, Source
from desk.lines import Line
from desk.spans import EPOCH
from lab import headstart, headstart_days, headstart_hours

#: Each span the arrays keep for the history, and how far Stooq's stamp lies after a bar's start.
ENDS = {"15m": timedelta(0), "30m": timedelta(0), "1h": timedelta(hours=1)}


def spans(line: Line, folder: Path, span: str) -> tuple[Five, ...]:
    """A line's bars of a span from the matrices in folder, each named by its start in UTC."""
    name = headstart._named(line, span)  # noqa: SLF001  # the one name of a line's arrays
    stamps = np.load(folder / f"{name}_ts.npy").tolist()
    rows = zip(stamps, np.load(folder / f"{name}_ohlcv.npy").T, strict=True)
    return headstart._stamped(  # noqa: SLF001  # the one reading of Stooq's clock
        ((EPOCH + timedelta(milliseconds=at) - ENDS[span], *row) for at, row in rows),
        True,
    )


def one(line: Line, old: Path, path: Path) -> str:
    """A line's arrays of every span into the databases, said in one line; a span already in is
    left, one the arrays do not hold is said."""
    said = []
    for span in ENDS:
        if headstart_hours.held(path, line, span, Source.MATRIX_INTRADAY):
            said.append(f"{span} already in")
            continue
        try:
            given = spans(line, old, span)
        except FileNotFoundError:
            said.append(f"{span} not held")
            continue
        said.append(
            headstart_hours.enter(line, given, path, span, Source.MATRIX_INTRADAY).split(": ", 1)[1]
        )
    return f"{line.symbol}: " + "; ".join(said)


if __name__ == "__main__":
    DATA = Path(os.environ.get("KESTREL2_DATA") or sys.exit("headstart_matrix: no KESTREL2_DATA"))
    try:
        FOUND = headstart.imports(DATA.parent / "kestrel2_notes" / "data_register.md")
        OLDS = [p for p in FOUND if p.name == "stooq_store_matrix"]
        OLDS or sys.exit("headstart_matrix: the register tags no matrices store IMPORT")
        for OLD in OLDS:
            headstart_hours.main(OLD, DATA / bars.LIVE, headstart_days.order(), one)
    except (OSError, ValueError, sqlite3.Error, bars.NoRound) as reason:
        sys.exit(f"headstart_matrix: {type(reason).__name__}: {reason}")
