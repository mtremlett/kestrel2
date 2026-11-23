"""command_parts - THE DESK'S POUND PER DOLLAR, moved out of desk/command.py to keep it under its
cap: the pound's last close in dollars as the price store holds it (the one door, keeper.pound);
and the account a rehearsal found (Found)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

from desk import keeper
from desk.keeper import Broker
from desk.lines import POUND as POUND
from desk.paper import Account, Apart

POUND_LOG = "pound.log"  #: the log the preflight reads


def rates(home: Path, day: date, broker: Broker | None = None) -> dict[str, Decimal]:  # noqa: ARG001 - command._desk still passes it
    """A DAY'S POUNDS PER UNIT OF EACH CURRENCY: the dollar's from the one door for prices, the
    keeper's store in home (market_history.db, market_live.db), never the IBKR, the archive or a
    file asked first; `broker` is no longer asked, and a pound not held fresh is a ValueError (the
    preflight names it). Home is named, never guessed from the desk's records: a rehearsal's
    records sit deeper than the store (Sun 22 Nov 18:00 NO-GO)."""
    try:
        return {"GBP": Decimal(1), "USD": keeper.pound(home, day)}
    except keeper.Stale as e:
        raise ValueError(str(e)) from e


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
