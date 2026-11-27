"""quality - THE DATA QUALITY MONITOR (R-RUNNER-217, his ruling of 16 November 2026), first steps:
the daily timeframe, then the rollups. Every line's daily bars are audited against its venue's
calendar (a session with no bar is a gap; a fault is whatever the store's own checks find), each
gap is backfilled by desk/backfill.py (the broker, then the archive), the line is audited again,
and one line is printed: green, or what stays red and why. The coarser timeframes the store
can build (1h, 4h, 1wk) are rolled up from the finer bars it holds, and a built bar that differs
from a pulled one is a red fault. Exit 0 only when green."""

from __future__ import annotations

import csv
import filecmp
import json
import os
import shutil
import sys
from collections.abc import Callable, Iterable, Sequence
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from functools import partial
from pathlib import Path

from desk import archive, backfill, bars, coverage, history_write, keeper, venues
from desk.bars import Source
from desk.lines import LINES, Line
from desk.spans import EPOCH, FIVE, SPANS, Five, Timed
from desk.store import AGREE, Bar, Refused
from desk.store import _clean as cleaned


def _missing(line: Line, held: tuple[Bar, ...], today: date) -> list[date]:
    """The sessions from the first held bar to yesterday on which the line holds none."""
    days = {bar.day for bar in held}
    first = min(days, default=today)
    return [d for d in venues.sessions(line.venue, first, today - timedelta(1)) if d not in days]


def _through(line: Line, now: datetime) -> date:
    """The day before which the store's checks hold sessions closed: today once the venue's
    session of today has closed (its auction ended) by now, else the day after it is excluded."""
    today = now.date()
    traded = venues.sessions(line.venue, today, today) == (today,)
    return (
        today + timedelta(1) if traded and venues.hours(line.venue, today).auction <= now else today
    )


def audit(path: Path, line: Line, now: datetime) -> list[str]:
    """What is red about one line's daily bars as of now: its gaps, then each un-noted fault
    the store's checks find on a day that is not itself a gap. A session closed by now counts."""
    today, held = now.date(), backfill._held(path, line)
    if not held:
        return [f"{line.symbol}: holds no daily bar"]
    gaps = _missing(line, held, today)
    found = [
        f
        for f in cleaned(line, held, _through(line, now), today)[1]
        if not f.noted and f.day not in gaps
    ]
    red = [f"{line.symbol}: {len(gaps)} sessions missing, the first {gaps[0]}"] if gaps else []
    return red + [f"{line.symbol}: {f.what}" for f in found]


def gaps(path: Path, lines: Iterable[Line], today: date) -> list[tuple[Line, date]]:
    """Every gap of every line, for the filler."""
    return [
        (line, day) for line in lines for day in _missing(line, backfill._held(path, line), today)
    ]


def rolled(path: Path, line: Line, today: date) -> tuple[int, list[str]]:
    """The line's coarser bars built from its finer ones, and how many landed, with the faults
    where a built bar differs from one held. A line holding no finer bars has nothing to build."""
    now = datetime.combine(today, time(), UTC)
    return history_write.roll(path, line, now), history_write.clashes(path, line, now)


SHORT = (
    "1m",
    "2m",
    FIVE,
    "10m",
    "15m",
    "30m",
    "1h",
    "4h",
)  #: the intraday timeframes audited for thin sessions


def _starts(path: Path, line: Line, span: str, until: datetime) -> list[datetime]:
    """When the line's bars of one short span start, as held; a span never held has none."""
    try:
        if span == FIVE:
            return [b.start for b in bars.five(path, line, EPOCH, until)]
        return [b.start for b in bars.timed(path, line, span, EPOCH, until)]
    except LookupError:  # the store never held this span for the line: nothing to be short of
        return []


