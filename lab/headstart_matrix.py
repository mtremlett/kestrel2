"""headstart_matrix - THE OLD STOOQ MATRICES' 15-MINUTE, 30-MINUTE AND HOURLY ARRAYS (R-RUNNER-10,
his ruling of 16 November 2026: history keeps every timeframe). Read-only, under Source.
MATRIX_INTRADAY. The arrays keep Stooq's clock as if UTC: a 15- or 30-minute bar is stamped by its
start, an hourly one by the hour it ends. Each bar is named by its start in UTC, must be vouched for
by its day's fresh daily bar and pass the one store's checks; a moment already held keeps its bar,
and a line whose span is already in is not read again (`python -m lab.headstart_matrix`)."""

from __future__ import annotations

import os
import re
import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np

from desk import bars
from desk.bars import Five, Source
from desk.lines import Line
from desk.spans import EPOCH
from lab import headstart, headstart_days, headstart_hours, headstart_parts

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


#: Each span the database keeps that the store can check (a one-minute bar is no five-minute mark).
TREND = ("1m", "15m", "30m", "1h", "4h", "1wk")


def trend(line: Line, old: Path, path: Path) -> str:
    """A line's rows of each timeframe in the old database into the history, under its own
    source, said in one line: a span already in is left, off-mark rows are counted refused."""
    said = []
    for span in TREND:
        if headstart_hours.held(path, line, span, Source.DATABASE):
            said.append(f"{span} already in")
            continue
        try:
            given, off = headstart_parts.timeframe(line, old, span)
        except ValueError:
            said.append(f"{span} not held")
            continue
        text = headstart_hours.enter(line, given, path, span, Source.DATABASE).split(": ", 1)[1]
        said.append(f"{text}; {off} off its marks refused")
    return f"{line.symbol}: " + "; ".join(said)


FILLED = re.compile(r"(\d+) (?:\w+ )*?filled")
DIFFER = re.compile(r"(\d+) of \d+ days held differ")


def whole(register: Path, path: Path, lines: list[Line], day: date) -> str:
    """The pass after the five-minute one (R-RUNNER-349): each IMPORT store's daily, hourly and
    matrix rows into the database at path, the database's first; a store already in is skipped
    by its readers. One line of counts per store: filled, refused, in disagreement."""
    stores = sorted(headstart.imports(register), key=lambda p: p.suffix != ".db")
    said = []
    for old in stores:
        got = []
        if old.suffix == ".db" or headstart_days._daily(old):  # noqa: SLF001  # the one test of form
            got.append(headstart_days.main(old, path, lines, day))
        if (old / "freq=h").is_dir():
            got.append(headstart_hours.main(old, path, lines))
        if old.suffix == ".db":
            got.append(headstart_hours.main(old, path, lines, trend))
        if old.name == "stooq_store_matrix":
            got.append(headstart_hours.main(old, path, lines, one))
        text = "\n".join(got)
        counts = (
            sum(int(n) for n in FILLED.findall(text)),
            text.count(": refused:"),
            sum(int(n) for n in DIFFER.findall(text)),
        )
        said.append(f"{old.name}: filled {counts[0]}, refused {counts[1]}, differ {counts[2]}")
    sys.stdout.write("\n".join(said) + "\n")
    return "\n".join(said)


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
