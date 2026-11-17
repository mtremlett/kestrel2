"""store - THE ONE PRICE STORE AND ITS ONE WRITER. Bars are cleaned once, on entry; a line
that cannot be made clean is parked with a reason and a date, and the others carry on.

The store is rebuilt from the archive on every prepare, so a parked line comes back out by itself
on the first clean day. One file per line, written whole, then swapped in: no half a write."""

from __future__ import annotations

import csv
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import astuple, dataclass, replace
from datetime import date, timedelta
from decimal import Decimal
from itertools import groupby
from pathlib import Path

from desk import venues
from desk.lines import Line
from desk.store_parts import ASTRAY as ASTRAY
from desk.store_parts import BLIP as BLIP
from desk.store_parts import FAR as FAR
from desk.store_parts import FX_FAR as FX_FAR
from desk.store_parts import FX_STEP as FX_STEP
from desk.store_parts import JUMP as JUMP
from desk.store_parts import NO_RATES as NO_RATES
from desk.store_parts import RATE_AGE as RATE_AGE
from desk.store_parts import RECENT as RECENT
from desk.store_parts import Bar as Bar
from desk.store_parts import Fault as Fault
from desk.store_parts import Rates as Rates
from desk.store_parts import _priced as _priced
from desk.store_parts import moves as moves
from desk.store_parts import pound_on as pound_on
from desk.store_parts import same_as_pound as same_as_pound

#: London's auctions can put an open or close just outside the day's range: within this fraction
#: the range stretches (his ruling, 13 Nov 2026).
STRETCH = Decimal("0.03")
#: A run this long, each bar repeating the one before or flat with no volume, is a frozen feed (the
#: longest real run since 2010 is three): dropped and listed.
FROZEN = 5
AGREE = Decimal("0.02")  #: two sources' closes for a session must agree within this (R-RUNNER-189)
PENCE, UNIT_DAYS = Decimal(100), 5  #: a hundredth: a shelf this far under, on this many sessions
UNIT_SHARE = Decimal("0.95")  #: of shared sessions a hundredth under; the rest, its bad days
SPLIT_NEAR = Decimal("0.25")  #: a recorded split is adopted if the jump is this near its ratio
UNRECORDED = "a gap in the archive, or a suspension the line does not record"
COLUMNS = ("day", "open", "high", "low", "close", "volume")
#: Where a line's older bars wait: the store is rebuilt on every prepare, joined to the archive's.
HISTORY = "history"


@dataclass(frozen=True)
class Refused:
    """The archive's answer for a line it would not, or could not, give."""

    reason: str


@dataclass(frozen=True)
class Parked:
    symbol: str
    reason: str
    day: date


def _once(bars: Sequence[Bar], faults: list[Fault]) -> list[Bar]:
    """One bar per date. A date given twice the same keeps one; given twice differently,
    neither, because the store cannot know which is true."""
    by_day: dict[date, list[Bar]] = {}
    for bar in bars:
        by_day.setdefault(bar.day, []).append(bar)
    once = []
    for day, given in sorted(by_day.items()):
        if len(set(given)) > 1:
            faults.append(Fault(day, f"{day} given {len(given)} times, differently; none kept"))
            continue
        if len(given) > 1:
            faults.append(Fault(day, f"{day} given {len(given)} times"))
        once.append(given[0])
    return once


def _entered(line: Line, bar: Bar, open_days: set[date], faults: list[Fault]) -> Bar | str:
    """The bar as it enters the store, or why it cannot be true on its own. A wrong high or low is
    clamped to the open or close and parks the line; a stretch is only noted beside the bar."""
    if bar.day in line.suspended:
        return f"{bar.day} has a bar, yet {line.symbol} records it as suspended"
    if bar.day not in open_days:
        return f"{bar.day} is not a closed session on the {line.venue} calendar, or too early"
    if not all(p.is_finite() and p > 0 for p in astuple(bar)[1:5]) or bar.volume < 0:
        return f"{bar.day} has a price or volume that cannot be"
    ends, reach = (bar.open, bar.close), (bar.low * (1 - STRETCH), bar.high * (1 + STRETCH))
    if not bar.low <= bar.high or not reach[0] <= min(ends) <= max(ends) <= reach[1]:
        return f"{bar.day} has an open or close outside its high and low"
    high, low = max(bar.high, *ends), min(bar.low, *ends)
    bad = (high >= JUMP * max(ends), low <= min(ends) / JUMP)
    if bad[0] or high != bar.high:
        what = f"{bar.day} high {'repaired' if bad[0] else 'stretched'}: was {bar.high}"
        faults.append(Fault(bar.day, what, noted=not bad[0]))
    if bad[1] or low != bar.low:
        what = f"{bar.day} low {'repaired' if bad[1] else 'stretched'}: was {bar.low}"
        faults.append(Fault(bar.day, what, noted=not bad[1]))
    return replace(bar, high=max(ends) if bad[0] else high, low=min(ends) if bad[1] else low)


