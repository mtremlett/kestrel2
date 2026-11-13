"""listing - EACH LINE AS THE PAPER BROKER KNOWS IT: the broker's own number for it, the
exchange it lists it on, the unit it prices it in and its price steps. All of it is asked of
the broker, through the one door (desk/paper.py), and none of it is written down here: the
broker changes its steps, and it prices some London lines in pence and others in pounds.

Only questions are sent. A line the broker does not list exactly once as the desk's own
(its name, a share or fund, its currency, an exchange of its venue) is named Unlisted with
the reason, and the other lines carry on; an answer the desk cannot read or cannot trust
stops the reading."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from typing import BinaryIO

from desk import paper
from desk.lines import Line

ASK_LINE, ASK_STEPS = 9, 91  #: what this module sends: two questions, neither places an order
LISTED, LISTED_END, STEPS = "10", "52", "93"  #: the answers, by the gateway's own numbers
UNKNOWN = "200"  #: the gateway's notice that it lists nothing under a name
ROUTE = "SMART"  #: where the desk's orders will go: the broker's own router
#: The broker's names for the exchanges of each of the desk's venues, each seen from the
#: gateway on one of the desk's lines. A line listed on any other is unlisted until its
#: exchange is named here.
EXCHANGES = {"LSE": frozenset({"LSEETF"}), "US": frozenset({"NASDAQ", "ARCA"})}
#: What the broker may multiply a currency's prices by: pounds alone are also priced in pence.
UNITS = {"GBP": (1, 100), "USD": (1,)}


@dataclass(frozen=True)
class Listing:
    """A line as the broker lists it."""

    line: Line
    contract: str  #: the broker's own lasting number for the line
    exchange: str  #: the exchange the broker lists it on
    magnifier: int  #: the broker's prices are the line's currency times this: 100 is pence
    #: From each price up, the step prices move in there; both in the line's currency.
    steps: tuple[tuple[Decimal, Decimal], ...]

    def __post_init__(self) -> None:
        """A number for the line, a unit its currency is priced in, and steps that are
        steps: from nothing up, each band above the last, each starting on its own step."""
        lows = [low for low, _ in self.steps]
        if not (
            (self.contract.isdigit() and int(self.contract) > 0)
            and self.magnifier in UNITS[self.line.currency]
            and all(
                low.is_finite() and step.is_finite() and step > 0 and low % step == 0
                for low, step in self.steps
            )
            and lows[:1] == [Decimal(0)]
            and lows == sorted(set(lows))
        ):
            raise ValueError(
                f"{self.line.symbol}: a listing the desk cannot trust: the broker's number "
                f"{self.contract!r}, prices {self.magnifier} times the currency, steps {self.steps}"
            )

    def floor(self, price: Decimal) -> Decimal:
        """The price the broker takes at or below this one: on its step for a price that
        high, and in its own unit. price is in the line's currency."""
        steps = [step for low, step in self.steps if low <= price] if price.is_finite() else []
        down = price // steps[-1] * steps[-1] if steps else Decimal(0)
        if down <= 0:
            raise ValueError(f"{self.line.symbol}: the broker has no price at or below {price}")
        return down * self.magnifier


@dataclass(frozen=True)
class Unlisted:
    """A line the broker cannot be asked to trade, and why."""

    line: Line
    reason: str


def _contracts(wire: BinaryIO, send: paper.Send, number: str, line: Line) -> list[list[str]] | str:
    """Every contract the broker lists under the line's name and currency, as it sent them;
    or its own words when it says it lists none."""
    asked = (number, 0, line.symbol, "STK", "", "0.0", "", "", ROUTE, "", line.currency)
    send(paper.message(ASK_LINE, 8, *asked, "", "", 0, "", "", ""))
    found: list[list[str]] = []
    while True:
        fields = paper.receive(wire)
        if fields[:2] == [LISTED, number]:
            found.append(fields)
        elif fields[0] == LISTED_END and fields[2:] == [number]:
            return found
        elif fields[0] == paper.NEWS and fields[2:4] == [number, UNKNOWN] and len(fields) > 4:
            return fields[4]
        else:
            paper.other(fields)


def _steps(wire: BinaryIO, send: paper.Send, rule: str) -> tuple[tuple[Decimal, Decimal], ...]:
    """One of the broker's rules of price steps, asked by its number."""
    send(paper.message(ASK_STEPS, rule))
    fields = paper.receive(wire)
    while fields[:2] != [STEPS, rule]:
        paper.other(fields)
        fields = paper.receive(wire)
    if len(fields) < 3 or len(fields) != 3 + 2 * int(fields[2]):
        raise ValueError(f"price steps of a shape the desk does not read: {fields}")
    prices = [Decimal(value) for value in fields[3:]]
    return tuple(zip(prices[::2], prices[1::2], strict=True))


def _rule(fields: list[str]) -> str:
    """The number of the rule of price steps where the desk's orders will go, from a listing
    whose shape is the one the desk reads: the rules sit six from the end, one for each of
    the line's exchanges."""
    if len(fields) > 30 and len(fields) == 40 + 2 * int(fields[30]):
        exchanges, rules = fields[16].split(","), fields[-6].split(",")
        if len(exchanges) == len(rules) and exchanges.count(ROUTE) == 1:
            rule = rules[exchanges.index(ROUTE)]
            if rule.isdigit():
                return rule
    raise ValueError(f"a listing of a shape the desk does not read: {fields}")


def _listing(wire: BinaryIO, send: paper.Send, number: str, line: Line) -> Listing | Unlisted:
    found = _contracts(wire, send, number, line)
    if isinstance(found, str):
        return Unlisted(line, f"the broker says: {found}")
    if len(found) != 1:
        return Unlisted(line, f"the broker lists {len(found)} contracts under the name")
    fields, rule = found[0], _rule(found[0])
    symbol, kind, currency, contract, magnifier, exchange = (
        fields[n] for n in (2, 3, 8, 12, 17, 20)
    )
    if (symbol, kind, currency) != (line.symbol, "STK", line.currency) or (
        exchange not in EXCHANGES[line.venue]
    ):
        return Unlisted(
            line, f"the broker's {symbol} ({kind}, in {currency}, on {exchange}) is another thing"
        )
    return Listing(line, contract, exchange, int(magnifier), _steps(wire, send, rule))


def converse(
    wire: BinaryIO, send: paper.Send, lines: Iterable[Line]
) -> dict[str, Listing | Unlisted]:
    """Ask over an open connection how the broker lists each line, one line at a time: the
    line, then the price steps where its orders will go."""
    paper.start(wire, send)
    return {
        line.symbol: _listing(wire, send, str(number), line) for number, line in enumerate(lines)
    }


def read(lines: Iterable[Line]) -> dict[str, Listing | Unlisted]:
    """Each line as the paper broker lists it now, by its symbol."""
    return paper.dial(lambda wire, send: converse(wire, send, lines))
