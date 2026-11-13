@CANON.md

# KESTREL2 — the facts a session needs

The canon above is HOW work is done. This file is WHAT this desk is. Hard limit 80 lines,
held by a guard. A rule does not belong here; put it in the canon or make it a check.

## The north star

Earn money for one family, as soon as it safely can. FIRST-LIGHT (the machine runs) →
A-GATE (the edge is real) → £100/day → £1,000/day. Urgency is spent on scope — fewer
lines, fewer strategies — never on how well the remaining thing is measured.

## What "working" means

`docs/SCENES.md` holds the scenes, in business language, each with its requirement ids,
its fixture data and an exact pass condition. They are the scoreboard. A change that
advances no scene needs a reason in `docs/PLAN.md`.

## The session protocol — when the operator says "continue"

1. **Start.** Read `docs/STATUS.md` and `docs/PLAN.md`. Run `python check.py`. If
   anything is red, restoring green IS the objective. Otherwise state the one objective
   from the plan and the test that will prove it.
2. **During.** That objective only. Follow the canon's workflow and its stop rules.
3. **End.** Update `docs/STATUS.md`, append one line to `docs/SCOREBOARD.md`, commit,
   push the branch, open or update the pull request with auto-merge armed, and give the
   operator five lines.

## The commands

    python check.py              everything (the gate for a merge)
    python check.py --fast       format, lint and guards, for a commit hook
    python check.py --scenes     the scenes alone, in plain English

## How code reaches main

Branch, push, open a pull request, and arm auto-merge (`gh pr merge --squash --auto`):
GitHub merges it the moment `check` is green on its last commit, with no one present. The
operator does not approve merges (his rulings, `docs/DECISIONS.md`). Main refuses a direct
push, a force-push and a merge whose check has not passed; GitHub enforces all three and
each has been driven to prove it. Nothing merges red. There is no known-failing list.

**A change that touches a guard** (`BUDGET.json`, `manifest.toml`, `tests/guards/`,
`check.py`, `.github/`) is announced by the check on the pull request. Tightening one
merges like any change. Loosening one waits for the operator's plain-English yes in chat,
asked as a business question with options and a recommendation, never "review this".

## The operator

He is not an engineer and does not read code or diffs. Write to him in plain English, in
terms of business behaviour and risk. Never ask him to review code. Ask him about
intended behaviour, priorities and trade-offs, with options and a recommendation.

He decides: going live, credentials, spend, permissions, the phase, and any loosening of
a guard. He does not approve merges. Everything else technical is the session's to decide
and to own.

## External systems

| what | how it is reached | state |
|---|---|---|
| broker (paper) | one adapter in `desk/`, paper port only | not built yet |
| price history | a free archive, re-fetched and re-checked on entry | not built yet |
| messages to the operator | one messenger, with a delivery record | desk: not built; merges: one Telegram line, `announce.py` |

The live-money port is 4001 and this desk NEVER dials it. The paper port is 4002. A guard
reads every line of every file in `desk/` and `lab/` on every change.

## The predecessor

The first desk is a separate, private repository, stood down and kept for reference. Its
code is a quarry, never a foundation: proven logic is ported in piece by piece under its
own test, and nothing is copied wholesale. Its numbers are not trusted — its own store
was five months stale when this one was started.

## The ten failure patterns

`docs/FAILURE_PATTERNS.md`, each with the check that now catches it. A new recurring
failure is added there with its guard, or it is not finished.
