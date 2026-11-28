"""ladder_kept - THE LADDER'S RESULTS FILE, READ BY OFFSET: each cell's last whole line found by
seek, a line a stop cut short cut off, and the file compacted once its superseded lines outnumber
its live cells. Split out of `lab/ladder.py` (O79), which judges the cells; it never imports the
ladder."""

from __future__ import annotations

import json
import os
from collections.abc import Iterator
from pathlib import Path
from typing import cast

from lab import verdict


class Kept:
    """The results file read line by line into an index of offsets only: each cell's last whole
    line (its answer now) is found by seek, and `end` is where the last whole line ends, so a
    line a stop cut short is cut off. No row is held."""

    def __init__(self, results: Path) -> None:
        self.path = results
        self._read()

    def _read(self) -> None:
        self.at, self.end, self.lines = {}, 0, 0
        if not self.path.exists():
            return
        with self.path.open("rb") as file:
            for line in file:
                if not line.endswith(b"\n"):
                    break
                self.at[tuple(json.loads(line)["cell"])] = (self.end, len(line))
                self.end += len(line)
                self.lines += 1

    def compact(self) -> None:
        """When superseded lines outnumber live cells, the file is rewritten once with each cell's
        last line only: a temp file beside it, then replaced: a stop leaves it whole."""
        if self.lines - len(self.at) <= len(self.at):
            return
        fresh = self.path.with_suffix(".compact")
        with fresh.open("wb") as out:
            for offset, size in sorted(self.at.values()):
                with self.path.open("rb") as file:
                    file.seek(offset)
                    out.write(file.read(size))
            out.flush()
            os.fsync(out.fileno())
        fresh.replace(self.path)
        self._read()

    def get(self, key: tuple[str, ...]) -> verdict.Row | None:
        """The cell's last line, read back from the file, or None."""
        if key not in self.at:
            return None
        offset, size = self.at[key]
        with self.path.open("rb") as file:
            file.seek(offset)
            return cast(verdict.Row, json.loads(file.read(size)))

    def rows(self) -> Iterator[verdict.Row]:
        """Every cell's last line, one at a time."""
        return (cast(verdict.Row, self.get(key)) for key in self.at)
