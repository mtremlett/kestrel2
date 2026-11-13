#!/usr/bin/env python
"""ONE LINE TO THE OPERATOR for every change that lands on main.

GitHub runs this once the check has passed on main (the "announce" job in
.github/workflows/check.yml). It compares docs/PLAN.md's phase checklists just before
and just after the merge, and sends one short Telegram line, read at a glance:

    kestrel2 · Phase 2 · step 3 of 6 done · scenes 4/7 (#16)
    kestrel2 · Phase 2 complete · scenes 7/7 (#20)
    kestrel2 · housekeeping · scenes 4/7 (#17)      (a change that ticks no step)

The bot key and the chat id are GitHub secrets the operator sets himself. A missing one
fails the job, loudly; it never skips. Standard library only (docs/DECISIONS.md).
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
from pathlib import Path
from typing import Any

from check import PUBLISHED, ROOT

#: A phase's checklist: its heading, then every line up to the next heading.
PHASE = re.compile(r"^## (Phase \d+)\b.*$((?:\n(?!## ).*)*)", re.MULTILINE)
BOX = re.compile(r"^- \[([ x])\]", re.MULTILINE)
SECRETS = ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID")
GITHUB = ("GITHUB_TOKEN", "GITHUB_REPOSITORY", "GITHUB_SHA", "GITHUB_STEP_SUMMARY")
#: The shape of a Telegram bot key. Checked on entry, so a bad paste is refused by name
#: and never reaches a URL, where an error would print it in a public log.
BOT_KEY = re.compile(r"\d+:[A-Za-z0-9_-]+")


def steps(plan: str) -> dict[str, tuple[int, int]]:
    """Each phase's steps, ticked and in all, or ValueError if the plan has no phases."""
    found = {name: BOX.findall(body) for name, body in PHASE.findall(plan)}
    if not found:
        raise ValueError("docs/PLAN.md no longer lists its phases as '## Phase N' checklists")
    return {name: (boxes.count("x"), len(boxes)) for name, boxes in found.items()}


def line(before: str, after: str, number: int) -> str:
    """The one line: each phase in which this merge ticked a step, or "housekeeping" when
    it ticked none. ValueError naming what docs/PLAN.md no longer says."""
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


def merged(pulls: list[dict[str, Any]], sha: str) -> int:
    """The number of the pull request whose merge made this commit. A commit on main that
    no merge made went round the rules, and is not announced as normal."""
    for pull in pulls:
        if pull.get("merge_commit_sha") == sha:
            return int(pull["number"])
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


def main(env: Mapping[str, str] = os.environ) -> None:
    secrets, github = required(env, SECRETS), required(env, GITHUB)
    if not BOT_KEY.fullmatch(secrets["TELEGRAM_BOT_TOKEN"]):
        raise SystemExit("announce: TELEGRAM_BOT_TOKEN is not a bot key; set it again")
    sha = github["GITHUB_SHA"]
    number = merged(_github(github, f"commits/{sha}/pulls"), sha)
    # The plan as main held it just before this merge: the merge commit's first parent.
    parent = _github(github, f"contents/docs/PLAN.md?ref={sha}~1")
    if parent.get("encoding") != "base64":
        raise SystemExit(
            f"announce: GitHub sent the previous docs/PLAN.md as {parent.get('encoding')!r}, "
            "not base64; over 1 MB it sends no content"
        )
    before = base64.b64decode(parent["content"]).decode("utf-8")
    text = line(before, (ROOT / "docs" / "PLAN.md").read_text(encoding="utf-8"), number)
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
