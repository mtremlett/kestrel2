"""t212 - THE ONE CLIENT FOR TRADING 212, READ-ONLY BY CONSTRUCTION (R-RUNNER-17). It reads
an account's cash, its holdings and its order history, and nothing else: the messages it
can send are the fixed list MESSAGES, every one a GET, and no order, change, cancel or write
exists in it. Two accounts: the DEMO one for paper trading and the LIVE one, whose fills the
desk only tracks. What it reads is shown beside the paper desk and is never fed to a
trading decision.

The key comes only from the environment it is given (TRADING212_<SIDE>_API_KEY and
_API_SECRET), once, on entry; it is never kept, logged or put in an error. A refused key is
one line naming the side and the answer's code, never a value. The wire is a function
handed in (`Wire`), so a test speaks to a fake and the real one is `fetch`."""

from __future__ import annotations

import json
from base64 import b64encode
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from functools import partial
from typing import Any, TypeVar
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

#: Every message this client can send, and the only ones: each a GET of a path.
MESSAGES = ("/equity/account/cash", "/equity/portfolio", "/equity/history/orders")
PAGES = 20  #: the most pages of history one reading follows
TIMEOUT = 30  #: seconds a message may take
Read = TypeVar("Read")
Wire = Callable[[str, Mapping[str, str]], bytes]  #: (address, headers) -> the answer's body


class Side(Enum):
    """Which account: its base address and the name of its keys in the environment."""

    DEMO = "https://demo.trading212.com/api/v0"
    LIVE = "https://live.trading212.com/api/v0"


class Refused(Exception):
    """Trading 212 refused, was unreachable, or answered what the desk does not understand."""


@dataclass(frozen=True)
class Cash:
    """An account's cash: free to use, and the account's total."""

    free: Decimal
    total: Decimal


@dataclass(frozen=True)
class Holding:
    """A position held: its ticker, quantity and average price paid."""

    ticker: str
    quantity: Decimal
    average: Decimal


@dataclass(frozen=True)
class Fill:
    """An order in the history: what was filled, at what price, and when."""

    ticker: str
    quantity: Decimal
    price: Decimal
    status: str
    when: datetime


def authorization(side: Side, env: Mapping[str, str]) -> str:
    """The Basic header for a side from its two environment variables, or a Refused naming
    which variable is missing (never a value)."""
    names = [f"TRADING212_{side.name}_API_{part}" for part in ("KEY", "SECRET")]
    missing = [name for name in names if not env.get(name)]
    if missing:
        raise Refused(f"Trading 212 {side.name}: {', '.join(missing)} not set")
    token = ":".join(env[name] for name in names)
    return "Basic " + b64encode(token.encode()).decode()


def fetch(address: str, headers: Mapping[str, str]) -> bytes:
    """The real wire: one GET. A refusal is a Refused naming the side's code, not the key."""
    try:
        request = Request(address, headers=dict(headers), method="GET")  # noqa: S310  # https, from Side
        with urlopen(request, timeout=TIMEOUT) as answer:  # noqa: S310  # the same request
            return bytes(answer.read())
    except HTTPError as error:
        raise Refused(f"Trading 212 answered {error.code} to {address.split('?')[0]}") from None
    except URLError as error:
        raise Refused(
            f"Trading 212 unreachable at {address.split('?')[0]}: {error.reason}"
        ) from None


class Client:
    """Read-only access to one account. Its public methods are `cash`, `holdings`, `fills`."""

    def __init__(self, side: Side, env: Mapping[str, str], wire: Wire = fetch) -> None:
        self._side, self._wire = side, wire
        self._headers = {"Authorization": authorization(side, env)}

    def _get(self, path: str) -> Any:
        if path.split("?")[0] not in MESSAGES:
            raise Refused(f"Trading 212: {path} is not one of the desk's messages")
        body = self._wire(self._side.value + path, self._headers)
        try:
            return json.loads(body)
        except ValueError:
            raise Refused(f"Trading 212 {self._side.name}: {path} answered no JSON") from None

    def cash(self) -> Cash:
        """The account's free and total cash."""
        answer = self._get(MESSAGES[0])
        return _read(
            MESSAGES[0], lambda: Cash(Decimal(str(answer["free"])), Decimal(str(answer["total"])))
        )

    def holdings(self) -> tuple[Holding, ...]:
        """Every position held."""
        answer = self._get(MESSAGES[1])
        return _read(
            MESSAGES[1],
            lambda: tuple(
                Holding(
                    row["ticker"], Decimal(str(row["quantity"])), Decimal(str(row["averagePrice"]))
                )
                for row in answer
            ),
        )

    def fills(self) -> tuple[Fill, ...]:
        """The order history, newest first, following its pages up to PAGES."""
        found: list[Fill] = []
        path: str | None = MESSAGES[2] + "?limit=50"
        for _ in range(PAGES):
            if not path:
                break
            answer = self._get(path)
            found.extend(_read(path, partial(_page, answer)))
            path = answer.get("nextPagePath")
            path = path.removeprefix("/api/v0") if path else None
        return tuple(found)


def _page(answer: Mapping[str, Any]) -> list[Fill]:
    return [_fill(row) for row in answer["items"]]


def _fill(row: Mapping[str, Any]) -> Fill:
    when = datetime.fromisoformat(row["dateExecuted"].replace("Z", "+00:00"))
    if when.tzinfo is None:
        raise ValueError("a fill dated in no time zone")
    return Fill(
        row["ticker"],
        Decimal(str(row["filledQuantity"])),
        Decimal(str(row["fillPrice"])),
        str(row["status"]),
        when,
    )


def _read(path: str, build: Callable[[], Read]) -> Read:
    try:
        return build()
    except (KeyError, TypeError, ValueError, ArithmeticError) as error:
        raise Refused(
            f"Trading 212: {path} answered what the desk cannot read ({error!r})"
        ) from None
