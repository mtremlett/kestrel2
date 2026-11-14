@CANON.md

# KESTREL2 — the facts a session needs

The canon above is HOW work is done. This file is WHAT this desk is. Hard limit 80 lines
(a guard is owed: `docs/STATUS.md`). A rule belongs in the canon or a check, not here.

## The north star

Earn money for one family, as soon as it safely can. FIRST-LIGHT (the machine runs) →
A-GATE (the edge is real) → £100/day → £1,000/day. Urgency is spent on scope — fewer
lines, fewer strategies — never on how well the remaining thing is measured.

## What "working" means

`docs/SCENES.md` holds the scenes, in business language, each with its requirement ids,
its fixture data and an exact pass condition. They are the scoreboard. A change that
advances no scene needs a reason in `docs/PLAN.md`.

## The session protocol — "continue", or "continue - lane X"

Five lanes build the desk side by side, day and night: MONEY, PAPER, DATA, GRID and
RUNGS, each a chain of sessions a runner on his PC starts outside this repository.
`docs/PLAN.md` gives each lane its objective, book of work and files (`manifest.toml`
enforces them). A lane edits only those and its sections of STATUS, PLAN, SCOREBOARD, DECISIONS.

1. **Start.** Read `docs/STATUS.md` and `docs/PLAN.md`. Run `python check.py`. If
   anything is red, restoring green IS the objective. Otherwise state the one objective
   (your lane's, in a lane) and the test that will prove it.
2. **During.** That objective only. Follow the canon's workflow and its stop rules.
3. **End.** Update your sections of `docs/STATUS.md` and `docs/PLAN.md`, append one line
   to your table in `docs/SCOREBOARD.md`, commit, push the branch, open the pull request
   with auto-merge armed, and give the operator five lines.

**A lane has no one watching** (his ruling, `docs/DECISIONS.md`). A question of intended
behaviour is decided by the session itself, as the desk's mentor, from the north star,
the scenes and his past rulings: it writes the options, its choice and why in its lane's
part of `docs/DECISIONS.md`, and carries on. It stops only for what is his alone (below),
writing that question, with options and a recommendation, in its STATUS section.

## The commands

    python check.py              everything (the gate for a merge)
    python check.py --fast       format, lint and guards, for a commit hook
    python check.py --scenes     the scenes alone, in plain English

## How code reaches main

Branch, push, open a pull request, and arm auto-merge (`gh pr merge --squash --auto`).
GitHub merges it when `check` is green on its last commit AND the branch holds all of main,
so two green pull requests cannot combine into a red main; the runner brings a lane's
branch up to date and re-checks it. The operator does not approve merges. Main refuses a
direct push, a force-push, a red merge and a branch behind it; each was driven to prove it.

**A change that touches a guard** (`BUDGET.json`, `manifest.toml`, `tests/guards/`,
`check.py`, `.github/`) is announced on the pull request. Tightening one merges like any
change; loosening one is a business question with options and a recommendation, and by
his standing ruling the recommended option is taken without waiting, then told to him.

## The operator

He is not an engineer and does not read code or diffs. Write to him in plain English, in
terms of business behaviour and risk, with options and a recommendation; never ask him
to review code. He alone decides going live, entering credentials and spending money.
Anything else asked of him takes the recommended option without waiting (13 November).
All of it is paper: no real money moves until he signs for going live.

## External systems

The broker: the pretend one (`desk/broker.py`); the paper one, built by PAPER, on IB Gateway
on his PC, port 4002 and the old desk's paper account. The live port 4001 this desk NEVER
dials; a guard reads every line of `desk/` and `lab/`. Prices: one free archive
(`desk/archive.py`). Messages: one Telegram line per merge (`announce.py`).

## The predecessor, and the failure patterns

The first desk is a private repository, stood down: a quarry, never a foundation; proven
logic is ported piece by piece under its own test, and its numbers are not trusted. Its
ten failure patterns are in `docs/FAILURE_PATTERNS.md`, each with the check that now
catches it. A new recurring failure is added there with its guard, or it is not finished.
