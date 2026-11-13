#!/usr/bin/env python
"""ONE LINE TO THE OPERATOR for every change that lands on main.

GitHub runs this once the check has passed on main (the "announce" job in
.github/workflows/check.yml). It takes the merged pull request's title from GitHub, the
scenes count and the current objective from docs/PLAN.md, and sends one Telegram line:

    kestrel2: <title> merged (#7). Scenes passing 1 of 7. Next: <the current objective>.

The bot key and the chat id are GitHub secrets the operator sets himself. A missing one
fails the job, loudly; it never skips. Standard library only (docs/DECISIONS.md).
"""

from __future__ import annotations

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

OBJECTIVE = re.compile(r"\*\*Current objective:\*\*(.+?)\n\s*\n", re.DOTALL)
SECRETS = ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID")
GITHUB = ("GITHUB_TOKEN", "GITHUB_REPOSITORY", "GITHUB_SHA", "GITHUB_STEP_SUMMARY")
#: The shape of a Telegram bot key. Checked on entry, so a bad paste is refused by name
#: and never reaches a URL, where an error would print it in a public log.
BOT_KEY = re.compile(r"\d+:[A-Za-z0-9_-]+")


def line(plan: str, title: str, number: int) -> str:
    """The one line, or ValueError naming what docs/PLAN.md no longer says."""
    scenes = PUBLISHED.search(plan)
    if scenes is None:
        raise ValueError("docs/PLAN.md no longer publishes 'Scenes passing: **N of M**'")
    objective = OBJECTIVE.search(plan)
    if objective is None:
        raise ValueError("docs/PLAN.md no longer states its '**Current objective:**'")
    following = " ".join(objective[1].split()).rstrip(".")
    return (
        f"kestrel2: {title} merged (#{number}). "
        f"Scenes passing {scenes[1]} of {scenes[2]}. Next: {following}."
    )


def required(env: Mapping[str, str], names: tuple[str, ...]) -> dict[str, str]:
    """Every name set and not blank, or the job stops here saying which are missing."""
    missing = [name for name in names if not env.get(name, "").strip()]
    if missing:
        raise SystemExit(
            f"announce: missing {', '.join(missing)}. Set it in the repository on GitHub: "
            "Settings, Secrets and variables, Actions."
        )
    return {name: env[name].strip() for name in names}


def merged(pulls: list[dict[str, Any]], sha: str) -> tuple[str, int]:
    """The title and number of the pull request whose merge made this commit. A commit on
    main that no merge made went round the rules, and is not announced as normal."""
    for pull in pulls:
        if pull.get("merge_commit_sha") == sha:
            return str(pull["title"]), int(pull["number"])
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


def main(env: Mapping[str, str] = os.environ) -> None:
    secrets, github = required(env, SECRETS), required(env, GITHUB)
    if not BOT_KEY.fullmatch(secrets["TELEGRAM_BOT_TOKEN"]):
        raise SystemExit("announce: TELEGRAM_BOT_TOKEN is not a bot key; set it again")
    sha = github["GITHUB_SHA"]
    pulls = _call(
        urllib.request.Request(
            f"https://api.github.com/repos/{github['GITHUB_REPOSITORY']}/commits/{sha}/pulls",
            headers={
                "Authorization": f"Bearer {github['GITHUB_TOKEN']}",
                "Accept": "application/vnd.github+json",
            },
        )
    )
    title, number = merged(pulls, sha)
    text = line((ROOT / "docs" / "PLAN.md").read_text(encoding="utf-8"), title, number)
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