def thin(path: Path, line: Line, today: date) -> list[str]:
    """For each short timeframe, the sessions between the first and the last bar held on which
    the line holds none, each named red; where a finer span holds bars on all of them the
    line says it is rollable from that span, else that no source holds them yet."""
    until, red = datetime.combine(today, time(), UTC), []
    finer: dict[str, set[date]] = {}
    for span in SHORT:
        days = {start.date() for start in _starts(path, line, span, until)}
        short = (
            [d for d in venues.sessions(line.venue, min(days), max(days)) if d not in days]
            if days
            else []
        )
        if short:
            base = next((f for f, held in finer.items() if set(short) <= held), None)
            how = f", rollable from {base}" if base else ", no source holds them yet"
            first = f"{len(short)} sessions with no {span} bar, the first {short[0]}"
            red.append(f"{line.symbol}: {first}{how}")
        if days:
            finer[span] = days
    return red


VOLUME_TOLERANCE = 0.5  #: a day's five-minute volume may exceed the daily bar's by this share


def volumes(path: Path, line: Line, today: date) -> list[str]:
    """The days on which the summed five-minute volume exceeds the daily bar's by more than the
    tolerance (a second feed counted twice). Five-minute bars short of the daily volume are a
    thin session, not a volume fault."""
    total: dict[date, int] = {}
    try:
        fives = bars.five(path, line, EPOCH, datetime.combine(today, time(), UTC))
    except LookupError:  # the store never held five-minute bars for the line: nothing to sum
        return []
    for five in fives:
        total[five.start.date()] = total.get(five.start.date(), 0) + five.volume
    daily = {held.day: held.volume for held in backfill._held(path, line)}
    off = sorted(
        d for d, v in total.items() if d in daily and v > daily[d] * (1 + VOLUME_TOLERANCE)
    )
    if not off:
        return []
    return [
        f"{line.symbol}: {len(off)} days with five-minute volume over the daily, first {off[0]}"
    ]


BASIS = {  #: sources whose prices are one adjustment basis; any other source is its own
    bars.Source.IBKR: "IBKR",
    bars.Source.IBKR_DAILY: "IBKR",
    bars.Source.BACKFILL: "archive",
    bars.Source.ARCHIVE: "archive",
}


def basis(path: Path, line: Line) -> list[str]:
    """Red when the line's daily series is kept from more than one adjustment basis (a rule
    reading across a basis change sees a false jump); the bases are named, IBKR's first."""
    try:
        held = bars.sources(path, line, bars.DAILY)
    except LookupError:  # the store never held this line's daily bars: no basis to mix
        return []
    named = {BASIS.get(source, source.value) for source in held}
    if len(named) < 2:
        return []
    return [f"{line.symbol}: daily series mixes bases: {', '.join(sorted(named))}"]


def covered(path: Path, lines: list[Line], now: datetime) -> tuple[str, bool]:
    """The desk's coverage score said in words, and whether the parked share is within its cap."""
    held = {}
    for line in lines:
        try:
            held[line.symbol] = len(bars.daily(path, line))
        except LookupError:  # the store never held this line's daily bars: no sessions
            held[line.symbol] = 0
    parked = keeper.parked_live(path, lines, now)
    score = coverage.desk_score(coverage.measure(held, parked))
    return f"coverage {score:.2f}", coverage.parked_within_cap(held, parked)


FREE_FLOOR = 0.10  # the share of its drive the store's folder must leave free (OPS-07)


def disk(home: Path) -> list[str]:
    """Red when the drive holding the store has less than FREE_FLOOR of itself free."""
    usage = shutil.disk_usage(home)
    share = usage.free / usage.total
    if share >= FREE_FLOOR:
        return []
    return [f"disk: {share:.0%} free on the drive of {home.name}, floor {FREE_FLOOR:.0%}"]


def rolloff(old: Path, kept: Path) -> tuple[list[Path], list[Path]]:
    """Roll old research files off the drive (OPS-07, his 23 Nov ruling): a file whose copy of
    the same relative name under `kept` matches it byte for byte is a true duplicate and is
    deleted; every other file is only returned, to be listed for his yes. -> (deleted, listed)."""
    deleted, listed = [], []
    for file in sorted(f for f in old.rglob("*") if f.is_file()):
        twin = kept / file.relative_to(old)
        if twin.is_file() and filecmp.cmp(file, twin, shallow=False):
            file.unlink()
            deleted.append(file)
        else:
            listed.append(file)
    return deleted, listed


