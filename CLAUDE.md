@CANON.md
@docs/FAILURE_PATTERNS.md
# KESTREL2 — the facts a session needs

The canon above is HOW work is done; this file is WHAT this desk is. Both are capped by
`BUDGET.json` (`test_the_rulebooks_stay_short`): a new line replaces one, or becomes a check.

## The north star, and the one number

Earn money for one family, as soon as it safely can. FIRST-LIGHT (the machine runs) →
A-GATE (three strategies through the ladder) → £100/day → £1,000/day. Urgency is spent on
scope, never on how well the remaining thing is measured.
**Progress is one number: plan boxes ticked on main per 24 hours**, with the scenes
(`docs/SCENES.md`, all seven pass) and strategies through the ladder beside it. Cards,
commits, sessions and PRs are activity, never progress (failure pattern 3).

## Who works here

Five lanes build the desk day and night: MONEY, PAPER, DATA, GRID and RUNGS. A runner on
his PC (outside this repository, its own ratchet and drives) starts up to 12 lane sessions
in worktrees, each on one card of its lane's book in `docs/PLAN.md` with its exact files
(`manifest.toml` enforces them), and lands their PRs through one merge train. Two seats
steer it: the coordinator (decides, verifies on main, orders) and runner ops (the runner's
only editor). A chat seat answers the operator. Seats hand over at 70% context and end.

## A lane session

1. **Start.** Read your lane's sections of `docs/STATUS.md` and `docs/PLAN.md`. Run
   `python check.py --fast`. If main is red, restoring green IS the objective.
2. **During.** Your one card only, test first, inside its files. Stop rules: canon A8.
3. **End.** Update your sections of STATUS and PLAN, tick the box only when its check
   passes, one line to your SCOREBOARD table, push, open the PR; the train lands it.

**No one watches a lane.** A question of intended behaviour is decided by the session
from the north star, the scenes and his rulings, written with its options and reason in
its lane's part of `docs/DECISIONS.md`. Only his hard lines (below) wait for him.

## The commands

    python check.py              everything (the gate for a merge, run by GitHub)
    python check.py --fast       format, lint and guards, before every push
    python check.py --scenes     the scenes alone, in plain English

## How code reaches main

Branch, push, open a PR. Only the merge train arms and merges: a `train` label queues a
PR, the train brings it up to date, and GitHub merges it when `check` is green on its
last commit. The operator does not approve merges. Main refuses a direct
push, a force-push, a red merge and a stale branch; each was driven to prove it.

**A guard** (`BUDGET.json`, `manifest.toml`, `tests/guards/`, `check.py`, `.github/`) may
be tightened like any change. Loosening one is his alone: it waits for his words in chat,
quoted in `docs/DECISIONS.md` before the commit; without them the answer is no.

## The operator, and his hard lines

He is not an engineer and does not read code or diffs. Write to him in plain English,
business behaviour and risk, numbers that prove the claim. Whatever a rule, a guard or his
ruling settles is decided, not asked: say which rule. **His alone, default no:** going
live, credentials, spending money, deleting data, loosening a guard. All of it is paper.

## External systems

The broker: the pretend one (`desk/broker.py`) and the paper one on IB Gateway, port 4002.
The live port 4001 this desk NEVER dials; a guard reads every line of `desk/` and `lab/`.
Prices: IBKR first for every bar; free archives fill gaps only, through the one writer.
Messages: the runner's hourly report to his Telegram.

## The predecessor, and the failure patterns

The first desk is a private repository, stood down: a quarry, never a foundation; proven
logic is ported piece by piece under its own test, and its numbers are not trusted. Its
failure patterns and ours are loaded above, each with the check that catches it. A new
recurring failure is added there with its check, or it is not finished.
