"""rung_regimes - THE LADDER'S FIFTH RUNG (R-RUNNER-122): two regime windows, judged apart.

A cell's window is cut at its middle day into two windows, each a stretch of the history in its
own regime. The cell's trades are priced once by the first rung (`lab/rung.py`), after the
broker's costs, and each trade belongs to the window of the day it was bought. Each window is
then judged by the first rung's own rule (`rung.verdict`) on its own trades: it needs its own
MIN_TRADES and its own T_PASS standard errors. A trade held across the cut belongs to the
window it was bought in.
THE RULE: a rule passes only when BOTH windows pass. One strong window is not enough: an
edge that earned in one stretch alone, and bled in the other, is a stretch's luck. Otherwise
the answer is the first rung's least of the two, so a window too thin to say holds the whole
at THIN and never fails it.

THE TAPE. It reads the tape of R-RUNNER-118 (`lab/tape.py`) through `cell.run`, and its result
is keyed by that tape's key plus this module's code (`Key.rung`), so a rung edited prices
again and simulates nothing.

BY THE WEATHER (REG-01, `lab/weather.py`). `by_weather` cuts the same priced trades not at a
day but by the trend state of the day each was bought: `up` and `down` are each judged alone,
by the same rule, and both must pass. A trade bought while the weather is still `warming` has
no regime yet and is left out; a day the weather never named is a fault, not a guess. Each
state is GRADED (`graded`, L19): thirty trades a state cannot prove a real edge in both (a t of
3 over 60 trades is about 2.1 in each), so a state of enough trades short of T_PASS is DOUBT,
and only one T_PASS standard errors below nothing FAILS; the verdict scores the rung soft
(MAX_WEAK), and a power case in its tests holds that fair.

PROVEN ALONE, by `tests/unit/test_lab_rung_regimes.py`: a planted edge passes; noise passes
at the rate of two windows both clearing the bar by chance; a broken copy is caught.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import date

from desk.orders import Settings
from desk.store import Bar
from lab import cell, rung, weather
from lab.cell import Key, Record
from lab.reproduce import Reproduction
from lab.rung import Answer, Priced, Rates, Rung, Verdict

WINDOWS = 2


@dataclass(frozen=True)
class Regimes:
    """A cell judged in its two windows apart, and the one answer over them."""

    key: Key  #: the tape's key and this module's code
    cut: date  #: the first day of the second window
    first: Verdict
    second: Verdict

    @property
    def answer(self) -> Answer:
        """The one rule over the two windows' answers."""
        return decide(self.first.answer, self.second.answer)

    @property
    def passed(self) -> bool:
        """Both windows earned."""
        return self.answer is Answer.PASS


def decide(first: Answer, second: Answer) -> Answer:
    """The rung's one rule: the least of the two windows' answers, so both must pass."""
    return min(first, second)


def graded(window: Verdict) -> Answer:
    """A window's answer on the three bands (`rung.band`): enough trades short of T_PASS is a
    DOUBT, and only a window T_PASS standard errors below nothing FAILS."""
    failed = window.answer is Answer.FAIL
    return rung.band(window.t) if failed and window.t is not None else window.answer


def judge(
    record: Record,
    bars: Sequence[Bar],
    settings: Settings,
    rates: Rates,
    reproduced: Sequence[Reproduction] = (),
) -> Regimes:
    """The record's trades priced once, then judged in each of its two windows apart."""
    whole = rung.judge(record, bars, settings, rates, reproduced)
    days = [
        bar.day for bar in cell.shown(record.key.cell, bars) if bar.day >= record.key.cell.start
    ]
    if len(days) < WINDOWS:
        raise ValueError(f"{record.key.cell}: {len(days)} bars cannot be cut into two windows")
    return apart(record.key.rung(__name__), whole.trades, days[len(days) // 2], reproduced)


def apart(
    key: Key, priced: Sequence[Priced], cut: date, reproduced: Sequence[Reproduction] = ()
) -> Regimes:
    """Priced trades judged in the window before the cut and the window from it."""
    before = tuple(p for p in priced if p.trade.bought < cut)
    after = tuple(p for p in priced if p.trade.bought >= cut)
    return Regimes(
        key,
        cut,
        rung.verdict(_window(key, "first", cut), before, reproduced),
        rung.verdict(_window(key, "second", cut), after, reproduced),
    )


def _window(key: Key, name: str, cut: date) -> Key:
    """The key of one window: the result's, with the window and its cut told into the data."""
    told = f"{key.data}\n{name}\n{cut}"
    return replace(key, data=hashlib.sha256(told.encode()).hexdigest())


@dataclass(frozen=True)
class Weathered:
    """A cell judged in the trend state it was bought in, up and down apart."""

    key: Key
    up: Verdict
    down: Verdict

    @property
    def answer(self) -> Answer:
        """The same rule over the two states: both must pass. A state the rule never traded in
        is too thin to say (the weather's fault, not the rule's), never a FAULT."""
        return decide(*(graded(v) if v.trades else Answer.THIN for v in (self.up, self.down)))


def by_weather(
    key: Key,
    priced: Sequence[Priced],
    labels: Mapping[date, str],
    reproduced: Sequence[Reproduction] = (),
) -> Weathered:
    """Priced trades judged apart in the up days and the down days they were bought on."""
    up, down = in_regimes(
        key,
        priced,
        (weather.UP, weather.DOWN),
        labels.__getitem__,
        dict.fromkeys((weather.UP, weather.DOWN), str(date.min)),
        reproduced,
    ).values()
    return Weathered(key, up, down)


def in_regimes(
    key: Key,
    priced: Sequence[Priced],
    names: Sequence[str],
    label: Callable[[date], str],
    told: Mapping[str, str],
    reproduced: Sequence[Reproduction] = (),
) -> dict[str, Verdict]:
    """The one regime cut: each named regime's priced trades, those bought on a day `label`
    gives that name, judged apart by the first rung. Each verdict's key is the result's with
    the regime and `told[name]` told into the data."""
    return {
        name: rung.verdict(
            replace(
                key, data=hashlib.sha256(f"{key.data}\n{name}\n{told[name]}".encode()).hexdigest()
            ),
            tuple(p for p in priced if label(p.trade.bought) == name),
            reproduced,
        )
        for name in names
    }


def _judged(first: Verdict) -> tuple[Answer, str]:
    """The regimes rung as the ladder reads it: the cell's window cut at its middle day, each
    half judged apart by the first rung's rule; the least answer, both halves in words."""
    cell_ = first.key.cell
    cut = cell_.start + (cell_.end - cell_.start) / WINDOWS
    split = apart(first.key, first.trades, cut, first.reproduced)
    words = f"first window {split.first.answer.name}, second {split.second.answer.name}"
    return split.answer, f"{words}, cut at {cut}; both must pass"


RUNG = Rung("regimes", "both halves of the window pass the first rung's rule", _judged)
