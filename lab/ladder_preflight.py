"""ladder_preflight - THE SET RUNNER'S PRE-FLIGHT (L20): each line a set's cells read, its own (or
its proxy's) and its market's, read once; a gap in a line's bars refuses the set, a day with no
pound rate is its cell's named reason. Split out of `lab/ladder.py` (O79), which runs it before
anything is written; it never imports the ladder."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from datetime import date

from desk.lines import LINES, Line
from desk.store import Bar
from lab import folds, rung
from lab.batch import Bars
from lab.cell import Cell
from lab.ladder_parts import FAILED, MARKETS, _resolve
from lab.rung import Rates


def inputs(todo: Sequence[Cell], bars: Bars) -> Iterator[tuple[Cell, Sequence[Bar]]]:
    """Each line the set's cells read, its own (or its proxy's) and its market's, from its first
    bar to the window's end, once, one at a time: the set runner's pre-flight (L20). A line whose
    bars cannot be read is its cell's to say, as it does now."""
    seen, asked = set[tuple[str, date, date]](), set[tuple[Line, date, date]]()
    for one in todo:
        if (one.line, one.start, one.end) in asked:  #: a line's window is read once, not per rule
            continue
        asked.add((one.line, one.start, one.end))
        try:
            c, own, _ = _resolve(one, bars)
            beside = next(line for line in LINES if line.symbol == MARKETS[c.line.venue])
            held = bars(beside)
        except FAILED:
            continue
        for line, read in ((c.line, own), (beside, held)):
            if (line.symbol, c.start, c.end) not in seen:
                seen.add((line.symbol, c.start, c.end))
                yield Cell(c.strategy, line, c.start, c.end), read


def preflight(todo: Sequence[Cell], bars: Bars, pounds: Rates) -> None:
    """The set runner's pre-flight (L20) over `inputs`: a gap in a line's bars refuses the set; a
    day with no pound rate does not, it is its cell's named reason (`_unrated`), judged again
    once the one writer fills it from the stored DEXUSUK series (`desk/backfill.py`)."""
    folds.preflight(
        ((c, read) for c, read in inputs(todo, bars) if not _unrated(c, ((c.line, read),), pounds)),
        pounds,
    )


def _unrated(c: Cell, read: Sequence[tuple[Line, Sequence[Bar]]], pounds: Rates) -> str | None:
    """The first day in the cell's window one of its lines has a bar and no rate of pounds, named
    as a gap; None when every such day has its rate."""
    for line, bar in ((line, bar) for line, held in read for bar in held):
        try:
            if c.start <= bar.day <= c.end:
                rung.rate(line, pounds, bar.day)
        except ValueError as gap:  #: named, never passed over: the cell's reason
            return f"a gap in the pound's rates, to be filled from DEXUSUK: {gap}"
    return None


def _priced(bars: Bars, pounds: Rates, rule: str, todo: Sequence[Cell]) -> Bars:
    """The rule's lines as its pooled folds read them: a line with a day unrated in its own cell's
    window (a proxy, in the widest of the rule's) raises, so the pool leaves it out and its gap is
    its own cell's reason, never a FAULT in the folds of the lines beside it."""
    mine = [one for one in todo if one.strategy == rule]

    def read(line: Line) -> Sequence[Bar]:
        own = [one for one in mine if one.line == line] or mine
        span = Cell(rule, line, min(o.start for o in own), max(o.end for o in own))
        if gap := _unrated(span, ((line, held := bars(line)),), pounds):
            raise ValueError(gap)
        return held

    return read
