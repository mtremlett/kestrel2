"""headstart - THE OLD DESK'S STORES AS A HEAD START (the operator's ask of 14 November 2026).
The archive forgets a five-minute bar after sixty days; the old desk kept its own since
February 2026, read here once into the fast store. Its numbers are not trusted, so no bar
enters on the old desk's word:

- the line's own daily bar from the archive, cleaned by the one store, must vouch for it: the
  bar lies within that day's high and low, as far out as the store lets an open or a close
  sit (STRETCH). A day with no fresh daily bar vouches for nothing;
- a bar of a line priced in pounds that fits its day only as pence is read as pence; then the
  fast store's own checks: hours, prices that can be, a wrong unit;
- the store must already hold, from another source, bars for some of the same moments, at
  least half agreeing: else nothing proves the clock and the instrument, and none is kept.

What enters is kept under its source's name and only fills moments that hold no bar: a fresh
bar, held or arriving later, wins, and each bar that differs from one held is counted.

The old stores are read and never written, nor is anything written beside them: every store
the data register in the desk's notes tags IMPORT, read by its form (`python -m lab.headstart`,
into the two databases of the data folder). Six forms have a reader: the matrices of Stooq's
bars, the database mark_the_trend.db, the parquet folders of ibkr_store (each venue's own clock) and
stooq_store, mark_the_trend's Stooq files and the raw Stooq zips (Stooq's clock); any other is
counted as having none yet. A source held already is not read again. Indicators are never read."""

from __future__ import annotations

import hashlib
import os
import shutil
import sqlite3
import sys
from collections import Counter
from collections.abc import Callable, Iterable, Mapping, Sequence
from contextlib import suppress
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime, time
from decimal import Decimal
from functools import partial
from pathlib import Path

from desk import archive, bars, store
from desk.bars import EPOCH, Five, Source
from desk.bars_parts import B
from desk.compare import doubt
from desk.lines import LINES, Line
from desk.store import STRETCH, Bar, Refused
from lab.headstart_parts import (  # noqa: F401  # the readers, still reached as lab.headstart.<name>
    MARKET as MARKET,
)
from lab.headstart_parts import (
    PARQUET as PARQUET,
)
from lab.headstart_parts import (
    PENCE as PENCE,
)
from lab.headstart_parts import (
    TREND as TREND,
)
from lab.headstart_parts import (
    WARSAW as WARSAW,
)
from lab.headstart_parts import (
    _ahead as _ahead,
)
from lab.headstart_parts import (
    _named as _named,
)
from lab.headstart_parts import (
    _priced as _priced,
)
from lab.headstart_parts import (
    _stamped as _stamped,
)
from lab.headstart_parts import (
    asked as asked,
)
from lab.headstart_parts import (
    database as database,
)
from lab.headstart_parts import (
    matrices as matrices,
)
from lab.headstart_parts import (
    matrix_days as matrix_days,
)
from lab.headstart_parts import (
    parquet as parquet,
)
from lab.headstart_parts import (
    raw as raw,
)

DAYS = "SELECT ts, close FROM ohlcv WHERE ticker = ? AND timeframe = '1d'"
RAW = "*/5_*_txt*.zip"  #: where Stooq's five-minute zips lie: a dated folder each
_ADJUSTED = "that are the adjusted form of the store's as-traded bars: not taken"
AFTER_ALL = datetime(9000, 1, 1, tzinfo=UTC)  #: after every bar
IMPORT = "| IMPORT |"  #: how a row of the data register naming a store to read in begins


def _vouched(line: Line, bar: B, day: Bar | None) -> B | str:
    """The bar in the line's currency, if its day's fresh daily bar vouches for it; else why
    it does not."""
    if day is None:
        return "on a day with no fresh daily bar to vouch for them"
    low, high = day.low * (1 - STRETCH), day.high * (1 + STRETCH)
    for unit in (Decimal(1), PENCE) if line.currency in archive.PENCE else (Decimal(1),):
        if low <= bar.low * unit and bar.high * unit <= high:
            prices = (bar.open, bar.high, bar.low, bar.close)
            o, h, lo, c = _priced(prices, unit)
            return replace(bar, open=o, high=h, low=lo, close=c)
    return "outside their day's fresh high and low"


