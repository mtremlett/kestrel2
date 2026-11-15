"""simcitycmd - SIMCITY'S COMMAND LINE, as the runner asks for it (`python -m desk.simcity`).

    python -m desk.simcity          a night of the first TWENTY worlds
    python -m desk.simcity --full   a night of all the hundred (the weekends')
    python -m desk.simcity --soak   the NEXT unused block of a hundred fresh seeds, logged
                                    in KESTREL2_DATA/simcity/seeds.jsonl before it starts

It lives the saved lines of the desk's price store, under the folder the environment names
(KESTREL2_DATA), with the desk's own capital and the pound's rate of the day, and adds the
night's one record to the desk's folder. Its answer is the night in words, one message, and
the code is 0 for a green night, 1 for a red one: the night is kept either way."""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path

from desk import command, simcity, store
from desk.lines import LINES
from desk.orders import Settings

USAGE = "python -m desk.simcity [--full | --soak]"
SOAKED = Path("simcity") / "seeds.jsonl"  #: under KESTREL2_DATA: one line per block lived
FIRST, BLOCK = 100, 100  #: the first seed a soak may use (0-99 are the nights'), and a block
QUICK = range(20)  #: the weekdays' night: a fifth of the worlds


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
    saved = {line: store.read(root / command.STORE, line.symbol) for line in LINES}
    room = Settings(command.CAPITAL)
    worlds = soak(Path(env["KESTREL2_DATA"]), now) if argv == ["--soak"] else QUICK
    worlds = simcity.WORLDS if argv == ["--full"] else worlds
    night = simcity.run(root, saved, room, command.rates(root, now.date()), now, worlds)
    block = f" Soak: seeds {worlds[0]}-{worlds[-1]}." if argv == ["--soak"] else ""
    print(night.words() + block)  # noqa: T201 - the command's answer to whoever asked
    return int(not night.green)
