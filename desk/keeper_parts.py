"""The keeper's lower parts: the pound's closes held, and a round's answers judged by the one
store and kept whole, each newest bar's source named. desk.keeper gives them to its callers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date
from pathlib import Path

from desk import bars, history, store
from desk.lines import DOLLARS, POUND, Line
from desk.store import Bar, Parked, Refused
from desk.store_scope import judge as scoped_judge


def pound_closes(hot: Path) -> store.Rates:
    """The pound's closes in dollars held (R-RUNGS-16): a bar in dollars is told from a move."""
    try:
        held = bars.daily(hot, POUND)
    except (LookupError, FileNotFoundError):  # never kept: no close is held
        held = ()
    return {bar.day: bar.close for bar in held if DOLLARS[0] < bar.close < DOLLARS[1]}


def _source(kept: Sequence[Bar], answer: store.Answer, broker: store.Answer | None) -> str:
    """Who gave a line's newest kept bar: the broker, else the archive (and why not the broker)."""
    gave = [{b.day for b in a} if isinstance(a, list | tuple) else None for a in (broker, answer)]
    day = kept[-1].day if kept else None
    if day in (gave[0] or ()):
        return "IBKR"
    why = "not asked" if gave[0] is None else "gave none"
    return f"archive (IBKR {why})" if day in (gave[1] or ()) else "the shelf, or none"


def _dropped(kept: Sequence[Bar], *answers: store.Answer | None) -> set[date]:
    """The days the answers gave that the judge did not keep: withdrawn, never deleted."""
    given = {b.day for a in answers if not isinstance(a, Refused | None) for b in a}
    return given - {b.day for b in kept}


def _standing(hot: Path, line: Line, day: date, broker: store.Answer | None) -> store.Answer | None:
    """The bars that stand first for a line: the broker's if it gave any this call, else the days
    of its window the store already holds, so a call that did not ask the broker leaves its bars
    as they are and the archive restates none (R-RUNNER-341)."""
    if isinstance(broker, list | tuple):
        return broker
    try:
        return tuple(b for b in bars.daily(hot, line) if b.day >= day - history.RECENT) or broker
    except (LookupError, FileNotFoundError):
        return broker  # the line was never kept: nothing stands over the archive


def _kept_in(
    hot: Path,
    answers: Mapping[Line, store.Answer],
    day: date,
    first: Mapping[Line, store.Answer],
    standing: bool = True,
) -> tuple[list[Parked], tuple[str, ...]]:
    """The answers judged by the one store and kept as one round, whole; the lines parked, and in
    words each source of a newest bar and each close the broker and the archive differ on."""
    parked, rates, named, said = [], pound_closes(hot), dict[str, list[str]](), []
    with bars.writing(hot) as round_:
        for line, answer in answers.items():
            broker = first.get(line)
            shelf = bars.bridged(hot, line, day, None, answer, broker)
            stands = _standing(hot, line, day, broker) if standing else broker
            kept, faults, park = scoped_judge(line, answer, day, rates, shelf=shelf, broker=stands)
            round_.daily(line, kept, withdrawn=_dropped(kept, answer, broker))
            parked += [park] if park else []
            named.setdefault(_source(kept, answer, broker), []).append(line.symbol)
            said += [f"{line.symbol}: {f.what}, held" for f in faults if "(broker)" in f.what]
    return parked, (*(f"newest bar from {k}: {', '.join(v)}" for k, v in named.items()), *said)