@dataclass(frozen=True)
class Adopted:
    """What became of one line's bars from an old store."""

    filled: int  #: bars that entered: each passed every check, on a moment that held none
    met: int  #: bars that passed, on a moment the store already held from another source
    differ: int  #: of those met, the ones that differ from the bar held, which stays
    faults: tuple[str, ...]  #: why the others did not enter


def adopt(
    path: Path,
    source: Source,
    answers: Mapping[Line, Iterable[Five] | Refused],
    daily: Mapping[Line, Sequence[Bar]],
) -> dict[Line, Adopted]:
    """An old store's bars into the fast store at path under its source's name, in one round:
    for each line the bars its fresh daily bars vouch for and the store's checks pass, on the
    moments that hold none. A bar's day is its start's in UTC: both venues trade within one."""
    adopted: dict[Line, Adopted] = {}
    with bars.writing(path, source) as round_:
        for line, given in answers.items():
            if isinstance(given, Refused):
                adopted[line] = Adopted(0, 0, 0, (f"{source.value} gave nothing: {given.reason}",))
                continue
            days = {bar.day: bar for bar in daily.get(line, ())}
            judged = [_vouched(line, bar, days.get(bar.start.date())) for bar in given]
            sound = [bar for bar in judged if isinstance(bar, Five)]
            since = min((bar.start for bar in sound), default=EPOCH)
            kept, found = bars.checked(line, sound, round_.closes(line, since))
            unvouched = Counter(why for why in judged if isinstance(why, str))
            faults = [f"{count} bars {why}" for why, count in sorted(unvouched.items())] + found
            verdict = round_.compare(line, kept)
            if kept and (why := doubt(verdict.met, verdict.differ)):
                faults.append(why)
                kept = []
            raw = [bar for bar in kept if bar.start.date() not in verdict.factors]
            if len(raw) < len(kept):
                faults.append(f"{len(kept) - len(raw)} bars on days {_ADJUSTED}")
            adopted[line] = Adopted(
                round_.five(line, raw), verdict.met, len(verdict.differ), tuple(faults)
            )
    return adopted


@dataclass(frozen=True)
class Tally:
    """One line's five-minute bars of an old store set beside the one store's, by moment."""

    old: int  #: bars the old store gave
    held: int  #: of them, moments the one store holds a bar for
    same: bool  #: the checksum of those held bars equals the checksum of the old bars there
    missing: tuple[datetime, ...]  #: the moments of old bars the one store holds none for


def _sum(given: Iterable[Five]) -> str:
    rows = (
        f"{b.start:%Y%m%d%H%M} {b.open:.6f} {b.high:.6f} {b.low:.6f} {b.close:.6f};" for b in given
    )
    return hashlib.sha256("".join(rows).encode()).hexdigest()


def compare(path: Path, answers: Mapping[Line, Iterable[Five] | Refused]) -> dict[Line, Tally]:
    """For each line an old store gave, its bars beside the one store at path: counts, a checksum
    of the prices at the moments both hold, and the moments only the old store holds, named."""
    tallies: dict[Line, Tally] = {}
    for line, given in answers.items():
        if isinstance(given, Refused):
            continue
        old = sorted(given, key=lambda bar: bar.start)
        have = {bar.start: bar for bar in bars.five(path, line, EPOCH, AFTER_ALL)}
        both = [bar for bar in old if bar.start in have]
        same = _sum(both) == _sum(have[bar.start] for bar in both)
        tallies[line] = Tally(
            len(old), len(both), same, tuple(bar.start for bar in old if bar.start not in have)
        )
    return tallies


def _daily_sum(given: Iterable[Bar]) -> str:
    rows = (f"{b.day:%Y%m%d} {b.open:.6f} {b.high:.6f} {b.low:.6f} {b.close:.6f};" for b in given)
    return hashlib.sha256("".join(rows).encode()).hexdigest()


