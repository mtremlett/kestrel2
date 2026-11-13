#!/usr/bin/env python
"""ONE LINE TO THE OPERATOR for every change that lands on main.

GitHub runs this once the check has passed on main (the "announce" job in
.github/workflows/check.yml). It compares docs/PLAN.md's phase checklists just before
and just after the merge, and sends one short Telegram line, read at a glance:

    kestrel2 · Phase 2 · step 3 of 6 done · scenes 4/7 · usage 21% (#16)
    kestrel2 · Phase 2 complete · scenes 7/7 · usage 34% (#20)
    kestrel2 · housekeeping · scenes 4/7 · usage n/a (#17)   (no step; no usage stated)

The bot key and the chat id are GitHub secrets the operator sets himself. A missing one
fails the job, loudly; it never skips. Standard library only (docs/DECISIONS.md).

He sleeps from 22:00 to 08:00 UK (his words, 13 November 2026). A line made then is not
sent: it is recorded in the job's summary, and the runner's 08:00 message lists the night's
changes instead.
"""

from __future__ import annotations

import base64
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from check import PUBLISHED, ROOT

#: A phase's checklist: its heading, then every line up to the next heading.
PHASE = re.compile(r"^## (Phase \d+)\b.*$((?:\n(?!## ).*)*)", re.MULTILINE)
BOX = re.compile(r"^- \[([ x])\]", re.MULTILINE)
#: The week's usage of the operator's plan, which GitHub cannot see: a lane run states it
#: on a line of its own in its pull request's description. A hand-made one has none.
USAGE = re.compile(r"^Weekly usage: ([0-9]{1,3})%[ \t\r]*$", re.MULTILINE)
SECRETS = ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID")
GITHUB = ("GITHUB_TOKEN", "GITHUB_REPOSITORY", "GITHUB_SHA", "GITHUB_STEP_SUMMARY")
#: The shape of a Telegram bot key. Checked on entry, so a bad paste is refused by name
#: and never reaches a URL, where an error would print it in a public log.
BOT_KEY = re.compile(r"\d+:[A-Za-z0-9_-]+")
#: His sleeping hours, UK time: a line made in them waits for the runner's 08:00 message.
QUIET_FROM, QUIET_UNTIL = 22, 8


def _last_sunday(year: int, month: int) -> datetime:
    """01:00 UTC on the month's last Sunday: when UK clocks change."""
    day = datetime(year, month + 1, 1, 1, tzinfo=UTC) - timedelta(days=1)
    return day - timedelta(days=(day.weekday() + 1) % 7)


def uk_hour(when: datetime) -> int:
    """The hour on a UK clock: GMT, or BST from the last Sunday of March to the last
    Sunday of October (the law since 1998; no time-zone database needed)."""
    utc = when.astimezone(UTC)
    summer = _last_sunday(utc.year, 3) <= utc < _last_sunday(utc.year, 10)
    return (utc + timedelta(hours=1 if summer else 0)).hour


def asleep(when: datetime) -> bool:
    hour = uk_hour(when)
    return hour >= QUIET_FROM or hour < QUIET_UNTIL


def steps(plan: str) -> dict[str, tuple[int, int]]:
    """Each phase's steps, ticked and in all, or ValueError if the plan has no phases."""
    found = {name: BOX.findall(body) for name, body in PHASE.findall(plan)}
    if not found:
        raise ValueError("docs/PLAN.md no longer lists its phases as '## Phase N' checklists")
    return {name: (boxes.count("x"), len(boxes)) for name, boxes in found.items()}


def line(before: str, after: str, number: int, usage: int | None) -> str:
    """The one line: each phase in which this merge ticked a step, or "housekeeping" when
    it ticked none, and the week's usage as the pull request stated it, or "n/a".
    ValueError naming what docs/PLAN.md no longer says."""
    scenes = PUBLISHED.search(after)
    if scenes is None:
        raise ValueError("docs/PLAN.md no longer publishes 'Scenes passing: **N of M**'")
    was, now = steps(before), steps(after)
    moved = [
        f"{name} complete" if done == total else f"{name} · step {done} of {total} done"
        for name, (done, total) in now.items()
        if done > was.get(name, (0, 0))[0]
    ]
    parts = ["kestrel2", *(moved or ["housekeeping"]), f"scenes {scenes[1]}/{scenes[2]}"]
    parts.append("usage n/a" if usage is None else f"usage {usage}%")
    return " · ".join(parts) + f" (#{number})"


