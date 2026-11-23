"""simcity_fills - THE TRADE-FAITHFULNESS REPLAY (R-RUNNER-409). Each real paper buy is decided
again from the bars saved before its day, by the desk's own code (strategy.today, orders.size,
orders.gate), and must come out the same: the signal, the size, the stop, and no refusal, the
correlation cap among them (MSTR and IB1T move together). A difference names the fill and the
field. `python -m desk.simcity_fills` replays the desk's own ledger; the code is 1 on one."""

from __future__ import annotations

import os
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from desk import book, command, keeper, orders, strategy
from desk.broker import Fill
from desk.lines import LINES, Line
from desk.orders import Refused, Settings
from desk.store import Bar
from desk.strategy import Action


@dataclass(frozen=True)
class Mismatch:
    """One field of one fill the replay decides otherwise."""

    fill: str  #: the fill's execution id
    field: str  #: signal, size, stop, refusal or correlation
    recorded: str
    replayed: str

    def words(self) -> str:
        """The mismatch as one line."""
        return f"fill {self.fill}: {self.field} recorded {self.recorded}, replayed {self.replayed}"


def replay(
    archive: Mapping[Line, Sequence[Bar]],
    fills: Sequence[Fill],
    stops: Mapping[str, Decimal],
    room: Settings,
    rates: Mapping[str, Decimal],
) -> tuple[Mismatch, ...]:
    """Every rule buy in fills (the ledger's order; stops are its recorded levels, "<buy>-stop"),
    decided again from the bars before its day with the book as the fills before it left it."""
    found, held, holders = list[Mismatch](), dict[str, int](), dict[str, str]()
    for f in fills:
        name = orders.strategy_of(f.order_id)
        if f.quantity > 0 and name != "stranger":
            before = {x: [b for b in bars if b.day < f.day] for x, bars in archive.items()}
            found += _one(f, name, before, stops, held, holders, room, rates)
            holders.setdefault(f.symbol, name)
        held = {
            s: n for s, n in {**held, f.symbol: held.get(f.symbol, 0) + f.quantity}.items() if n
        }
    return tuple(found)


def _one(
    f: Fill,
    name: str,
    before: Mapping[Line, Sequence[Bar]],
    stops: Mapping[str, Decimal],
    held: Mapping[str, int],
    holders: Mapping[str, str],
    room: Settings,
    rates: Mapping[str, Decimal],
) -> list[Mismatch]:
    """One buy decided again, the first field that differs told."""

    def differs(field: str, recorded: object, replayed: object) -> list[Mismatch]:
        return [Mismatch(f.execution_id, field, str(recorded), str(replayed))]

    line = next(x for x in before if x.symbol == f.symbol)
    now = {x.symbol: bars for x, bars in before.items() if x.symbol == f.symbol}
    decision = next(
        d
        for d in strategy.today(now, {s: h for s, h in holders.items() if s in held and s in now})
        if d.strategy == name
    )
    if decision.action is not Action.BUY:
        return differs("signal", Action.BUY.name, decision.action.name)
    price, fx = before[line][-1].close, rates[line.currency]
    try:
        order = orders.size(decision, line, price, fx, room, held)
        orders.gate(order, room, held, moves=orders.moves(set(held), before, f.symbol))
    except Refused as refused:
        return differs(
            "correlation" if "above the cap" in str(refused) else "refusal", "bought", refused
        )
    if order.quantity != f.quantity:
        return differs("size", f.quantity, order.quantity)
    level = stops.get(f"{f.order_id}-stop")
    if level is not None and level != (due := orders.stop_under(line, f.price)):
        return differs("stop", level, due)
    return []


def main(env: Mapping[str, str] = os.environ) -> int:
    """THE COMMAND: the desk's ledger replayed from the saved store; 1 if any fill differs."""
    now, data = datetime.now(UTC), Path(env["KESTREL2_DATA"])
    root = data / command.ROOT
    saved, _parked = keeper.saved(data, now.date(), LINES)
    found = replay(
        saved,
        book.fills(root),
        book.levels(root),
        Settings(command.CAPITAL),
        command.rates(data, now.date()),
    )
    print(*(m.words() for m in found) or ("every fill replays the same",), sep="\n")  # noqa: T201 - the answer
    return int(bool(found))


if __name__ == "__main__":
    sys.exit(main())
