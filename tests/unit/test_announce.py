"""The one line to the operator on each merge: what it says, and that it refuses rather
than guesses or stays quiet."""

from __future__ import annotations

import io
import json
import urllib.error
import urllib.request
from email.message import Message
from pathlib import Path
from typing import Any

import pytest

import announce
from check import PUBLISHED, ROOT

PLAN = (ROOT / "docs" / "PLAN.md").read_text(encoding="utf-8")


def test_the_line_word_for_word() -> None:
    plan = "**Current objective:** daily bars for\nthe twenty lines.\n\nScenes passing: **1 of 7**."
    assert announce.line(plan, "price store", 6) == (
        "kestrel2: price store merged (#6). Scenes passing 1 of 7. "
        "Next: daily bars for the twenty lines."
    )


def test_the_line_reads_the_plan_as_it_is_published() -> None:
    scenes = PUBLISHED.search(PLAN)
    assert scenes is not None
    text = announce.line(PLAN, "price store", 6)
    assert text.startswith(
        f"kestrel2: price store merged (#6). Scenes passing {scenes[1]} of {scenes[2]}. Next: "
    )
    assert "\n" not in text and "**" not in text and text.endswith(".")


def test_a_plan_that_stops_saying_it_fails_instead_of_sending_half_a_line() -> None:
    for said in ("Scenes passing:", "**Current objective:**"):
        with pytest.raises(ValueError, match="docs/PLAN.md"):
            announce.line(PLAN.replace(said, "Something else:"), "price store", 6)


def test_a_missing_secret_fails_loudly_and_names_it() -> None:
    with pytest.raises(SystemExit, match="TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID"):
        announce.main({})
    with pytest.raises(SystemExit, match="missing TELEGRAM_CHAT_ID"):
        announce.main({"TELEGRAM_BOT_TOKEN": "a key", "TELEGRAM_CHAT_ID": "  "})


def test_only_the_pull_request_that_made_the_commit_is_announced() -> None:
    pulls = [
        {"merge_commit_sha": "aaa", "title": "an older change", "number": 5},
        {"merge_commit_sha": "bbb", "title": "price store", "number": 6},
    ]
    assert announce.merged(pulls, "bbb") == ("price store", 6)
    with pytest.raises(ValueError, match="ccc on main was not made by merging"):
        announce.merged(pulls, "ccc")


KEY = "123456:a-fake_key"
PULLS = [{"merge_commit_sha": "bbb", "title": "price store", "number": 6}]


def _env(record: Path, key: str = KEY) -> dict[str, str]:
    telegram = {"TELEGRAM_BOT_TOKEN": key, "TELEGRAM_CHAT_ID": "42"}
    github = {"GITHUB_TOKEN": "t", "GITHUB_REPOSITORY": "o/r", "GITHUB_SHA": "bbb"}
    return telegram | github | {"GITHUB_STEP_SUMMARY": str(record)}


def _replies(monkeypatch: pytest.MonkeyPatch, *replies: Any) -> list[str]:
    """The network, faked at its one edge. Returns the hosts called, in order."""
    queue, called = list(replies), []

    def urlopen(request: urllib.request.Request, timeout: float) -> io.BytesIO:
        assert timeout > 0, "a call with no timeout can hang the job until GitHub kills it"
        called.append(request.host)
        reply = queue.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return io.BytesIO(json.dumps(reply).encode())

    monkeypatch.setattr(urllib.request, "urlopen", urlopen)
    return called


def test_a_delivered_line_is_recorded_with_telegrams_message_number(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    called = _replies(monkeypatch, PULLS, {"ok": True, "result": {"message_id": 9}})
    announce.main(_env(tmp_path / "summary.md"))
    assert called == ["api.github.com", "api.telegram.org"]
    record = (tmp_path / "summary.md").read_text(encoding="utf-8")
    assert "Telegram message 9 sent" in record and "price store merged (#6)" in record


def test_an_undelivered_line_fails_and_never_prints_the_key(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    said = io.BytesIO(b'{"ok": false, "description": "chat not found"}')
    url = f"https://api.telegram.org/bot{KEY}/sendMessage"
    refused = urllib.error.HTTPError(url, 400, "Bad Request", Message(), said)
    for refusal in ({"ok": False, "description": "chat not found"}, refused):
        _replies(monkeypatch, PULLS, refusal)
        with pytest.raises(SystemExit, match="chat not found") as stopped:
            announce.main(_env(tmp_path / "summary.md"))
        assert KEY not in str(stopped.value)
    assert not (tmp_path / "summary.md").exists()


def test_a_key_that_is_not_a_bot_key_is_refused_by_name_not_shown() -> None:
    with pytest.raises(SystemExit, match="TELEGRAM_BOT_TOKEN is not a bot key") as stopped:
        announce.main(_env(Path("unused"), key="123456:a bad paste"))
    assert "bad paste" not in str(stopped.value)