def required(env: Mapping[str, str], names: tuple[str, ...]) -> dict[str, str]:
    """Every name set and not blank, or the job stops here saying which are missing."""
    missing = [name for name in names if not env.get(name, "").strip()]
    if missing:
        raise SystemExit(
            f"announce: missing {', '.join(missing)}. Set it in the repository on GitHub: "
            "Settings, Secrets and variables, Actions."
        )
    return {name: env[name].strip() for name in names}


def weekly(body: str | None) -> int | None:
    """The week's usage, in percent, from its own line in a pull request's description,
    or None unless exactly one such line states a whole percent up to 100: two lines, an
    example quoted beside the real one or a stale one left in, could say different things."""
    found = USAGE.findall(body or "")
    return int(found[0]) if len(found) == 1 and int(found[0]) <= 100 else None


def merged(pulls: list[dict[str, Any]], sha: str) -> tuple[int, int | None]:
    """The number and the stated weekly usage of the pull request whose merge made this
    commit. A commit on main that no merge made went round the rules, and is not
    announced as normal."""
    for pull in pulls:
        if pull.get("merge_commit_sha") == sha:
            return int(pull["number"]), weekly(pull.get("body"))
    raise ValueError(
        f"commit {sha} on main was not made by merging a pull request, "
        "or GitHub has not linked it yet: re-run this job to tell which"
    )


def _call(request: urllib.request.Request) -> Any:
    try:
        with urllib.request.urlopen(request, timeout=30) as reply:  # noqa: S310 - fixed https hosts
            return json.load(reply)
    except urllib.error.HTTPError as refused:
        said = refused.read().decode(errors="replace")
        raise SystemExit(f"announce: {request.host} refused, {refused.code}: {said}") from refused


def _github(github: Mapping[str, str], path: str) -> Any:
    return _call(
        urllib.request.Request(
            f"https://api.github.com/repos/{github['GITHUB_REPOSITORY']}/{path}",
            headers={
                "Authorization": f"Bearer {github['GITHUB_TOKEN']}",
                "Accept": "application/vnd.github+json",
            },
        )
    )


def main(env: Mapping[str, str] = os.environ, when: datetime | None = None) -> None:
    secrets, github = required(env, SECRETS), required(env, GITHUB)
    if not BOT_KEY.fullmatch(secrets["TELEGRAM_BOT_TOKEN"]):
        raise SystemExit("announce: TELEGRAM_BOT_TOKEN is not a bot key; set it again")
    sha = github["GITHUB_SHA"]
    number, usage = merged(_github(github, f"commits/{sha}/pulls"), sha)
    # The plan as main held it just before this merge: the merge commit's first parent.
    parent = _github(github, f"contents/docs/PLAN.md?ref={sha}~1")
    if parent.get("encoding") != "base64":
        raise SystemExit(
            f"announce: GitHub sent the previous docs/PLAN.md as {parent.get('encoding')!r}, "
            "not base64; over 1 MB it sends no content"
        )
    before = base64.b64decode(parent["content"]).decode("utf-8")
    after = (ROOT / "docs" / "PLAN.md").read_text(encoding="utf-8")
    text = line(before, after, number, usage)
    if asleep(when or datetime.now(UTC)):
        with Path(github["GITHUB_STEP_SUMMARY"]).open("a", encoding="utf-8") as record:
            record.write(f"Held for the 08:00 message (his sleeping hours):\n\n> {text}\n")
        return
    form = {"chat_id": secrets["TELEGRAM_CHAT_ID"], "text": text}
    sent = _call(
        urllib.request.Request(
            f"https://api.telegram.org/bot{secrets['TELEGRAM_BOT_TOKEN']}/sendMessage",
            data=urllib.parse.urlencode(form).encode(),
        )
    )
    if sent.get("ok") is not True:
        raise SystemExit(f"announce: Telegram did not deliver: {sent.get('description')}")
    with Path(github["GITHUB_STEP_SUMMARY"]).open("a", encoding="utf-8") as record:
        record.write(f"Telegram message {sent['result']['message_id']} sent:\n\n> {text}\n")


if __name__ == "__main__":
    main()
