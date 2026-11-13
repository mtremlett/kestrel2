"""The one line to the operator on each merge: what it says, and that it refuses rather
than guesses or stays quiet."""

from __future__ import annotations

import base64
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


def _plan(*phases: str, scenes: str = "3 of 7") -> str:
    """A plan in the published shape: the scenes count, then one checklist per phase."""
    return "\n\n".join([f"Scenes passing: **{scenes}**.", *phases, "## Rules\n\n- [ ] x\n"])


PHASE_1 = "## Phase 1 — data\n\n- [x] bars\n- [x] **Scene 1 passes**"
#: A step's wrapped line and a box indented under it are part of that step, not steps.
OPEN = "\n".join(
    [
        "## Phase 2 — money\n",
        "- [x] template",
        "- [ ] sizing",
        "      (wrapped)",
        "  - [ ] a detail",
        "- [ ] broker",
    ]
)
TICKED = OPEN.replace("- [ ] sizing", "- [x] sizing")
ALL_DONE = TICKED.replace("- [ ] broker", "- [x] broker")


def test_a_ticked_step_is_named_by_its_phase_and_count_word_for_word() -> None:
    before, after = _plan(PHASE_1, OPEN), _plan(PHASE_1, TICKED)
    assert (
        announce.line(before, after, 15)
        == "kestrel2 · Phase 2 · step 2 of 3 done · scenes 3/7 (#15)"
    )


def test_a_change_that_ticks_no_step_still_sends_a_line_marked_as_housekeeping() -> None:
    plan = _plan(PHASE_1, TICKED)
    assert announce.line(plan, plan, 16) == "kestrel2 · housekeeping · scenes 3/7 (#16)"


def test_the_last_step_of_a_phase_says_the_phase_is_complete() -> None:
    before, after = _plan(PHASE_1, TICKED), _plan(PHASE_1, ALL_DONE, scenes="7 of 7")
    assert announce.line(before, after, 20) == "kestrel2 · Phase 2 complete · scenes 7/7 (#20)"


def test_steps_ticked_in_two_phases_at_once_are_both_named() -> None:
    before = _plan(PHASE_1.replace("- [x] bars", "- [ ] bars"), OPEN)
    after = _plan(PHASE_1, TICKED)
    assert announce.line(before, after, 17) == (
        "kestrel2 · Phase 1 complete · Phase 2 · step 2 of 3 done · scenes 3/7 (#17)"
    )


def test_the_line_reads_the_plan_as_it_is_published_and_stays_short() -> None:
    scenes = PUBLISHED.search(PLAN)
    assert scenes is not None
    count = f"scenes {scenes[1]}/{scenes[2]}"
    assert announce.line(PLAN, PLAN, 6) == f"kestrel2 · housekeeping · {count} (#6)"
    ticked = announce.line(PLAN.replace("- [x]", "- [ ]", 1), PLAN, 106)
    assert ticked.startswith("kestrel2 · Phase ") and ticked.endswith(f"· {count} (#106)")
    assert "housekeeping" not in ticked
    assert len(ticked) <= 60, f"too long to read at a glance: {ticked}"


def test_a_plan_that_stops_saying_it_fails_instead_of_sending_half_a_line() -> None:
    plan = _plan(PHASE_1, TICKED)
    for broken in (
        plan.replace("Scenes passing:", "Something else:"),
        plan.replace("## Phase", "## Lane"),
    ):
        with pytest.raises(ValueError, match="docs/PLAN.md"):
            announce.line(plan, broken, 6)


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
    assert announce.merged(pulls, "bbb") == 6
    with pytest.raises(ValueError, match="ccc on main was not made by merging"):
        announce.merged(pulls, "ccc")


KEY = "123456:a-fake_key"
PULLS = [{"merge_commit_sha": "bbb", "title": "price store", "number": 6}]
#: The plan as it stood on main just before this merge: one step fewer ticked.
PARENT = {
    "encoding": "base64",
    "content": base64.encodebytes(PLAN.replace("- [x]", "- [ ]", 1).encode()).decode(),
}


def _env(record: Path, key: str = KEY) -> dict[str, str]:
    telegram = {"TELEGRAM_BOT_TOKEN": key, "TELEGRAM_CHAT_ID": "42"}
    github = {"GITHUB_TOKEN": "t", "GITHUB_REPOSITORY": "o/r", "GITHUB_SHA": "bbb"}
    return telegram | github | {"GITHUB_STEP_SUMMARY": str(record)}


def _replies(monkeypatch: pytest.MonkeyPatch, *replies: Any) -> list[str]:
    """The network, faked at its one edge. Returns the addresses called, in order."""
    queue, called = list(replies), []

    def urlopen(request: urllib.request.Request, timeout: float) -> io.BytesIO:
        assert timeout > 0, "a call with no timeout can hang the job until GitHub kills it"
        called.append(request.full_url)
        reply = queue.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return io.BytesIO(json.dumps(reply).encode())

    monkeypatch.setattr(urllib.request, "urlopen", urlopen)
    return called


def test_a_delivered_line_is_recorded_with_telegrams_message_number(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    called = _replies(monkeypatch, PULLS, PARENT, {"ok": True, "result": {"message_id": 9}})
    announce.main(_env(tmp_path / "summary.md"))
    assert called[:2] == [
        "https://api.github.com/repos/o/r/commits/bbb/pulls",
        "https://api.github.com/repos/o/r/contents/docs/PLAN.md?ref=bbb~1",
    ]
    assert called[2] == f"https://api.telegram.org/bot{KEY}/sendMessage" and len(called) == 3
    record = (tmp_path / "summary.md").read_text(encoding="utf-8")
    assert "Telegram message 9 sent" in record and "kestrel2 · Phase " in record


def test_a_previous_plan_github_did_not_send_whole_fails_saying_so(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _replies(monkeypatch, PULLS, {"encoding": "none", "content": ""})
    with pytest.raises(SystemExit, match="previous docs/PLAN.md .*'none'"):
        announce.main(_env(tmp_path / "summary.md"))
    assert not (tmp_path / "summary.md").exists()


def test_an_undelivered_line_fails_and_never_prints_the_key(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    said = io.BytesIO(b'{"ok": false, "description": "chat not found"}')
    url = f"https://api.telegram.org/bot{KEY}/sendMessage"
    refused = urllib.error.HTTPError(url, 400, "Bad Request", Message(), said)
    for refusal in ({"ok": False, "description": "chat not found"}, refused):
        _replies(monkeypatch, PULLS, PARENT, refusal)
        with pytest.raises(SystemExit, match="chat not found") as stopped:
            announce.main(_env(tmp_path / "summary.md"))
        assert KEY not in str(stopped.value)
    assert not (tmp_path / "summary.md").exists()


def test_a_key_that_is_not_a_bot_key_is_refused_by_name_not_shown() -> None:
    with pytest.raises(SystemExit, match="TELEGRAM_BOT_TOKEN is not a bot key") as stopped:
        announce.main(_env(Path("unused"), key="123456:a bad paste"))
    assert "bad paste" not in str(stopped.value)
