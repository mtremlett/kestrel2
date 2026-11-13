# Status

**Read this first, then `docs/PLAN.md`, then run `python check.py`.**

Three lanes run side by side (`docs/PLAN.md`). The shared part below is changed only by a
session the operator starts himself; each lane writes only in its own section, so that
parallel pull requests never touch the same lines. A lane's section says where it is, its
next step, what it found and did not fix, and any question it holds for the operator.

## Shared

Last updated: 13 November 2026.

### Where we are

Phase 2 under way. Scenes 1, 2 and 3 pass: scenes passing 3 of 7.

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

Three lanes now run day and night on the operator's PC, by his rulings of 13 November
(`docs/DECISIONS.md`): MONEY (scenes 4 to 7), DATA (the rehearsal data, the parked lines,
the store's open findings) and LADDER (phase 4). A runner outside this repository starts
each lane's next session when the last one ends, inside the plan's included usage only.
GitHub merges a pull request only when its check is green and its branch already holds
everything on main, so two green lanes cannot combine into a red main.

### Open questions for the operator

1. **A second GitHub account** for sessions to work through, so that the guards cannot be
   removed by the account that enforces them. On 13 November he chose to start the lanes
   on his own account now; the question stays open for later.

### Found, not fixed

- **Two of the line limits are prose, not guards.** CLAUDE.md says its 80 lines and
  CANON.md its 200 are held by a guard; no test reads either, and CANON.md is 224 lines.
- **A lane that needs the operator cannot reach him.** Its question waits in its STATUS
  section, and Telegram speaks only when a pull request merges. A lane that is halted, or
  out of usage, is seen only in the runner's report on his PC.
- **A newer ruff on the operator's PC calls the tree badly formatted.** Version 0.15
  formats differently from the pinned 0.8.6, so `python check.py` run with whatever is
  installed shows format red on a clean main. Run it in an environment built from
  `requirements.txt`. The check does not yet say which tool versions it ran with.
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

## MONEY

Last updated: 13 November 2026.

### Where it is

Scene 4 passes: the desk sends an order and its stop rests at the broker (`book.send`).
Before sending, the desk asks the broker whether it already has the order; if so it
records what the broker did and sends nothing, so a desk that dies mid-send and restarts
never buys twice. Only an order the broker never received passes the pre-trade gate and is
sent. Each fill is written once in the desk's ledger under the broker's own execution id.
A rejection, a partial fill and a dropped connection each come back with a stated reason;
a dropped order may be sent again, since the broker never had it. The contract test was
seen failing first; eleven deliberate breaks of the send path were each caught.

The desk has a pretend broker to trade against in simulation (`desk/broker.py`), built to
behave like the real one. A buy fills at the day's opening price under the broker's own
execution id, and leaves a stop resting at the broker for the shares it got, so the stop
protects the position even with the desk switched off. The stop is tested at every open,
and on the day of the buy itself: a day that falls through it sells at the stop, or at the
open when the day opens below it. Faults on request, each stated and never silent: a
rejection, a partial fill (half, the rest cancelled), a dropped connection (the order never
arrived), and the desk dying after the broker has the order. The desk can then ask the
broker what it did with an order id, so it never needs to send twice; a repeated id is
refused and counted. A position can be planted as if bought by hand. Its own contract test
was seen failing first; thirty deliberate breaks of the broker were each caught; a blind
review found nothing blocking, and its one fix taken (below) is tested.

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

### Next step

The book built from the broker (`book.positions`): what is held and what is left, with
every fill the broker made in the ledger, a stop's overnight sale included, so the gate
can enforce at most five holdings and give two buys of one line one fifth between them.

### Found, not fixed

- **What the blind review of the pretend broker left for the send path and the day run**
  (its one finding fixed: a fault was used up by an order that met no market):
  - The ledger holds only the fills an order's answer carries. A stop the broker sells is
    in no order's answer, so the book must collect the broker's fills since the last
    ask, or the ledger and the broker part company on the first stop that fires.
  - **What the blind review of the send path left** (nothing blocking; its test gap - an
    order the broker already holds must not be judged by the gate again - is fixed):
    the ledger is swapped in whole but not forced to disk, so a power cut (not a crash of
    the desk) can lose it; and a ledger deleted later reads as "no fills" without a
    word. Neither can send twice, since the broker is asked first; reconciliation
    (scene 6) is where a lost ledger must show. Unit test lines now stand at 1261 against
    1262 of product: the next step's tests must come with its code.
  - The broker fills at the bare open and sells a stop at exactly its level. Spread and
    slippage are not in its prices, so the day run must charge both, on both legs, the
    stop's sale included, or profit reads too high.
  - An order is sized at the last close and fills at the next open. On a gap up the fill
    costs more than the gate allowed; the book must hold a line to what was filled.
  - `open` judges the stops against the whole day before the desk's orders that day. A
    line sold by its stop and bought again the same morning can be stopped out twice on
    one bar. The day run should not buy a line its stop sold that day.
  - The desk cannot sell yet: the broker takes buys only. Scene 5 needs a sell, which
    must also take its line's resting stop away.
  - `inject` takes any symbol and a negative quantity (a hand sale) unchecked. Untested
    so far: a planted position on a line that also has the desk's stop, a partial fault
    on a one-share order, and several stops firing on one open.
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
- **What a blind review of the scenes left open** (the rest was fixed before commit):
  the sizer is given total capital, not what is left after the
  positions already held; the currency cost is not separated from commission in scene
  3; "a day with a cost line missing is refused" is held by the types, not by a day
  that should have paid UK tax showing none; scene 5 does not tell a sale by the
  strategy's rule from one by the resting stop; "no halt in force" has no interface yet.

### Unfinished code

Every one of these raises NotImplementedError, by design, until its phase builds it.

| part | phase |
|---|---|
| `book.positions`, `book.round_trips` | 2 |
| `day.run` | 2 |

Built and real: the send path and the ledger (`book.send`, `book.fills`), the pretend broker (`broker.Pretend`), sizing, cost and the gate for one holding (`orders.size`, `orders.cost`,
`orders.gate`), the five strategies (`strategy.decide`), the twenty lines, the archive
client (`archive.fetch`), the price store (`store.prepare`, `store.read`, `store.faults`),
the venue calendars,
the typed records (`Line`, `Bar`, `Parked`, `Decision`, `Settings`,
`Order`, `Fill`, `Sent`, `RoundTrip`, `Costs`, `Record`), and `Order` refusing a missing
stop, or one not below its price.

## DATA

Last updated: 13 November 2026.

### Where it is

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

The scenes' rehearsal data (`tests/scenes/rehearsal.py`, this lane's) is now fourteen
months long, September 2024 to 14 November 2025, each line on its own venue's calendar:
London lines trade 307 days, US lines 303. It rises, falls, breaks out, dips sharply and
falls again, and each of the five rules buys and sells on every one of the nineteen clean
lines (his ruling of 13 November). The scenes still see only its last six weeks, which
hold no holiday on either side, until scene 2 can count two calendars (below).

