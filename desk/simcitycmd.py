"""simcitycmd - SIMCITY'S COMMAND LINE, as the runner asks for it (`python -m desk.simcity`).

    python -m desk.simcity          a night of the first TWENTY worlds
    python -m desk.simcity --full   a night of all the hundred (the weekends')

It lives the saved lines of the desk's price store, under the folder the environment names
(KESTREL2_DATA), with the desk's own capital and the pound's rate of the day, and adds the
night's one record to the desk's folder. Its answer is the night in words, one message, and
the code is 0 for a green night, 1 for a red one: the night is kept either way."""

from __future__ import annotations

import os
import sys
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path

from desk import command, simcity, store
from desk.lines import LINES
from desk.orders import Settings

USAGE = "python -m desk.simcity [--full]"
QUICK = range(20)  #: the weekdays' night: a fifth of the worlds


def main(
    argv: Sequence[str] = sys.argv[1:],
    env: Mapping[str, str] = os.environ,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> int:
    """THE COMMAND LINE (USAGE): the night's words printed, and 0 only if it is green."""
    if argv not in ([], ["--full"]):
        raise SystemExit(USAGE)
    root, now = Path(env["KESTREL2_DATA"]) / command.ROOT, clock()
    if not root.is_absolute():
        raise SystemExit(f"KESTREL2_DATA names no whole path to a folder: {root.parent}")
    saved = {line: store.read(root / command.STORE, line.symbol) for line in LINES}
    room = Settings(command.CAPITAL)
    worlds = simcity.WORLDS if argv else QUICK
    night = simcity.run(root, saved, room, command.rates(root, now.date()), now, worlds)
    print(night.words())  # noqa: T201 - the command's answer to whoever asked
    return int(not night.green)
