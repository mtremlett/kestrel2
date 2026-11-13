# Status

**Read this first, then `docs/PLAN.md`, then run `python check.py`.**

Last updated: 13 November 2026.

## Where we are

Phase 1 under way. Scene 1 passes: scenes passing 1 of 7. The desk has one price store
with one writer (`desk/store.py`): it rebuilds itself from the archive each morning,
keeps only bars that can be true, and parks a line it cannot clean with a dated reason;
the line comes back by itself once its bars are clean. Gaps and staleness are judged
against each venue's own calendar (`desk/venues.py`, London and US, 2010 to 2027). Its
tests were seen failing first, and thirteen deliberate breaks of the store and calendar
were each caught by a test.

Two rulings of 13 November are in force (`docs/DECISIONS.md`): sessions merge their own
pull requests when the check is green, and GitHub now refuses any merge whose check has
not passed (driven red on pull request #5); the A-GATE test is written as AG-01 to
AG-06 in `docs/PLAN.md`, with the thirty-day terms fixed in advance.

## The next step

The rest of phase 1: daily bars for the twenty lines, fetched from a free archive into
the store. The twenty lines themselves are not chosen yet; that choice comes first.

## Open questions for the operator

1. **A second GitHub account** for sessions to work through, so that the guards cannot be
   removed by the account that enforces them. Not urgent; needed before any unattended
   work.

## Found, not fixed

- **What a blind review of the scenes left open** (the rest was fixed before commit):
  the fixture is 33 trading days, so a strategy needing a longer warm-up would never
  trade in scenes 5 to 7 — lengthen it, with the venue calendars, when the five
  strategies are chosen; the sizer is given total capital, not what is left after the
  positions already held; the currency cost is not separated from commission in scene
  3; "a day with a cost line missing is refused" is held by the types, not by a day
  that should have paid UK tax showing none; scene 5 does not tell a sale by the
  strategy's rule from one by the resting stop; "no halt in force" has no interface yet.
- **The store cannot read history before 2010 or after 2027.** The calendar refuses those
  years rather than guess, so a line whose archive reaches back further stops the
  prepare loudly. Extend the calendar's one-off closures before loading older history.
- **A split the archive did not adjust parks the line**, as does a genuine one-day move
  of more than 60% up or 37.5% down. Parking is the safe side; adjusting for splits needs
  a record of corporate actions, which nothing holds yet.
- **A whole history quoted in pence passes.** The store catches a change of unit within
  a line, not a line that is in the wrong unit from its first bar. The instrument master
  does not yet say which unit each line is quoted in.
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
| `strategy.decide` | 2 |
| `orders.size`, `orders.cost`, `orders.gate` | 2 |
| `broker.Pretend` and all its methods | 2 |
| `book.send`, `book.fills`, `book.positions`, `book.round_trips` | 2 |
| `day.run` | 2 |

Built and real: the price store (`store.prepare`, `store.read`), the venue calendars,
the typed records (`Line`, `Bar`, `Parked`, `Decision`, `Settings`,
`Order`, `Fill`, `Sent`, `RoundTrip`, `Costs`, `Record`), and `Order` refusing a missing
stop, or one not below its price.
