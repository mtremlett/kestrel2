"""simcitycmd - SIMCITY'S COMMAND LINE, as the runner asks for it (`python -m desk.simcity`).

    python -m desk.simcity          a night of the first TWENTY worlds
    python -m desk.simcity --full   a night of all the hundred (the weekends')
    python -m desk.simcity --soak   the NEXT unused block of a hundred fresh seeds, logged
                                    in KESTREL2_DATA/simcity/seeds.jsonl before it starts

It lives the saved lines of the desk's price store (the keeper's door), in the folder the
environment names (KESTREL2_DATA), with the desk's own capital and the pound's rate of the
day, and adds the night's one record to the desk's folder. Its answer is the night in
words, one message, and the code is 0 for a green night, 1 for a red
one: the night is kept either way.

THE DEEP RUN (--full, --soak) ends in three named lines more. STRESS: the saved history lived
once in its true order through the money path, and the yardstick's worst days told, each with
the book the broker's and no order left working. CALIBRATION: the rungs' pass rate on the
night's noise worlds, which is lab/ work the desk may not import: the line says it was not run.
LIFECYCLE: every order the stress replay sent, counted by where it ended; a stuck one is red."""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from itertools import pairwise
from pathlib import Path
from tempfile import TemporaryDirectory

from desk import command, day, keeper, simcity
from desk.broker import Pretend
from desk.lines import LINES, YARDSTICK, Line
from desk.orders import Settings
from desk.store import Bar

USAGE = "python -m desk.simcity [--full | --soak]"
SOAKED = Path("simcity") / "seeds.jsonl"  #: under KESTREL2_DATA: one line per block lived
FIRST, BLOCK = 100, 100  #: the first seed a soak may use (0-99 are the nights'), and a block
QUICK = range(20)  #: the weekdays' night: a fifth of the worlds
WORST = 5  #: the yardstick's worst days the stress pass tells
NO_CALIBRATION = (
    "Calibration: NOT RUN - the rungs' pass rate on noise worlds is lab/ work and the desk "
    "may not import lab/; the rungs lane owes it."
)


@dataclass(frozen=True)
class Lifecycle:
    """THE LIFECYCLE CENSUS: the orders a broker received, each counted once by where it ended."""

    filled: int
    part: int  #: filled in part, the reason given
    refused: int  #: none filled, and not working
    stuck: int  #: left working at the broker, unfilled

    def words(self) -> str:
        """The census as the deep run's last line."""
        total = self.filled + self.part + self.refused + self.stuck
        return (
            f"Lifecycle: {total} orders, {self.filled} filled, {self.part} part-filled, "
            f"{self.refused} refused, {self.stuck} stuck working."
        )


def lifecycle(pretend: Pretend) -> Lifecycle:
    """Every order id the broker received, by the end its own report tells."""
    stuck, ends = set(pretend.working()), {"filled": 0, "part": 0, "refused": 0, "stuck": 0}
    for order_id in dict.fromkeys(pretend.submitted()):
        report = pretend.report(order_id)
        if order_id in stuck:
            ends["stuck"] += 1
        elif report is None or not report.fills:
            ends["refused"] += 1
        else:
            ends["filled" if report.reason is None else "part"] += 1
    return Lifecycle(**ends)


def stress(
    archive: Mapping[Line, Sequence[Bar]], room: Settings, rates: Mapping[str, Decimal]
) -> tuple[str, Lifecycle]:
    """THE STRESS PASS: the saved lines lived once in their true order at the pretend broker,
    and on the yardstick's WORST days the book must be the broker's and no order left working.
    Its words name the days; red ones are the days that broke (or the desk's refusal)."""
    steady = archive[YARDSTICK]
    falls = sorted(pairwise(steady), key=lambda pair: pair[1].close / pair[0].close)[:WORST]
    worst, broke = {bar.day for _, bar in falls}, list[str]()
    pretend, began = Pretend(archive, {}), steady[0].day
    sessions = sorted({b.day for bars in archive.values() for b in bars if b.day > began})
    with TemporaryDirectory() as scratch:
        for on in sessions:
            pretend.open(on)
            saved = {
                x: [b for b in bars if b.day <= on]
                for x, bars in archive.items()
                if bars[0].day < on
            }
            try:
                record = day.run(Path(scratch), saved, pretend, room, on, rates)
            except ValueError as refusal:  #: the desk's own word that it cannot go on: told
                broke.append(f"{on}: the desk refused, saying: {refusal}")
                break
            if on in worst and (record.mismatches or pretend.working()):
                broke.append(f"{on}: the book was not the broker's or an order was left working")
    told = ", ".join(sorted(d.isoformat() for d in worst))
    verdict = f"BROKEN: {'; '.join(broke)}" if broke else "all kept"
    words = f"Stress: the {len(worst)} worst days ({told}) replayed in order: {verdict}."
    return words, lifecycle(pretend)


def soak(data: Path, now: datetime) -> range:
    """THE NEXT BLOCK: the seeds after the highest logged, logged before they are lived."""
    path, start = data / SOAKED, FIRST
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            block = json.loads(line)
            start = max(start, block["first"] + block["count"])
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {"first": start, "count": BLOCK, "date": now.date().isoformat()}
    with path.open("a", encoding="utf-8") as kept:
        kept.write(json.dumps(entry) + "\n")
    return range(start, start + BLOCK)


def main(
    argv: Sequence[str] = sys.argv[1:],
    env: Mapping[str, str] = os.environ,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> int:
    """THE COMMAND LINE (USAGE): the night's words printed, and 0 only if it is green."""
    if argv not in ([], ["--full"], ["--soak"]):
        raise SystemExit(USAGE)
    root, now = Path(env["KESTREL2_DATA"]) / command.ROOT, clock()
    if not root.is_absolute():
        raise SystemExit(f"KESTREL2_DATA names no whole path to a folder: {root.parent}")
    saved, _parked = keeper.saved(Path(env["KESTREL2_DATA"]), now.date(), LINES)
    room = Settings(command.CAPITAL)
    worlds = soak(Path(env["KESTREL2_DATA"]), now) if argv == ["--soak"] else QUICK
    worlds = simcity.WORLDS if argv == ["--full"] else worlds
    rates = command.rates(root, now.date())
    night = simcity.run(root, saved, room, rates, now, worlds)
    block = f" Soak: seeds {worlds[0]}-{worlds[-1]}." if argv == ["--soak"] else ""
    print(night.words() + block)  # noqa: T201 - the command's answer to whoever asked
    if argv == []:
        return int(not night.green)
    deep, census = stress(saved, room, rates)
    lines = (deep, NO_CALIBRATION, census.words())
    print(*lines, sep="\n")  # noqa: T201 - the deep run's last lines
    return int(not night.green or "BROKEN" in deep or census.stuck > 0)
