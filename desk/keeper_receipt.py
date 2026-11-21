"""keeper_receipt - THE KEEPER'S DATED RECEIPT: a file a day in `receipts`, a line for each call
that did anything: what was done, what was missed and which newest bars ARRIVED (DQ-10, DQ-12).

A bar arrived at the first call that found it as a line's newest bar of a span, and the receipt
says its span, moment and source (as the store holds them) beside the call's time. What the last
call saw is kept in `newest.json`, swapped in whole AFTER the receipt line is appended: a keeper
killed between the two says the arrivals again at its restart, never not at all. A receipt line
torn by a kill is ended before the next is written."""

from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from desk import bars
from desk.lines import Line

RECEIPTS = "receipts"
SEEN = "newest.json"  #: in `receipts`: each line's newest bar of each span, as the last call saw


def _seen(folder: Path) -> dict[str, str]:
    """The newest bars the last call saw, by line and span; none before the first call."""
    return json.loads((folder / SEEN).read_text("utf-8")) if (folder / SEEN).is_file() else {}


def newest(hot: Path, lines: Sequence[Line]) -> dict[str, str]:
    """Each line's newest bar of each span: its moment and source, by "VENUE:SYMBOL span"."""
    found = {}
    for line in lines:
        for span in (bars.DAILY, bars.FIVE):
            try:
                got = bars.newest(hot, line, span)
            except (LookupError, FileNotFoundError):  # never held, or no round has landed
                continue
            if got:
                found[f"{line.venue}:{line.symbol} {span}"] = f"{got[0]} {got[1].value}"
    return found


def write(
    home: Path, now: datetime, done: list[str], missed: list[str], held: dict[str, str]
) -> dict[str, str]:
    """The call's receipt line, with the bars of `held` that are new since the last call; given
    back: those arrivals."""
    (folder := home / RECEIPTS).mkdir(exist_ok=True)
    arrived = {name: said for name, said in held.items() if _seen(folder).get(name) != said}
    line = json.dumps({"at": now.isoformat(), "done": done, "missed": missed, "arrived": arrived})
    path = folder / f"{now.date()}.jsonl"
    torn = path.is_file() and not path.read_bytes().endswith(b"\n")
    with path.open("a", encoding="utf-8", newline="\n") as out:
        out.write(("\n" if torn else "") + line + "\n")
    (part := folder / f"{SEEN}.part").write_text(json.dumps(held), encoding="utf-8")
    part.replace(folder / SEEN)
    return arrived
