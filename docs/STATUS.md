# Status

**Read this first, then `docs/PLAN.md`, then run `python check.py`.**

Last updated: 13 November 2026.

## Where we are

Phase 0. The operator approved the seven scenes on 13 November, and they are now written
as tests in `tests/scenes/test_scenes.py`. Scenes passing: 0 of 7, as expected: each one
stops at a part of the desk that is not built yet. The desk's shape exists only as the
typed outlines those scenes call; there is no working desk code.

**The check is RED on one guard, and only the operator can clear it** — see open
question 1. Everything else is green: format, lint, strict types, eleven of twelve
guards, and the scenes step.

## The next step

The operator's ruling on open question 1. Then this branch merges, and phase 1 starts:
one price store with one writer, cleaned on entry, until scene 1 passes.

## Open questions for the operator

1. **A size rule blocks writing the tests before the code.** The rule: once the desk
   passes 200 lines, test lines may not exceed desk lines. The guards alone are 282
   lines and the seven scenes 220, so writing the scenes first — which the canon
   requires — puts tests at 502 lines against 303 of desk outline. Options:
   - **A (recommended):** the rule counts only the everyday tests, the kind that pile up
     one per bug, and applies from the first line instead of from 200. The guards and
     the scenes are fixed in number and already change only with his approval.
   - **B:** keep the rule. Then nothing on this branch can merge until about 200 more
     lines of desk exist, and phase 1 would have to be built on this same branch.
   A session tried to make change A and was refused, correctly: loosening a guard is
   his call. On his word, the edit is a few lines in `tests/guards/test_guards.py`
   and one key in `BUDGET.json`.
2. **A second GitHub account** for sessions to work through, so that the guards cannot be
   removed by the account that enforces them. Not urgent; needed before any unattended
   work.
3. **The A-GATE test.** Ten consecutive £100 days is close to unreachable for an honest
   edge. The recommendation is sixty trading days averaged, luck-corrected, with a
   drawdown limit. He has agreed in conversation; it is not yet written into a
   requirement.

## Found, not fixed

- **What a blind review of the scenes left open** (the rest was fixed before commit):
  the fixture is 33 trading days, so a strategy needing a longer warm-up would never
  trade in scenes 5 to 7 — lengthen it, with the venue calendars, when the five
  strategies are chosen; the sizer is given total capital, not what is left after the
  positions already held; the currency cost is not separated from commission in scene
  3; "a day with a cost line missing is refused" is held by the types, not by a day
  that should have paid UK tax showing none; scene 5 does not tell a sale by the
  strategy's rule from one by the resting stop; "no halt in force" has no interface yet.
- **The scenes rule trusts the error's name.** A scene counts as "not built" when it
  fails with NotImplementedError. A test that raised that error itself would pass as
  unbuilt. No test does; nothing yet checks that none does.
- **Sessions opened in the predecessor's folder carry its permissions.** The session that
  wrote the scenes was started there and could not delete a scratch file. Open sessions
  directly on this folder.
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

Every one of these raises NotImplementedError, by design, until its phase builds it.

| part | phase |
|---|---|
| `store.prepare`, `store.read` | 1 |
| `strategy.decide` | 2 |
| `orders.size`, `orders.cost`, `orders.gate` | 2 |
| `broker.Pretend` and all its methods | 2 |
| `book.send`, `book.fills`, `book.positions`, `book.round_trips` | 2 |
| `day.run` | 2 |

Built and real: the typed records (`Line`, `Bar`, `Parked`, `Decision`, `Settings`,
`Order`, `Fill`, `Sent`, `RoundTrip`, `Costs`, `Record`), and `Order` refusing a missing
stop, or one not below its price.