def _held_rows(file: Path, home: Path, lines: Iterable[Line]) -> bool:
    """True when the file is a CSV of daily bars (symbol, day, open, high, low, close, volume)
    and the store holds every row exactly; unreadable, unknown or differing, False."""
    by_name, held = {line.symbol: line for line in lines}, {}
    try:
        with file.open(newline="", encoding="utf-8") as rows:
            for row in csv.DictReader(rows):
                line = by_name[row["symbol"]]
                if line.symbol not in held:
                    held[line.symbol] = {b.day: b for b in backfill._held(home / keeper.HOT, line)}
                at = held[line.symbol].get(date.fromisoformat(row["day"]))
                o, h, lo, c = (Decimal(row[k]) for k in ("open", "high", "low", "close"))
                if at is None or at != Bar(at.day, o, h, lo, c, int(row["volume"])):
                    return False
    except (
        KeyError,
        ValueError,
        ArithmeticError,
        OSError,
    ):  # an unknown line, a bad row or file: kept, named
        return False
    return True


def rolloff_rows(
    files: Iterable[Path], home: Path, lines: Iterable[Line]
) -> tuple[list[Path], list[Path]]:
    """Old research files with no byte twin, checked row by row against the store: a file whose
    every row the store holds is safe to roll; any other is kept. Nothing is deleted.
    -> (safe, kept)."""
    safe: list[Path] = []
    kept: list[Path] = []
    every = tuple(lines)
    for file in files:
        (safe if _held_rows(file, home, every) else kept).append(file)
    return safe, kept


Pull = Callable[[Line, str], Sequence[Timed] | Refused]  #: a source's bars of one line's span
Pulls = Sequence[tuple[Source, Pull]]  #: the sources in the order they are tried


def fill_cells(path: Path, lines: Iterable[Line], pulls: Pulls, now: datetime) -> list[str]:
    """Each intraday cell holding no bar (daily gaps have `gaps`) asked of the pulls in order,
    the broker first and the free archives behind it, the first answer written through the one
    writer under its own source; a cell holding a bar asks nothing. What was written, in words."""
    wrote = []
    for line in lines:
        for span in HOVER_SPANS:
            if span == "daily" or span in OFFERED.get(line.symbol, ()):
                continue
            if cell(path, line, span, now) != "holds no bar":
                continue
            for source, pull in pulls:
                got = pull(line, span)
                if isinstance(got, Refused) or not got:
                    continue
                with bars.writing(path, source) as opened:
                    if span == "5m":
                        opened.five(
                            line,
                            [Five(t.start, t.open, t.high, t.low, t.close, t.volume) for t in got],
                        )
                    else:
                        opened.timed(line, span, got)
                wrote.append(f"{line.symbol}/{span}: {source.value}")
                break
    return wrote


def monitor(
    path: Path,
    lines: Iterable[Line],
    broker: backfill.Ask,
    archived: backfill.Ask,
    now: datetime,
    pulls: Pulls = (),
) -> str:
    """Audit, backfill every gap, audit again: the one line saying green, or what stays red."""
    every, today = list(lines), now.date()
    fill_cells(path, every, pulls, now)
    asks: backfill.Asks = (
        *backfill.ordered(broker, archived),
        (Source.ROLLUP_5M, partial(bars.rolled_day, path)),
    )
    wrote, named = backfill.fill(path, gaps(path, every, today), asks, today)
    built = [rolled(path, line, today) for line in every]
    red = [why for line in every for why in audit(path, line, now)]
    red += [why for _, faults in built for why in faults]
    red += [why for line in every for why in thin(path, line, today)]
    red += [why for line in every for why in volumes(path, line, today)]
    red += [why for line in every for why in basis(path, line)]
    red += disk(path.parent)
    red += [stale] if (stale := archive.alert(path.parent, now)) else []
    score, within = covered(path, every, now)
    if not within:
        red.append(f"parked lines exceed {coverage.PARKED_CAP:.0%} of the lines")
    said = f"{len(wrote)} bars backfilled, {sum(n for n, _ in built)} rolled up, {score}"
    if not red:
        return f"quality: green, {len(every)} lines, {said}"
    return f"quality: RED, {said}; {'; '.join(red)}; unfilled {len(named)}"