### Next step

Move the scenes onto the whole fourteen months - one line, `SCENES_FROM = FIRST` - as soon
as the money lane's scene 2 counts each line's own days. Meanwhile: one line the archive
refuses is parked, not the whole fetch stopped.

### Asked of the money lane

- **Scene 2's count assumes every line trades the same days.** It expects five rules times
  nineteen lines times one list of days. Over fourteen months London and the US keep
  different holidays, so the count must be each line's own: the number of bars each line
  has, added up, times five. That reads the same on today's six weeks, so it can land
  first. Driven: at full length scene 2 finds 28,925 decisions, every one present, and
  expects 29,545. Its future-blind loop over all 311 days takes about twenty seconds; it
  may cut on fewer days.
- `SESSIONS` will then be every day either venue trades; a day run on it meets days only
  one venue trades (Thanksgiving, Easter Monday).

### Found, not fixed

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
- **None of the five rules ever buys in the six weeks the scenes see today.** The fourteen
  months are built and proven to trade; scene 5 needs the scenes moved onto them (above).
  Until then no test reads the months before October, so only the script recorded in
  `docs/DECISIONS.md` shows they park nothing clean and that each rule trades in them.
- **What the blind review of the store's rules left open** (its one blocking finding - a run
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

## LADDER

Last updated: 13 November 2026.

### Where it is

The ladder has its unit of work (`lab/cell.py`): one of the five strategies on one of the
twenty lines over a window of days. It runs the desk's own decisions, never a copy of them,
over the line's whole history up to the window's end, and records the days each trade was
bought and sold. Each record carries a fingerprint of the code that made it and of every
bar it read, so a later batch can keep results and re-run only what changed. It names no
price or profit yet: no result is reported without its costs (`docs/DECISIONS.md`).

### Next step

A batch service that runs many cells, survives a bad one and a restart.

### Found, not fixed

- **The unit tests are within fifteen lines of the product.** The guard holds unit tests
  to no more lines than `desk/` and `lab/` together (1,120 against 1,134 on this branch).
  Every lane's next test must come with as much product, or a test consolidated.
- **What the blind review of the unit of work left for the batch** (nothing blocking; its
  test gaps on the data version and the trade pairing, and its unsorted-bars finding, are
  fixed and tested):
  - The code version is read from disk when `lab/cell.py` is imported. A long-lived
    process that imported the strategies earlier, and had them changed on disk before
    that, would key old code's results under the new code. The batch service must run each
    batch in a fresh process, or refuse when the files no longer match `cell.LOADED`.
  - Three of the five rules never trade in the contract test's twenty-five-day shapes
    (RSI-2, the 50/200 cross, Supertrend need far longer); their agreement with the desk
    is shown there only as "no trades". A fixture of more than 200 bars would cover them.
  - The key does not include the Python version, and only file contents, not file paths,
    are hashed; a file moved without a change of text keeps its key.
- **A cell runs all five strategies to keep one.** It asks `strategy.decide`, which decides
  every rule at once; a batch of the five on one line pays five times. Fine until a
  benchmark says otherwise.

- **A missing session older than sixty sessions no longer parks a line**, so research over
  years of history (the ladder) will meet gaps it must handle.
