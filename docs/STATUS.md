# Status

**Read this first, then `docs/PLAN.md`, then run `python check.py`.**

Last updated: 13 November 2026.

## Where we are

Phase 0. The machinery exists and is proven; no desk code has been written yet. Scenes
passing: 0 of 7, because the scenes are not yet written as tests.

The check is green: format, lint, strict types and twelve guards, on this machine and on
GitHub. Main refuses a direct push, proven by trying one.

## The next step

Write the seven scenes as failing tests, once the operator has approved them. They are
expected to fail — that is the point. Then phase 1: one price store with one writer,
cleaned on entry.

## Open questions for the operator

1. **The scenes** in `docs/SCENES.md` need his approval before they become the
   scoreboard.
2. **A second GitHub account** for sessions to work through, so that the guards cannot be
   removed by the account that enforces them. Not urgent; needed before any unattended
   work.
3. **The A-GATE test.** Ten consecutive £100 days is close to unreachable for an honest
   edge. The recommendation is sixty trading days averaged, luck-corrected, with a
   drawdown limit. He has agreed in conversation; it is not yet written into a
   requirement.

## Found, not fixed

- **The predecessor's price archive is five months stale.** A sample of 120 tickers
  found the newest bar in June 2026 for 85% of them, none current, and some major names
  absent entirely. It is usable as a head start on history, never as current data.
- **Eight of the predecessor's scheduled tasks could not be disabled** — they refuse with
  "access denied" because they were registered with different rights. Two of them can
  place orders. Buying is blocked by that desk's own kill switch instead; the tasks
  themselves still need the operator's hand.
- **The predecessor's paper book is not flat.** It holds positions with stops resting at
  the broker. Selling them needs the operator present, inside market hours.

## Unfinished code

Nothing. There is no desk code yet, so nothing is half-built. When there is, each
unfinished part raises an explicit error and is listed here by name.