def _split(bars: list[Bar], day: date, ratio: Decimal, faults: list[Fault]) -> None:
    """Multiply the prices before day by ratio (divide the volume), if the jump across day is the
    ratio within SPLIT_NEAR; a market-sized jump is adjusted already; any other is a fault."""
    at = next((n for n, bar in enumerate(bars) if bar.day >= day), 0)
    if at == 0:
        return
    jump = bars[at].close / bars[at - 1].close
    if 1 / JUMP <= jump <= JUMP:
        return
    if abs(jump / ratio - 1) > SPLIT_NEAR:
        what = f"{day} is recorded as a split of {ratio}, yet the bar's jump is {jump:.4f}"
        faults.append(Fault(day, what, lasting=True))
        return
    for n, bar in enumerate(bars[:at]):
        shares = int((Decimal(bar.volume) / ratio).to_integral_value())
        bars[n] = replace(bar, volume=shares, **{k: getattr(bar, k) * ratio for k in COLUMNS[1:5]})


def _still(before: Bar, bar: Bar) -> bool:
    """The bar repeats the one before it, its volume too or with none, or sits flat at its
    close with none: no market prints the same bar day after day."""
    prices = (bar.open, bar.high, bar.low, bar.close)
    repeated = prices == (before.open, before.high, before.low, before.close)
    flat = all(p == before.close for p in prices)
    return (repeated and bar.volume in (0, before.volume)) or (flat and bar.volume == 0)


def _thawed(kept: Sequence[Bar], faults: list[Fault]) -> list[Bar]:
    """Drop and list every run of FROZEN or more still bars, by the run's last day."""
    still = [at > 0 and _still(kept[at - 1], bar) for at, bar in enumerate(kept)]
    thawed: list[Bar] = []
    for frozen, pairs in groupby(zip(kept, still, strict=True), key=lambda pair: pair[1]):
        run = [bar for bar, _ in pairs]
        if frozen and len(run) >= FROZEN:
            what = f"{run[0].day} to {run[-1].day} repeat one price with no volume: a frozen feed"
            faults.append(Fault(run[-1].day, what))
        else:
            thawed.extend(run)
    return thawed


def _clean(
    line: Line, bars: Sequence[Bar], day: date, since: date, rates: Rates = NO_RATES
) -> tuple[list[Bar], list[Fault]]:
    """The bars of one line that can be true, and every fault found."""
    faults: list[Fault] = []
    first = min((b.day for b in bars if b.day.year in venues.SESSION_YEARS), default=day)
    every = venues.sessions(line.venue, max(first, line.starts or first), day - timedelta(1))
    expected = [d for d in every if d not in line.suspended]
    open_days, sound = set(expected), []
    for bar in _once(bars, faults):
        entered = _entered(line, bar, open_days, faults)
        if isinstance(entered, str):
            faults.append(Fault(bar.day, entered))
        else:
            sound.append(entered)
    for split_day, ratio in sorted(line.splits):
        _split(sound, split_day, ratio, faults)
    kept = _thawed(_priced(line, sound, faults, rates), faults)
    held = {b.day for b in kept}
    missing = [d for d in expected if d not in held]
    if not kept:
        faults.append(Fault(day, "no clean bar: every session missing"))
    for gap in ([d for d in missing if d < since], [d for d in missing if d >= since]):
        if kept and gap:
            what = f"{len(gap)} sessions missing, the first {gap[0]}: {UNRECORDED}"
            faults.append(Fault(gap[0], what))
    return kept, faults


def _write(path: Path, header: Sequence[str], rows: Iterable[Sequence[object]]) -> None:
    part = path.with_suffix(".part")
    with part.open("w", newline="", encoding="utf-8") as out:
        writer = csv.writer(out)
        writer.writerow(header)
        writer.writerows(rows)
    part.replace(path)


Answer = Sequence[Bar] | Refused  #: what the archive gave for a line
Older = Sequence[Bar] | None  #: a line's older bars


