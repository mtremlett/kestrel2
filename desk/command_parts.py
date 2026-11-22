"""command_parts - THE DESK'S POUND PER DOLLAR, moved out of desk/command.py to keep it under its
cap: the pound read from the one door for prices (the keeper's database, `keeper.pound`), the
day's rate kept and told in `pound.log`; and the account a rehearsal found (Found)."""

from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

from desk import book, keeper
from desk.keeper import Broker
from desk.lines import Line
from desk.paper import Account, Apart

#: The pound in dollars; no pound closes outside these (keeper.pound_closes reads the same).
POUND, DOLLARS = Line("GBPUSD=X", "US", "USD", 1), (Decimal(1), Decimal(2))
POUND_LOG = "pound.log"  #: where each day's rate and its source are told


def rates(root: Path, day: date, broker: Broker | None = None) -> dict[str, Decimal]:  # noqa: ARG001 - command.py still passes it
    """A DAY'S POUNDS PER UNIT OF EACH CURRENCY: the dollar's as the desk's record at root
    keeps it for the day, else the pound as the database beside it holds it (`keeper.pound`,
    never the broker nor the archive asked here), told in `pound.log`; none fresh, ValueError."""
    kept: Decimal | None = None
    with suppress(ValueError):  # no rate kept for the day
        kept = book.rate(root, "USD", day)
    if kept is None:
        try:
            kept = keeper.pound(root.parent, day)
        except keeper.Stale as why:  # the desk's callers name a ValueError, as for any bad rate
            raise ValueError(f"{day}: no pound in dollars to trust: {why}") from why
        root.mkdir(parents=True, exist_ok=True)
        with (root / POUND_LOG).open("a", encoding="utf-8") as log:
            print(f"{day}: the database's pound, {kept} pounds a dollar", file=log)
    return {"GBP": Decimal(1), "USD": kept}


@dataclass(frozen=True)
class Found(Apart):
    """THE ACCOUNT AS THE REHEARSAL FOUND IT: its held lines and working orders are the
    account's, so the rehearsal's steps do not see them and cannot touch them (a Door's apart)."""

    orders: frozenset[str] = frozenset()  #: the broker's ids of the orders found working

    def without(self, account: Account) -> Account:
        """The account less what was found: what is left is the rehearsal's own."""
        gone = [o for o in account.orders if o.broker_id not in self.orders]
        return Account(
            tuple(h for h in account.holdings if h.name not in self.holdings), tuple(gone)
        )

    def changes(self, found: Account, now: Account) -> list[str]:
        """How the account now differs from found: the same holdings, the same working orders
        by id and level, and nothing else of the rehearsal's working. Each, named."""
        kept = {h.name: h.shares for h in now.holdings if h.shares}
        words = [
            f"{h.name}: {h.shares} shares held, now {kept.get(h.name, 0)}"
            for h in found.holdings
            if h.shares and kept.pop(h.name, 0) != h.shares
        ]
        words += [f"{name}: {shares} shares held, found none" for name, shares in kept.items()]
        listed = {o.broker_id: o for o in now.orders}
        for old in found.orders:
            if (new := listed.pop(old.broker_id, None)) is None:
                words.append(f"a held line's order {old.ref} ({old.symbol}) was cancelled")
            elif new.level != old.level:
                words.append(f"a held line's order {old.ref} ({old.symbol}) was moved")
        words += [f"its own order {o.ref} ({o.symbol}) is still working" for o in listed.values()]
        return words
