"""keeper_round - THE KEEPER'S JUDGING OF A ROUND: answers judged by the one store and kept, with
the source of each line's newest bar named, and the lines a call owes (split from keeper)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date, datetime
from pathlib import Path

from desk import bars, history, store
from desk.bars_form import entered
from desk.keeper_rotate import Kept
from desk.lines import DOLLARS, POUND, Line
from desk.store import Bar, Parked, Refused
from desk.store_scope import judge as scoped_judge

TRIES = 6  #: the calls at which a line parked for a fault is asked again (half an hour)


def pound_closes(hot: Path) -> store.Rates:
    """The pound's closes in dollars held (R-RUNGS-16): a bar in dollars is told from a move."""
    return {bar.day: bar.close for bar in _held(hot, POUND) if DOLLARS[0] < bar.close < DOLLARS[1]}


def _source(kept: Sequence[Bar], answer: store.Answer, broker: store.Answer | None) -> str:
    """Who gave a line's newest kept bar: the broker, else the archive (and why not the broker)."""
    gave = [{b.day for b in a} if isinstance(a, list | tuple) else None for a in (broker, answer)]
    day = kept[-1].day if kept else None
    if day in (gave[0] or ()):
        return "IBKR"
    why = "not asked" if gave[0] is None else "gave none"
    return f"archive (IBKR {why})" if day in (gave[1] or ()) else "the shelf, or none"


def _dropped(held: Sequence[Bar], *answers: store.Answer | None) -> set[date]:
    """Days answered whose held bar is the answered one itself (R-DATA-77): an older one stays."""
    shown = {b.day: entered(b) for b in held}
    given = [b for a in answers if not isinstance(a, Refused | None) for b in a]
    return {b.day for b in given if shown.get(b.day, entered(b)) == entered(b)}


def _held(hot: Path, line: Line) -> tuple[Bar, ...]:
    """The daily bars the store shows for a line, none if never kept."""
    try:
        return tuple(bars.daily(hot, line))
    except (LookupError, FileNotFoundError):  # never kept: nothing stands over the archive
        return ()


def _upheld(
    hot: Path, line: Line, held: Sequence[Bar], day: date, rates: store.Rates, dropped: set[date]
) -> set[date]:
    """Of the days dropped and those withdrawn, the ones whose held bar the one judge keeps,
    unchanged, in the line's whole held history (its withdrawn days among it): a day stays
    withdrawn only while that judgement drops it (the withdraw rule's table, pattern 13)."""
    try:
        under = set(bars.daily(hot, line, bars.UNDER))
    except (LookupError, FileNotFoundError):  # never kept: no day of it is withdrawn
        under = set()
    if not under and not dropped:
        return set()
    whole = sorted([*held, *under], key=lambda bar: bar.day)
    kept = set(scoped_judge(line, whole, day, rates)[0])
    return {b.day for b in whole if b in kept and (b in under or b.day in dropped)}


def _standing(hot: Path, line: Line, day: date, broker: store.Answer | None) -> store.Answer | None:
    """The bars standing first: the broker's if given, else those the store holds (R-RUNNER-341)."""
    held = tuple(b for b in _held(hot, line) if b.day >= day - history.RECENT)
    return broker if isinstance(broker, list | tuple) else held or broker


def _kept_in(
    hot: Path,
    answers: Mapping[Line, store.Answer],
    day: date,
    first: Mapping[Line, store.Answer],
    standing: bool = True,
) -> tuple[list[Parked], tuple[str, ...]]:
    """Answers judged by the one store, kept as one round: lines parked, sources in words."""
    parked, rates, named, said, ibkr, judged = (
        [],
        pound_closes(hot),
        dict[str, list[str]](),
        [],
        [],
        [],
    )
    for line, answer in answers.items():  # every line judged first, outside any round
        broker = first.get(line)
        shelf = bars.bridged(hot, line, day, None, answer, broker)
        stands = _standing(hot, line, day, broker) if standing else broker
        kept, faults, park = scoped_judge(line, answer, day, rates, shelf=shelf, broker=stands)
        held, gave = _held(hot, line), broker if isinstance(broker, list | tuple) else ()
        theirs = {(g.day, entered(g)) for g in gave}
        ibkr.append((line, [b for b in kept if (b.day, entered(b)) in theirs]))
        standing_bars = frozenset(held)
        fresh = [b for b in kept if b not in standing_bars]  # a held bar keeps its label
        dropped = _dropped(held, answer, broker) - {b.day for b in kept}
        upheld = _upheld(hot, line, held, day, rates, dropped)
        judged.append((line, fresh, dropped - upheld, upheld))
        parked += [park] if park else []
        named.setdefault(_source(kept, answer, broker), []).append(line.symbol)
        said += [f"{line.symbol}: {f.what}, held" for f in faults if "(broker)" in f.what]
    with bars.writing(hot) as round_:  # the round holds the lock only while it writes
        for line, fresh, withdrawn, restored in judged:
            round_.daily(line, fresh, withdrawn=withdrawn, restored=restored)
    with bars.writing(hot, bars.Source.IBKR) as round_:  # the broker's own bars, so labelled
        for line, own in ibkr:
            round_.days(line, own)
    return parked, (*(f"newest bar from {k}: {', '.join(v)}" for k, v in named.items()), *said)


def _due(last: Kept | None, lines: Sequence[Line], now: datetime) -> tuple[list[Line], int]:
    """The lines asked on this call and its number: all on a date's first, else those still owed."""
    if last is None or last.at.date() != now.date():
        return list(lines), 1
    again = last.refused
    if last.tries < TRIES or len(last.parked) == len(lines):  # as a parked line: TRIES calls
        again |= last.unasked | set(last.parked)
    return [line for line in lines if line.symbol in again], last.tries + 1