def register(path: Path, lines: Iterable[Line]) -> tuple[str, list[str]]:
    """The register of sources: each line's newest daily bar and the source that gave it, and
    the lines whose newest bar came from a replacement (not the broker, the price of record)."""
    rows = [(line, bars.newest(path, line, "daily")) for line in lines]
    held = [(line.symbol, got[1]) for line, got in rows if got]
    replaced = [f"{name}: {src.value}" for name, src in held if src is not Source.IBKR]
    counts = {
        src.value: sum(s is src for _, s in held) for src in dict.fromkeys(s for _, s in held)
    }
    return ", ".join(f"{name} {n}" for name, n in sorted(counts.items())), replaced


def against_record(path: Path, line: Line, record: Bar) -> list[str]:
    """Red when the store's close for the broker's bar day differs from the broker's close (the
    price of record) by more than the sources' agreement (store.AGREE),
    or the store holds no bar for that day."""
    held = {bar.day: bar for bar in bars.daily(path, line)}.get(record.day)
    if held is None:
        return [f"{line.symbol}: no daily bar held for {record.day}, the broker has one"]
    if abs(held.close - record.close) <= record.close * AGREE:
        return []
    return [f"{line.symbol} {record.day}: held close {held.close}, broker's {record.close}"]


def check_records(path: Path, lines: Iterable[Line], ask: backfill.Ask, now: datetime) -> list[str]:
    """The daily check: each line's last ended session asked of the broker and judged by
    `against_record`; a refusal is said, never skipped. Empty when every line agrees."""
    red: list[str] = []
    for line in lines:
        day = _last_session(line, now)
        got = ask(line, day)
        if isinstance(got, Sequence) and got:
            red += against_record(path, line, got[-1])
        else:
            red.append(f"{line.symbol} {day}: the broker gave no bar to check against: {got}")
    return red


GOLDEN = ("SPY", "QQQ", "VUAG", "IITU")  #: always green, or the table says why (his 22 Nov)
OFFERED = {"VUAG": ("1m", "15m", "30m", "4h")}  #: spans a line's venue never supplies: not a gap
HOVER_SPANS = ("5m", "15m", "30m", "1h", "4h", "daily", "1wk", "1m")  #: every span, as stored
REMIND = timedelta(minutes=30)  #: while red, one reminder this often


def _last_session(line: Line, now: datetime) -> date:
    """The last session of the line's venue that had ended by now."""
    for back in range(10):
        day = now.date() - timedelta(back)
        if venues.sessions(line.venue, day, day) and venues.hours(line.venue, day).auction <= now:
            return day
    raise LookupError(f"{line.venue}: no session ended in the ten days to {now}")


def _held_on(path: Path, line: Line, span: str, day: date) -> set[datetime]:
    """When the line's bars of one short span start on a day, as held; none if never held."""
    since = datetime.combine(day, time(), UTC)
    try:
        got = bars.five if span == FIVE else partial(bars.timed, span=span)
        return {b.start for b in got(path, line, since=since, until=since + timedelta(1))}
    except (LookupError, FileNotFoundError):  # the store never held this span for the line
        return set()