def compare_days(path: Path, where: Path, lines: Iterable[Line] = LINES) -> dict[Line, Tally]:
    """For each line an old store holds daily rows of, them beside the one store's daily bars at
    path: counts, a checksum of the prices on the days both hold, the days only the old one
    holds (each as midnight UTC). A line the one store holds nothing of: all missing."""
    from lab import headstart_days  # imports this module

    _, read = headstart_days.form(where)
    tallies: dict[Line, Tally] = {}
    for line in lines:
        try:
            old = sorted(read(line, where), key=lambda bar: bar.day)
        except (OSError, ValueError, sqlite3.Error):  # this line is not in that old store
            continue
        try:
            have = {bar.day: bar for bar in bars.daily(path, line)}
        except LookupError:
            have = {}
        both = [bar for bar in old if bar.day in have]
        same = _daily_sum(both) == _daily_sum(have[bar.day] for bar in both)
        gone = tuple(datetime.combine(b.day, time(), UTC) for b in old if b.day not in have)
        tallies[line] = Tally(len(old), len(both), same, gone)
    return tallies


def drill(path: Path, scratch: Path, lines: Iterable[Line] = LINES) -> dict[Line, Tally]:
    """The restore drill: the one store's databases copied to scratch under their own names, and
    each line's whole five-minute history read back from the copy, beside the original's."""
    scratch.mkdir(parents=True)
    for file in filter(Path.is_file, bars.files(path).values()):
        shutil.copy2(file, scratch / file.name)
    held = {}
    for line in lines:
        with suppress(LookupError):  # the store never held this line's five-minute bars
            held[line] = bars.five(path, line, EPOCH, AFTER_ALL)
    return compare(scratch / path.name, held)


def imports(register: Path) -> tuple[Path, ...]:
    """The old stores the register tags IMPORT: a row `| IMPORT |` and a path in backticks."""
    rows = register.read_text(encoding="utf-8").splitlines()
    tagged = [row for row in rows if row.startswith(IMPORT)]
    if not tagged or any(row.count("`") < 2 for row in tagged):
        raise ValueError(f"{register} tags no store IMPORT by its path: {tagged}")
    return tuple(Path(row.split("`")[1]) for row in tagged)


def reader(where: Path) -> tuple[Source, Callable[[Line, Path], tuple[Five, ...]]] | None:
    """An old store's source and how it is read, judged by its form: a database file, a
    folder of some line's matrices, parquet files or Stooq's zips. Any other store has no reader
    yet; one that is not there is refused: the register names it wrongly or its drive is away."""
    if not where.exists():
        raise FileNotFoundError(f"{where}: the register tags it IMPORT, and it is not there")
    if where.suffix == ".db":
        return Source.DATABASE, database
    if any((where / f"{_named(line)}_ts.npy").is_file() for line in LINES):
        return Source.MATRICES, matrices
    if any(where.glob(RAW)):
        return Source.STOOQ_RAW, raw
    if any(where.glob("*.5.parquet")):  # a file a line, mark_the_trend's
        return Source.TREND_STOOQ, partial(parquet, source=Source.TREND_STOOQ)
    if (where / "freq=5").is_dir():  # only ibkr_store keeps a fetch record beside its bars
        found = next((where / "freq=5").glob("*/*/fetch.json"), None)
        source = Source.IBKR_STORE if found else Source.STOOQ_STORE
        return source, partial(parquet, source=source)
    return None


def held(path: Path, source: Source) -> bool:
    """The store at path holds five-minute bars from source already. An old store lands in
    one round, whole or not at all, so one that is held is in, and is not read again."""
    for line in LINES if path.is_file() else ():
        with suppress(LookupError):  # the store never held this line's five-minute bars
            if source in bars.sources(path, line, bars.FIVE):
                return True
    return False


def fresh(path: Path, day: date) -> dict[Line, tuple[Bar, ...]]:
    """The archive's five-minute bars up to day into the store at path, for the old bars to be
    met with, and every line's fresh daily bars before day, cleaned by the one store, to vouch
    for them. An archive giving no line's bars of either span proves nothing: refused."""
    fives = archive.gather(LINES, datetime.combine(day, time(), UTC), archive.fetch_five)
    answers = archive.gather(LINES, day, archive.fetch)
    for span, given in ("five-minute", fives), ("daily", answers):
        if all(isinstance(answer, Refused) for answer in given.values()):
            raise ValueError(f"the archive gave no line's {span} bars before {day}: none proves")
    bars.keep(path, fives)
    return {line: tuple(store.judge(line, answers[line], day)[0]) for line in LINES}


Reader = tuple[Path, Source, Callable[[Line, Path], tuple[Five, ...]]]


