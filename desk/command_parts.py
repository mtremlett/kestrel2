"""command_parts - THE DESK'S POUND PER DOLLAR, moved out of desk/command.py to keep it under its
cap: the pound's last close in dollars from IBKR first, the archive's where IBKR gives none, each
told in `pound.log`, the day's rate kept; and the account a rehearsal found (Found)."""

from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from http.client import HTTPException
from pathlib import Path

from desk import archive, book
from desk.keeper import Broker
from desk.lines import Line
from desk.paper import Account, Apart
from desk.running import DAY
from desk.store import Answer, Refused

#: The pound in dollars at the archive; no pound closes outside these; the oldest close trusted.
POUND, DOLLARS, FRESH = Line("GBPUSD=X", "US", "USD", 1), (Decimal(1), Decimal(2)), 4 * DAY
BAND, POUND_LOG = Decimal("0.02"), "pound.log"  #: IBKR and archive may differ by this; the log


def _close(answer: Answer, day: date) -> Decimal | str:
    """A source's last pound close before the day (its own bar still moves), or why none."""
    if isinstance(answer, Refused):
        return answer.reason
    last = [bar for bar in answer if bar.day < day][-1:]
    if last and day - last[0].day <= FRESH and DOLLARS[0] < last[0].close < DOLLARS[1]:
        return last[0].close
    return f"no pound in dollars to trust: {last}"


def _quote(day: date, broker: Broker | None) -> tuple[Decimal, str]:
    """THE POUND IN DOLLARS, IBKR first (R-RUNNER-282), the archive's where it gives none; the
    words name the source, a gap beyond BAND a FAULT; neither is an error."""
    ibkr = _close(broker([POUND], day)[POUND] if broker else Refused("not asked"), day)
    if not isinstance(ibkr, Decimal):  # the archive is then the only source, and may raise
        other = _close(archive.fetch(POUND, day), day)
        if not isinstance(other, Decimal):
            raise ValueError(f"{day}: no pound in dollars; IBKR: {ibkr}; archive: {other}")
        return other, f"IBKR gave none ({ibkr}); archive {other}"
    try:
        other = _close(archive.fetch(POUND, day), day)
    except (OSError, HTTPException, ValueError) as why:
        other = f"the archive was not reached: {why}"
    fault = isinstance(other, Decimal) and abs(other / ibkr - 1) > BAND
    return ibkr, f"IBKR {ibkr}" + f"; FAULT: the archive's {other} is not within {BAND}" * fault


def rates(root: Path, day: date, broker: Broker | None = None) -> dict[str, Decimal]:
    """A DAY'S POUNDS PER UNIT OF EACH CURRENCY: the dollar's as the desk's record at root
    keeps it for the day, else one over the pound's `_quote`, its source told in `pound.log`."""
    kept: Decimal | None = None
    with suppress(ValueError):  # no rate kept for the day
        kept = book.rate(root, "USD", day)
    if kept is None:
        close, told = _quote(day, broker)
        root.mkdir(parents=True, exist_ok=True)
        kept = (1 / close).quantize(Decimal("0.000001"))
        with (root / POUND_LOG).open("a", encoding="utf-8") as log:
            print(f"{day}: {told}", file=log)
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
