"""Contract of desk/t212: read-only by construction, keys from the environment only, answers
read once into typed values, a refusal told without a key."""

from __future__ import annotations

import inspect
import json
from base64 import b64decode
from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from desk import t212
from desk.t212 import Client, Refused, Side

ENV = {"TRADING212_DEMO_API_KEY": "k-demo", "TRADING212_DEMO_API_SECRET": "s-demo"}
READS = {"cash", "holdings", "fills"}  #: the client's whole public surface, held here
ANSWERS = {
    "/equity/account/cash": {"free": 90.5, "total": 100},
    "/equity/portfolio": [{"ticker": "VOD_EQ", "quantity": 3, "averagePrice": 71.25}],
    "/equity/history/orders?limit=50": {
        "items": [
            {
                "ticker": "VOD_EQ",
                "filledQuantity": 3,
                "fillPrice": 71.25,
                "status": "FILLED",
                "dateExecuted": "2026-11-13T09:30:00Z",
            }
        ],
        "nextPagePath": "/api/v0/equity/history/orders?limit=50&cursor=2",
    },
    "/equity/history/orders?limit=50&cursor=2": {"items": [], "nextPagePath": None},
}


class Wire:
    """A fake at the adapter boundary: answers from ANSWERS and keeps what was asked."""

    def __init__(self) -> None:
        self.asked: list[tuple[str, Mapping[str, str]]] = []

    def __call__(self, address: str, headers: Mapping[str, str]) -> bytes:
        self.asked.append((address, headers))
        return json.dumps(ANSWERS[address.removeprefix(Side.DEMO.value)]).encode()


def fixed(body: bytes) -> t212.Wire:
    """A fake wire that answers every message with the same body."""
    return lambda _address, _headers: body


def test_the_client_can_only_read_and_only_the_listed_messages() -> None:
    public = {n for n, _ in inspect.getmembers(Client, inspect.isfunction) if not n.startswith("_")}
    assert public == READS
    assert all(path.startswith("/equity/") for path in t212.MESSAGES)
    assert not any(w in path for path in t212.MESSAGES for w in ("order/", "cancel", "place"))
    wire = Wire()
    client = Client(Side.DEMO, ENV, wire)
    client.cash(), client.holdings(), client.fills()
    assert {a.removeprefix(Side.DEMO.value).split("?")[0] for a, _ in wire.asked} <= set(
        t212.MESSAGES
    )
    with pytest.raises(Refused, match="not one of the desk's messages"):
        client._get("/equity/orders/limit")


def test_answers_are_read_into_exact_typed_values() -> None:
    client = Client(Side.DEMO, ENV, Wire())
    assert client.cash() == t212.Cash(Decimal("90.5"), Decimal(100))
    assert client.holdings() == (t212.Holding("VOD_EQ", Decimal(3), Decimal("71.25")),)
    assert client.fills() == (
        t212.Fill(
            "VOD_EQ",
            Decimal(3),
            Decimal("71.25"),
            "FILLED",
            datetime(2026, 11, 13, 9, 30, tzinfo=UTC),
        ),
    )


def test_the_key_comes_from_the_environment_alone_and_never_appears_in_a_refusal() -> None:
    wire = Wire()
    Client(Side.DEMO, ENV, wire).cash()
    assert b64decode(wire.asked[0][1]["Authorization"].removeprefix("Basic ")) == b"k-demo:s-demo"
    with pytest.raises(
        Refused, match="TRADING212_LIVE_API_KEY, TRADING212_LIVE_API_SECRET not set"
    ):
        Client(Side.LIVE, ENV, wire)
    with pytest.raises(Refused) as caught:
        Client(Side.DEMO, ENV, fixed(b"[{")).cash()
    assert "k-demo" not in str(caught.value) and "s-demo" not in str(caught.value)


def test_an_answer_the_desk_cannot_read_is_refused() -> None:
    for body in (b'{"free": 1}', b'[{"ticker": "X"}]'):
        client = Client(Side.DEMO, ENV, fixed(body))
        with pytest.raises(Refused, match="cannot read"):
            client.cash() if body.startswith(b"{") else client.holdings()