def planned(register: Path, path: Path) -> tuple[list[Reader], list[str], list[str]]:
    """The register's IMPORT stores to read, in the order of Source, each a clock's proof for the
    next; those whose source is held already; those with no reader. A second store of one form
    is refused: it would be skipped."""
    todo: list[Reader] = []
    skipped, unread = list[str](), list[str]()
    for where in imports(register):
        how = reader(where)
        if how is None:
            unread.append(where.name)
        elif any(how[0] is source for _, source, _ in todo) or how[0].value in skipped:
            raise ValueError(f"{where}: a second store of the form of {how[0].value}")
        elif held(path, how[0]):
            skipped.append(how[0].value)
        else:
            todo.append((where, *how))
    return sorted(todo, key=lambda one: list(Source).index(one[1])), skipped, unread


def checked(register: Path, path: Path, scratch: Path) -> str:
    """Every old store the register tags IMPORT, set beside the one store at path, per line:
    counts, checksum, the first moments missing; then the restore drill in scratch. Nothing is
    written but the drill's copy, nothing deleted."""
    bad = 0
    for where in imports(register):
        how = reader(where)
        found = {"5m": compare(path, archive.gather(LINES, where, how[1])) if how else {}}
        with suppress(ValueError):  # a store of no daily form has no daily rows to compare
            found["1d"] = compare_days(path, where)
        for span, tallies in found.items():
            for line, tally in tallies.items():
                bad += not tally.same or bool(tally.missing)
                named = ", ".join(f"{at:%Y-%m-%d %H:%M}" for at in tally.missing[:3]) or "none"
                counts = f"old {tally.old}, held {tally.held}"
                match = "match" if tally.same else "DIFFER"
                row = f"{where.name}: {line.symbol} {span}: {counts}; {match}; missing {named}"
                sys.stdout.write(row + "\n")
    restored = drill(path, scratch)
    bad += sum(not t.same or bool(t.missing) for t in restored.values())
    said = (
        f"headstart check: {bad} lines differ or miss bars; drill read back {len(restored)} lines"
    )
    sys.stdout.write(said + "\n")
    return said


def main(register: Path, path: Path, day: date) -> str:
    """Every old store the register tags IMPORT into the fast store at path, met with the
    archive's five-minute bars up to day (which enter first) and vouched for by its daily bars
    before day; one held already is skipped. Each line's fate is said, then one line of counts."""
    todo, skipped, unread = planned(register, path)
    daily = fresh(path, day) if todo else {}
    totals = Counter[str]()
    for where, source, read in todo:
        for line, got in adopt(path, source, archive.gather(LINES, where, read), daily).items():
            counts = f"filled {got.filled}, met {got.met}, differ {got.differ}"
            more = [f"and {len(got.faults) - 4} more"] * (len(got.faults) > 4)
            faults = "; ".join([*got.faults[:4], *more])
            sys.stdout.write(f"{source.value}: {line.symbol}: {counts}; {faults}\n")
            totals.update(filled=got.filled, met=got.met, differ=got.differ)
    left = f"{len(unread)} with no reader yet ({', '.join(unread) or 'none'})"
    bars_in = f"bars filled {totals['filled']}, met {totals['met']}, differ {totals['differ']}"
    said = f"headstart: {len(todo)} old stores read, {len(skipped)} already in, {left}; {bars_in}"
    sys.stdout.write(said + "\n")
    return said


if __name__ == "__main__":
    DATA = Path(os.environ.get("KESTREL2_DATA") or sys.exit("headstart: KESTREL2_DATA is unset"))
    REGISTER, TODAY = DATA.parent / "kestrel2_notes" / "data_register.md", datetime.now(UTC).date()
    if sys.argv[1:] == ["check"]:
        import tempfile

        checked(REGISTER, DATA / bars.LIVE, Path(tempfile.mkdtemp()) / "restore")
        sys.exit()
    try:
        main(REGISTER, DATA / bars.LIVE, TODAY)
        from lab import (
            headstart_days,
            headstart_matrix,
        )  # imports this module: the pass follows the five-minute one

        headstart_matrix.whole(REGISTER, DATA / bars.LIVE, headstart_days.order(), TODAY)
    except (OSError, ValueError, sqlite3.Error, bars.NoRound) as reason:  # the one line, then out
        sys.exit(f"headstart: {type(reason).__name__}: {reason}")
