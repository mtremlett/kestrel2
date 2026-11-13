"""The one line to the operator on each merge: what it says, and that it refuses rather
than guesses or stays quiet."""

from __future__ import annotations

import base64
import io
import json
import urllib.error
import urllib.request
from datetime import UTC, datetime
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
        announce.line(before, after, 15, 21)
        == "kestrel2 · Phase 2 · step 2 of 3 done · scenes 3/7 · usage 21% (#15)"
    )


def test_no_step_is_housekeeping_and_no_usage_figure_is_n_a_never_a_guess() -> None:
    plan = _plan(PHASE_1, TICKED)
    assert announce.line(plan, plan, 16, None) == (
        "kestrel2 · housekeeping · scenes 3/7 · usage n/a (#16)"
    )


def test_the_last_step_of_a_phase_says_the_phase_is_complete() -> None:
    before, after = _plan(PHASE_1, TICKED), _plan(PHASE_1, ALL_DONE, scenes="7 of 7")
    assert announce.line(before, after, 20, 100) == (
        "kestrel2 · Phase 2 complete · scenes 7/7 · usage 100% (#20)"
    )


def test_steps_ticked_in_two_phases_at_once_are_both_named() -> None:
    before = _plan(PHASE_1.replace("- [x] bars", "- [ ] bars"), OPEN)
    after = _plan(PHASE_1, TICKED)
    assert announce.line(before, after, 17, None) == (
        "kestrel2 · Phase 1 complete · Phase 2 · step 2 of 3 done · scenes 3/7 · usage n/a (#17)"
    )


def test_the_line_reads_the_plan_as_it_is_published_and_stays_short() -> None:
    scenes = PUBLISHED.search(PLAN)
    assert scenes is not None
    count = f"scenes {scenes[1]}/{scenes[2]}"
    assert announce.line(PLAN, PLAN, 6, 0) == f"kestrel2 · housekeeping · {count} · usage 0% (#6)"
    ticked = announce.line(PLAN.replace("- [x]", "- [ ]", 1), PLAN, 106, 100)
    assert ticked.startswith("kestrel2 · Phase ") and ticked.endswith(
        f"· {count} · usage 100% (#106)"
    )
    assert "housekeeping" not in ticked
    assert len(ticked) <= 72, f"too long to read at a glance: {ticked}"


def test_a_plan_that_stops_saying_it_fails_instead_of_sending_half_a_line() -> None:
    plan = _plan(PHASE_1, TICKED)
    for broken in (
        plan.replace("Scenes passing:", "Something else:"),
        plan.replace("## Phase", "## Lane"),
    ):
        with pytest.raises(ValueError, match="docs/PLAN.md"):
            announce.line(plan, broken, 6, None)


def test_a_missing_secret_fails_loudly_and_names_it() -> None:
    with pytest.raises(SystemExit, match="TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID"):
        announce.main({})
    with pytest.raises(SystemExit, match="missing TELEGRAM_CHAT_ID"):
        announce.main({"TELEGRAM_BOT_TOKEN": "a key", "TELEGRAM_CHAT_ID": "  "})


def test_only_the_pull_request_that_made_the_commit_is_announced() -> None:
    pulls = [
        {"merge_commit_sha": "aaa", "number": 5, "body": "Weekly usage: 90%"},
        {"merge_commit_sha": "bbb", "title": "price store", "number": 6},
    ]
    assert announce.merged(pulls, "bbb") == (6, None)
    with pytest.raises(ValueError, match="ccc on main was not made by merging"):
        announce.merged(pulls, "ccc")


def test_the_usage_figure_is_read_from_its_own_line_in_the_description_or_not_at_all() -> None:
    bodies: dict[str | None, int | None] = {
        "Weekly usage: 21%": 21,
        "Phase 2, step 3.\r\n\r\nWeekly usage: 7%\r\n\r\nMore words.": 7,
        "Weekly usage: 100%": 100,
        None: None,
        "": None,
        "Made by hand, no figure.": None,
        "Weekly usage: about 20%": None,
        "Weekly usage: 21": None,
        "Weekly usage: 101%": None,
        "Weekly usage: 2.5%": None,
        "Last week's Weekly usage: 30%": None,
        "Weekly usage: 21% by Tuesday": None,
        "Weekly usage: 21%  ": 21,
        "Weekly usage: 21%\r\nWeekly usage: 90%": None,
        "Weekly usage: ٢١%": None,
    }
    for body, figure in bodies.items():
        pull = {"merge_commit_sha": "bbb", "number": 6, "body": body}
        assert announce.merged([pull], "bbb") == (6, figure), body


