# Status

**Read this first, then `docs/PLAN.md`, then run `python check.py`.**

Last updated: 13 November 2026.

## Where we are

Phase 2 under way. Scenes 1, 2 and 3 pass: scenes passing 3 of 7.

The desk now sizes a buy from one capital number (`desk/orders.py`), by the operator's
ruling of 13 November: at most five holdings, each costing at most a fifth of the capital,
a leveraged line counted at what it controls (5QQQ may take £400 of £10,000), and the stop
set before the order exists, where the market under the line has fallen 10%. Whole shares
only, priced in pounds under Interactive Brokers UK's published fixed fees, the currency
conversion counted. The sizer and the pre-trade gate read the same number: change it and
both move. Leverage is a fact on every line in the instrument master. Thirty deliberate
breaks are each caught; a blind review's blocking finding (a pound line at any
exchange rate slipped past the gate) is fixed, and its other one is recorded below.

The desk has its five
daily strategies (`desk/strategy.py`), chosen by the operator on 13 November: five
textbook rules at their published settings, long only, untuned - Connors' RSI-2
pullback, Bollinger's 20/2 pullback, the Turtles' 20/10 breakout, the 50/200-day cross
and Supertrend 10/3. Each is shown one bar at a time after its close, so it cannot read
a later bar; scene 2 proves the decisions up to any day are the same with the later
bars deleted. A second implementation written apart from the desk's found the same
trade days on sixty long walks, and forty-four of forty-five deliberate breaks were
caught; the forty-fifth cannot change a decision.