def judge(
    line: Line,
    answer: Answer,
    day: date,
    rates: Rates = NO_RATES,
    shelf: Older = None,
    broker: Answer | None = None,
) -> tuple[list[Bar], list[Fault], Parked | None]:
    """THE ONE JUDGEMENT of a line's bars: those that can be true, every fault found and, if one
    is recent or lasting, the line parked, ready to trade on day. The broker's bars stand first
    (his ruling of 16 November), the archive's under them, the shelf's under those. A line none
    gave bars for keeps none, so none from an earlier day can be read as today's."""
    since = venues.sessions(line.venue, day - timedelta(100), day - timedelta(1))[-RECENT]
    top = None if broker is None or isinstance(broker, Refused) else broker
    if isinstance(answer, Refused) and top is None:
        kept: list[Bar] = []
        faults = [Fault(day, f"the archive refused it: {answer.reason}")]
    else:
        joined, faults = ([], []) if isinstance(answer, Refused) else _joined(shelf, answer)
        if top is not None:
            joined, over = _joined(joined, top, "broker", "archive")
            faults += [replace(f, noted=True) for f in over]  # the broker's bar stands: no park
        kept, found = _clean(line, joined, day, since, rates)
        faults = [*faults, *found]
    recent = [f.what for f in faults if not f.noted and (f.lasting or f.day >= since)]
    return kept, faults, Parked(line.symbol, "; ".join(recent), day) if recent else None


def prepare(
    root: Path, archive: Mapping[Line, Answer], day: date, rates: Rates = NO_RATES
) -> tuple[Parked, ...]:
    """Clean the archive's bars into the CSV store at root, ready to trade on day."""
    root.mkdir(parents=True, exist_ok=True)
    parked: list[Parked] = []
    for line, answer in archive.items():
        shelved = (root / HISTORY / f"{line.symbol}.csv").is_file()
        older = read(root / HISTORY, line.symbol) if shelved else None
        kept, faults, park = judge(line, answer, day, rates, older)
        _write(root / f"{line.symbol}.csv", COLUMNS, (astuple(bar) for bar in kept))
        _write(root / f"{line.symbol}.faults.csv", ("fault",), ((f.what,) for f in faults))
        parked += [park] if park else []
    return tuple(parked)


def shelve(root: Path, line: Line, bars: Iterable[Bar]) -> None:
    """A line's older bars, kept for every prepare to join to the archive's, replacing any
    shelved before. They are cleaned as the archive's are, with it, on each prepare."""
    (root / HISTORY).mkdir(parents=True, exist_ok=True)
    _write(root / HISTORY / f"{line.symbol}.csv", COLUMNS, (astuple(bar) for bar in bars))


def _joined(
    shelf: Older, bars: Sequence[Bar], over: str = "archive", under: str = "shelf"
) -> tuple[list[Bar], list[Fault]]:
    """The upper source's bars, a lower one's bar for each day it gives none; closes both give
    beyond AGREE are a fault naming both, the upper's standing. A frozen run is dropped. A shelf a
    hundredth of the upper's on UNIT_SHARE of its shared sessions is in the wrong unit (IB1T, 250
    of 255): put right bar by bar; days still apart are named, the line not parked."""
    if shelf is None:
        return list(bars), []
    given = {bar.day: bar for bar in _thawed(bars, [])}
    pairs = [(b.close, given[b.day].close) for b in shelf if b.day in given and under == "shelf"]
    fits = sum(abs(PENCE * lo / up - 1) <= AGREE for lo, up in pairs) >= UNIT_SHARE * len(pairs)
    unit = len(pairs) >= UNIT_DAYS and fits
    lower = [replace(b, **{k: getattr(b, k) * PENCE for k in COLUMNS[1:5]}) for b in shelf]
    put = [Fault(b.day, f"{b.day} {under} put right: a unit fault", noted=True) for b in lower]
    lower, put = (lower, put) if unit else (list(shelf), [])
    differ = [
        Fault(b.day, f"{b.day} close {a.close} ({over}), {b.close} ({under})", noted=unit)
        for b in lower
        if (a := given.get(b.day)) and abs(b.close / a.close - 1) > AGREE
    ]
    fills = [bar for bar in lower if bar.day not in given]
    return sorted([*fills, *given.values()], key=lambda x: x.day), put + differ


def _bar(r: Mapping[str, str]) -> Bar:
    o, h, low, c = (Decimal(r[name]) for name in COLUMNS[1:5])
    return Bar(date.fromisoformat(r["day"]), o, h, low, c, int(r["volume"]))


def read(root: Path, symbol: str) -> tuple[Bar, ...]:
    """Every bar the store kept for one line, oldest first (a parked line's too)."""
    with (root / f"{symbol}.csv").open(newline="", encoding="utf-8") as stored:
        return tuple(_bar(r) for r in csv.DictReader(stored))


def faults(root: Path, symbol: str) -> tuple[str, ...]:
    """Every fault found in a line's bars on the last prepare, the old ones that no longer
    park it included."""
    with (root / f"{symbol}.faults.csv").open(newline="", encoding="utf-8") as stored:
        return tuple(row["fault"] for row in csv.DictReader(stored))