KEY = "123456:a-fake_key"
DAY = datetime(2026, 11, 13, 14, 0, tzinfo=UTC)  #: a fixed afternoon: the line is sent
PULLS = [{"merge_commit_sha": "bbb", "title": "x", "number": 6, "body": "Weekly usage: 21%"}]
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
    announce.main(_env(tmp_path / "summary.md"), DAY)
    assert called[:2] == [
        "https://api.github.com/repos/o/r/commits/bbb/pulls",
        "https://api.github.com/repos/o/r/contents/docs/PLAN.md?ref=bbb~1",
    ]
    assert called[2] == f"https://api.telegram.org/bot{KEY}/sendMessage" and len(called) == 3
    record = (tmp_path / "summary.md").read_text(encoding="utf-8")
    assert "Telegram message 9 sent" in record and "kestrel2 · Phase " in record
    assert "· usage 21% (#6)" in record


def test_a_previous_plan_github_did_not_send_whole_fails_saying_so(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _replies(monkeypatch, PULLS, {"encoding": "none", "content": ""})
    with pytest.raises(SystemExit, match="previous docs/PLAN.md .*'none'"):
        announce.main(_env(tmp_path / "summary.md"), DAY)
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
            announce.main(_env(tmp_path / "summary.md"), DAY)
        assert KEY not in str(stopped.value)
    assert not (tmp_path / "summary.md").exists()


def test_a_key_that_is_not_a_bot_key_is_refused_by_name_not_shown() -> None:
    with pytest.raises(SystemExit, match="TELEGRAM_BOT_TOKEN is not a bot key") as stopped:
        announce.main(_env(Path("unused"), key="123456:a bad paste"), DAY)
    assert "bad paste" not in str(stopped.value)


def test_a_line_made_while_he_sleeps_is_held_for_the_morning_not_sent(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """22:00 to 08:00 UK: the line is recorded, and nothing reaches Telegram."""
    for hour, minute in ((22, 0), (3, 30), (7, 59)):
        called = _replies(monkeypatch, PULLS, PARENT)
        night = datetime(2026, 11, 13, hour, minute, tzinfo=UTC)  # November: UK is UTC
        announce.main(_env(tmp_path / "summary.md"), night)
        assert not any("telegram" in url for url in called) and len(called) == 2
    record = (tmp_path / "summary.md").read_text(encoding="utf-8")
    assert record.count("Held for the 08:00 message") == 3 and "· usage 21% (#6)" in record


def test_his_hours_begin_at_22_and_end_at_08_uk_time_in_summer_too() -> None:
    def gmt(year: int, month: int, day: int, hour: int, minute: int) -> datetime:
        return datetime(year, month, day, hour, minute, tzinfo=UTC)

    winter = [
        announce.asleep(gmt(2026, 11, 13, h, m)) for h, m in ((21, 59), (22, 0), (7, 59), (8, 0))
    ]
    assert winter == [False, True, True, False]
    assert announce.asleep(gmt(2026, 7, 1, 21, 30))  # 22:30 in London
    assert not announce.asleep(gmt(2026, 7, 1, 7, 0))  # 08:00 in London
    # the clocks change at 01:00 UTC on the last Sundays of March and October
    assert (
        announce.uk_hour(gmt(2026, 3, 29, 0, 59)) == 0
        and announce.uk_hour(gmt(2026, 3, 29, 1, 0)) == 2
    )
    assert (
        announce.uk_hour(gmt(2026, 10, 25, 0, 59)) == 1
        and announce.uk_hour(gmt(2026, 10, 25, 1, 0)) == 1
    )
    assert (
        announce.uk_hour(gmt(2027, 3, 28, 1, 0)) == 2
        and announce.uk_hour(gmt(2027, 10, 31, 0, 30)) == 1
    )