Phase 1's data is in. The twenty lines are in the
instrument master (`desk/lines.py`), by the operator's ruling of 13 November: ten in
London in pounds, ten in the US in dollars. One client for the free archive
(`desk/archive.py`, Yahoo's public chart service) fetches every bar since 2010 and reads
it once, on entry. Fetched into a store on 13 November for the 13th: **sixteen of the
twenty are clean and ready**: all ten US lines from 2010, and SMGB, IITU, VHYG, IB1T, ISF
and VUSA. Four are parked, each with a named reason (below, under "found, not fixed"). Two
store rules came from his rulings the same day: a London auction price up to 3% outside
the day's range stretches it, and only a fault in the last sixty sessions parks a line
(older bad days are dropped and listed in the line's fault record; a price step parks
however old).

The desk has one price store with one writer (`desk/store.py`): it rebuilds itself from the archive each morning,
keeps only bars that can be true, and parks a line it cannot clean with a dated reason;
the line comes back by itself once its bars are clean. Gaps and staleness are judged
against each venue's own calendar (`desk/venues.py`, London and US, 2010 to 2027). Its
tests were seen failing first; a blind review's five blocking findings were each made a
failing test, then fixed; and twenty-five deliberate breaks of the store, the
calendar and the instrument master were each caught by a test. This session's three store
rules were each driven against deliberate breaks in both directions, and caught.

Two rulings of 13 November are in force (`docs/DECISIONS.md`): sessions merge their own
pull requests when the check is green, and GitHub now refuses any merge whose check has
not passed (driven red on pull request #5); the A-GATE test is written as AG-01 to
AG-06 in `docs/PLAN.md`, with the thirty-day terms fixed in advance.

Every change that lands on main now sends the operator one Telegram line once the check
passes there. Since his request of 13 November it is short: the phase whose step the change
ticked in this plan's checklist, or "housekeeping" when it ticked none, the scenes count,
the week's usage of his plan as the pull request states it on a line "Weekly usage: 21%"
("n/a" when it states none), and the pull request's number, for example "kestrel2 · Phase
2 · step 3 of 6 done · scenes 4/7 · usage 21% (#16)" (`announce.py`, the `announce` job;
`docs/DECISIONS.md`). A missing secret turns the job red; that was driven on main before
the secrets existed. The first line, for #7, reached his phone on 13 November; the first
short one, for #17, on the same day.

## The next step

Phase 2's third step: the pretend broker, with its faults, and the send path that records
its fills, so that scene 4 passes. Before scene 5, the scenes' rehearsal data is lengthened to about fourteen months
(his ruling of 13 November): on today's six weeks none of the five rules ever buys.

## Open questions for the operator

1. **A second GitHub account** for sessions to work through, so that the guards cannot be
   removed by the account that enforces them. Not urgent; needed before any unattended
   work.

## Found, not fixed

- **No Telegram line when main is red after a merge.** The line waits for the check on
  main. Two green pull requests could combine into a red main, and then he hears nothing
  from Telegram; GitHub's own failure notice is the only alarm. Closing it means either
  requiring a branch to be up to date before it merges, or a second line for a red main.
- **A newer ruff on the operator's PC calls the tree badly formatted.** Version 0.15
  formats differently from the pinned 0.8.6, so `python check.py` run with whatever is
  installed shows format red on a clean main. Run it in an environment built from
  `requirements.txt`. The check does not yet say which tool versions it ran with.
- **Four of the twenty lines are parked, each for a reason in the archive's data:**
  - 3LGO has no history in the free archive at all (the same product in dollars, 3GOL,
    has fourteen years). He chose to keep 3LGO; it waits for history to gather.
  - 2MU moved more in a day than the store believes a market moves, five times (5 August
    2024, 26 September 2024, 19 December 2024, 4 April 2025, 24 October 2025): real crashes
    of a 2x product, most likely. Each needs its confirmed close recorded in
    `Line.real_moves`, from the issuer or a second source, before the line comes back.
  - 5QQQ jumped from 0.0024 to 1.18 pounds on 22 August 2024: a share consolidation the
    archive did not adjust. Its history before that date is on another scale.
  - SGLN's first weeks, April to June 2011, swing between two price levels ten times: the
    archive garbled them. A price step parks however old, so the line stays parked.
- **The free archive promises nothing.** Yahoo's chart service is free and keyless but
  unofficial; it may change or stop. Stooq, the other free archive, now answers with a
  bot check, which this desk does not get around.
- **One line the archive refuses stops the whole fetch.** `archive.fetch` raises for that
  line; the day run (phase 2) must park it instead and carry on with the others.
- **A missing session older than sixty sessions no longer parks a line**, so research over
  years of history (the ladder) will meet gaps it must handle.
- **What the blind review of this session left open** (its one blocking finding - a run
  of days in the wrong unit taken as a lasting step - is fixed and tested; the first fix
  dropped 2MU's real December 2024 crash as bad days, so a run is now bad days only when it
  sits a hundredfold out):
  - A single day out of line with both neighbours is still dropped as a wrong unit, at any
    size: a real one-day crash that recovers the next day would be lost from the history.
  - A stretched bar's new high or low is not recorded anywhere as differing from the
    archive's.
  - A line's bars and its fault record are swapped in one after the other, so a crash
    between the two leaves them disagreeing.
  - The sixty-session window looks back a hundred days on the calendar, which knows 2010
    onward, so a trading day before mid-April 2010 cannot be prepared.
- **What the blind review of sizing left for the book** (its blocking finding - a pound
  line accepted any exchange rate - is fixed and tested):
  - **"At most five holdings" is not enforced yet.** The gate sees one order, not the
    book, so a sixth holding passes, and two strategies buying the same line the same day
    each get their own fifth (two orders, two ids). The book must give the gate what is
    held and what is left before scene 5 trades more than one line.
  - The gate trusts the stop of an order built by hand; only the sizer sets the 10% rule.
    Scene 4's own orders carry a stop of 30, about a third below their price.
  - Stops and costs are exact decimals, not rounded: a real broker refuses a stop off its
    price step, so the paper adapter (phase 3) must round each stop to its line's step,
    down, and the instrument master must carry that step.
  - The fees are Interactive Brokers UK's fixed pricing. If his account is on tiered
    pricing, the schedule is a different one; and UK stamp duty is assumed nil for the ten
    London funds and products, to be confirmed line by line before the day counts UK tax.
- **What the blind review of the five strategies left for later scenes** (its blocking
  findings, test gaps, are fixed):
  - A rule's position is its own idea, not the book's. It counts each of its buys and
    sells as done; if the gate refuses a buy, or the resting stop sells, the rule still
    thinks it holds, will not buy again while its condition lasts, and later says sell to
    a flat book. The day run must decide which it trusts before scene 5.
  - A decision depends on where the history starts (the averages' seeds, Supertrend's
    carried bands, the 50/200's observed cross). Measured: walk 1 with its first 30 bars
    dropped changes two Bollinger decisions. If the archive's first date moves, the same
    day can decide differently; a replay is identical only on identical saved data.
  - A line whose last bar is older than the day still gets decisions, dated at its own
    last bar. The day run must act only on decisions dated that day.
  - "Still warming up" and "chose to stay out" both read as hold; "the 20 days before"
    means the 20 bars before, so a day the store dropped is skipped over.
  - Wilder's smoothing and the true range live inside `strategy`. If the stop at entry
    is set from the true range, it is asked of `strategy`, not written a second time.
- **None of the five rules ever buys in the scenes' rehearsal data.** They need 20 to 200
  days of history and then a breakout or a sharp dip; the 33 rehearsal days drift
  gently. Scene 5 cannot pass until the data is lengthened, as he ruled on 13 November.
- **What a blind review of the scenes left open** (the rest was fixed before commit):
  the sizer is given total capital, not what is left after the
  positions already held; the currency cost is not separated from commission in scene
  3; "a day with a cost line missing is refused" is held by the types, not by a day
  that should have paid UK tax showing none; scene 5 does not tell a sale by the
  strategy's rule from one by the resting stop; "no halt in force" has no interface yet.
- **What the blind review of the store left open** (its five blocking findings, and one
  its re-review found in the repair, were fixed and each is now a test):
  - The calendar knows 2010 to 2027 only. A bar from another year is refused and its
    line parked; history before 2010 needs that decade's one-off closures first.
  - A split the archive did not adjust parks the line if it is 2-for-1 or larger; a
    smaller wrong factor (a 3-for-2 split, pounds read as dollars) cannot be told from
    a real move by price alone and passes.
    So does a whole history quoted in pence by an archive that says pounds: pence
    become pounds only when the archive names them pence.
  - A real move larger than the store believes (a fall of 37.5%, a rise of 60%) parks
    the line until its confirmed close is recorded on the line (`Line.real_moves`).
    Nothing fills that record yet; 2MU is parked for want of it.
  - Two bad bars in a row are kept and the line parked, not cleaned: safe only while a
    parked line is never traded or read for a decision.
  - Parking lives only in what `store.prepare` returns (each line's faults are now
    saved beside its bars, but not whether they parked it), and a line dropped from the
    archive leaves its old files readable. The day run (phase 2)
    must read parking from the prepare it runs.
  - A frozen feed (the same bar repeated with no volume) is not caught.
  - A vendor that leaves out a day a line did not trade (a suspension) parks the line
    for as long as that gap is in its history.
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
- **The predecessor's paper book is flat.** Read at 14:36 UK on 13 Nov 2026, read-only:
  paper account, no positions and no open orders. Nothing was placed.

## Unfinished code

Every one of these raises NotImplementedError, by design, until its phase builds it.

| part | phase |
|---|---|
| `broker.Pretend` and all its methods | 2 |
| `book.send`, `book.fills`, `book.positions`, `book.round_trips` | 2 |
| `day.run` | 2 |

Built and real: sizing, cost and the gate for one holding (`orders.size`, `orders.cost`,
`orders.gate`), the five strategies (`strategy.decide`), the twenty lines, the archive
client (`archive.fetch`), the price store (`store.prepare`, `store.read`, `store.faults`),
the venue calendars,
the typed records (`Line`, `Bar`, `Parked`, `Decision`, `Settings`,
`Order`, `Fill`, `Sent`, `RoundTrip`, `Costs`, `Record`), and `Order` refusing a missing
stop, or one not below its price.