def _outage(path: Path, line: Line, span: str, day: date) -> list[datetime]:
    """The moments of the venue's session `day` on the span's marks at which the line holds no
    bar and neither does any other line of its venue: a feed stopped for the whole venue, never
    one line's quiet spell. One line holding the span alone cannot tell the two apart: none."""
    length, hours = timedelta(seconds=SPANS[span].seconds), venues.hours(line.venue, day)
    anchor = EPOCH + timedelta(seconds=SPANS[span].anchor)
    first = anchor + (hours.open - anchor) // length * length
    due = {first + length * n for n in range((hours.close - first) // length + 1)}
    own = _held_on(path, line, span, day)
    gone, seen = {t for t in due if t < hours.close} - own, False
    if not own or not gone:
        return []
    for other in (o for o in LINES if o.venue == line.venue and o != line):
        theirs = _held_on(path, other, span, day)
        seen, gone = seen or bool(theirs), gone - theirs
        if not gone:
            return []
    return sorted(gone) if seen else []


def cell(path: Path, line: Line, span: str, now: datetime) -> str | None:
    """None when the line's newest bar of one span is of its venue's last ended session (a
    week's: of that week or the one before); else why: the span holds no bar, or how far behind."""
    name = FIVE if span == "5m" else span
    try:
        got = bars.newest(path, line, name)
    except LookupError:  # the store never held this span for the line: a gap, said in words
        got = None
    if got is None:
        return "holds no bar"
    due = _last_session(line, now)
    at = date.fromordinal(got[0]) if name == "daily" else (EPOCH + timedelta(seconds=got[0])).date()
    if name == "1wk":
        due -= timedelta(due.weekday() + 7)
    if at < due:
        return f"newest {at}, last session {due}"
    if name not in ("daily", "1wk") and (gone := _outage(path, line, name, due)):
        return f"{len(gone)} bars missing in its venue's feed, the first on {due}"
    if name == "daily" and (moved := bars.moved_off(path, line)):  # IBKR first (B3)
        return f"{len(moved)} days moved off IBKR, the first {moved[0]}"
    if name == "daily" and line.symbol in GOLDEN:  # a hole inside the history is red too
        hole = _missing(line, backfill._held(path, line), due + timedelta(1))
        return f"{len(hole)} sessions missing, the first {hole[0]}" if hole else None
    return None


def kind(why: str) -> str:
    """The kind of a red cell, for the escalation (a model fixes a kind already seen): a gap holds
    no bar, a hole misses sessions inside its history, a source a day served off IBKR's bar, else
    the cell is stale."""
    if why == "holds no bar":
        return "gap"
    return "hole" if "missing" in why else "source" if "moved off IBKR" in why else "stale"


def escalate(red_kind: str, seen: frozenset[str]) -> str:
    """Which model a red kind wakes, cheapest first: Opus for a kind never seen, Sonnet to fix a
    kind already seen. (Haiku reads the fault and names its kind, by `kind`, before this.)"""
    return "sonnet" if red_kind in seen else "opus"


def _cells(
    path: Path, lines: Iterable[Line], now: datetime, spans: Iterable[str] = HOVER_SPANS
) -> list[tuple[str, Line, str | None]]:
    """Every line x span the venue supplies, judged: (name, line, why not fresh or None)."""
    return [
        (f"{line.symbol}/{span}", line, cell(path, line, span, now))
        for line in lines
        for span in spans
        if span not in OFFERED.get(line.symbol, ())
    ]


def table(paths: dict[str, Path], lines: Iterable[Line], now: datetime) -> str:
    """The hourly table: per database and span, the share fresh, the faults and the gaps, its golden
    lines (green, or each red cell with why), then its register of sources (each newest daily
    bar's source, lines on a replacement)."""
    held, rows = list(lines), []
    for db, path in paths.items():
        for span in HOVER_SPANS:
            why = [w for _, _, w in _cells(path, held, now, (span,))]
            gap = sum(w == "holds no bar" for w in why)
            bad = sum(w is not None for w in why)
            fresh = 100 * (len(why) - bad) // max(len(why), 1)
            rows.append(f"{db}/{span}: {fresh}% fresh, {bad - gap} faults, {gap} gaps")
        red = [f"{n} ({w})" for n, ln, w in _cells(path, held, now) if w and ln.symbol in GOLDEN]
        rows.append(f"{db} golden: {', '.join(red) or 'green'}")
        counts, replaced = register(path, held)
        rows.append(f"{db} sources: {counts}; replaced: {', '.join(replaced) or 'none'}")
    return "\n".join(rows)


def databases(home: Path) -> dict[str, Path]:
    """The two databases the monitor watches, by name: the long one and the short one."""
    return {name: home / name for name in (bars.HISTORY, keeper.HOT)}


def hover(paths: dict[str, Path], lines: Iterable[Line], now: datetime) -> tuple[str, bool]:
    """Every database x line x span judged against the venue's last ended session: the one line
    saying the share fresh, the faults (held but behind), the gaps (no bar) and the worst cell, and
    whether it is green: every golden line fresh at every span its venue supplies."""
    held = list(lines)
    cells = [
        (f"{db}/{name}", line, why)
        for db, path in paths.items()
        for name, line, why in _cells(path, held, now)
    ]
    behind = sorted(
        {n.split("/")[0] + "/" + n.split("/")[-1] for n, _, w in cells if w and kind(w) != "gap"}
    )
    bad = [(name, line, why) for name, line, why in cells if why]
    gap = sum(why == "holds no bar" for _, _, why in bad)
    first = next((b for b in bad if b[1].symbol in GOLDEN), bad[0]) if bad else None
    worst = (
        f"{first[0]} ({kind(first[2])}): {first[2]}" if first else "none"
    )  # a golden line's fault leads
    share = 100 * (len(cells) - len(bad)) // max(len(cells), 1)
    said = f"data quality: {share}% fresh, {len(bad) - gap} faults, {gap} gaps, worst {worst}"
    said += f"; stale spans {', '.join(behind)}" if behind else ""
    return said, not any(line.symbol in GOLDEN for _, line, _ in bad)


def alarm(
    since: datetime | None, sent: datetime | None, green: bool, why: str, now: datetime
) -> tuple[datetime | None, datetime | None, str | None]:
    """The alarm that tells only of change, from when red began and when it last spoke: the first
    red names why, a reminder follows every REMIND while red, the first green says how long it was
    red and falls silent. It returns the new (since, sent) and the message to send, if any."""
    if green:
        told = (
            None
            if since is None
            else f"back to green, red for {(now - since) // timedelta(minutes=1)} minutes"
        )
        return None, None, told
    if since is None or sent is None:
        return now, now, f"data quality RED: {why}"
    if now - sent >= REMIND:
        return since, now, f"data quality still RED: {why}"
    return since, sent, None


def announce(said: str, told: str | None) -> str:
    """What `hover` prints: the freshness line, then `SEND: <message>` when the alarm speaks, the
    line the runner's job posts to Telegram."""
    return f"{said}\n" + (f"SEND: {told}\n" if told else "")


def watch(state: Path, said: str, green: bool, now: datetime) -> str | None:
    """One check of the alarm with its state (since, sent) kept in a file between runs, replaced
    whole; returns the message to send, if any."""
    held = json.loads(state.read_text("utf-8")) if state.exists() else {}  # bounded: two timestamps
    since, sent = (
        datetime.fromisoformat(held[k]) if held.get(k) else None for k in ("since", "sent")
    )
    since, sent, told = alarm(since, sent, green, said, now)
    temp = state.with_suffix(".tmp")
    temp.write_text(
        json.dumps({"since": since and since.isoformat(), "sent": sent and sent.isoformat()}),
        "utf-8",
    )
    temp.replace(state)
    return told


if __name__ == "__main__":
    home, now = Path(os.environ["KESTREL2_DATA"]), datetime.now(UTC)
    if sys.argv[1:] == ["table"]:
        sys.stdout.write(table(databases(home), LINES, now) + "\n")
        sys.exit(0)
    if sys.argv[1:] == ["hover"]:
        said, ok = hover(databases(home), LINES, now)
        told = watch(home / "hover_alarm.json", said, ok, now)
        sys.stdout.write(announce(said, told))
        sys.exit(0 if ok else 1)
    if sys.argv[1:] == ["register"]:
        counts, replaced = register(home / keeper.HOT, LINES)
        sys.stdout.write(f"sources: {counts}; replaced: {'; '.join(replaced) or 'none'}\n")
        sys.exit(0)
    if sys.argv[1:] == ["record"]:
        red = check_records(home / keeper.HOT, LINES, backfill._broker(home, now), now)
        sys.stdout.write("record: " + ("RED: " + "; ".join(red) if red else "green") + "\n")
        sys.exit(1 if red else 0)
    if sys.argv[1:2] == ["rolloff"]:
        gone, left = rolloff(Path(sys.argv[2]), home)
        sys.stdout.write(f"rolloff: {len(gone)} duplicates deleted; for his yes: {left}\n")
        sys.exit(0)
    said = monitor(home / keeper.HOT, LINES, backfill._broker(home, now), backfill._archive, now)
    sys.stdout.write(f"{said}\n")
    sys.exit(0 if " green," in said else 1)
