# Status

**Read this first, then `docs/PLAN.md`, then run `python check.py`.**

Five lanes run side by side (`docs/PLAN.md`). The shared part below is changed only by a
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

Five lanes now run day and night on the operator's PC, by his rulings of 13 November
(`docs/DECISIONS.md`): MONEY (scenes 5 to 7), PAPER (phase 3, begun alongside phase 2),
DATA (the research universe, the parked lines, the store's findings), GRID (the fast grid
engine) and RUNGS (the ladder's rungs). Every lane runs on Fable while its allowance is
under 45%, then on Opus until a Fable reset (his ruling). A
runner outside this repository starts each lane's next session when the last one ends,
inside the plan's included usage, stopping at 80% of the week.
GitHub merges a pull request only when its check is green and its branch already holds
everything on main, so two green lanes cannot combine into a red main.

### Open questions for the operator

1. **A second GitHub account** for sessions to work through, so that the guards cannot be
   removed by the account that enforces them. On 13 November he chose to start the lanes
   on his own account now; the question stays open for later.

### Found, not fixed

- **Two of the line limits are prose, not guards.** CLAUDE.md says its 80 lines and
  CANON.md its 200 are held by a guard; no test reads either, and CANON.md is 224 lines.
- **The runner's own lines to his phone wait for his key.** A lane that halts, pauses at
  the weekly cap or needs his decision, and the 07:00 line, are sent by the runner on his
  PC from a file holding the bot key, which he copies beside the runner himself. Until he
  does, they are written to the runner's log only.
- **A Windows Update restart overnight stops the lanes until he logs in.** The runner
  starts at his logon; starting it without one needs his password in Task Scheduler,
  which is his call. He is pausing updates.
- **The lane guard judges whole files.** A lane may write in any part of a shared
  document; that it keeps to its own section is checked only by the daily audit.
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
- **The predecessor's scheduled tasks are all disabled.** Eight had refused a session with
  "access denied"; on 13 November he checked every `KESTREL_` task in Task Scheduler as
  administrator and each says disabled (`docs/DECISIONS.md`).
- **The predecessor's paper book is flat.** Read at 14:36 UK on 13 Nov 2026, read-only:
  paper account, no positions and no open orders. Nothing was placed.
- **The unit tests are within a few lines of the product, and lanes collide on it.** The
  guard holds unit tests to no more lines than `desk/` and `lab/` together (about 1,435
  against 1,444 on this branch). The ladder's batch went red by one line once brought up to
  date with main (#28), each lane green alone; the runner's re-check caught it and a line
  was trimmed. Every lane's next test must come with as much product, or a test merged. A
  session the operator starts could record this in `docs/FAILURE_PATTERNS.md`.

## MONEY

Last updated: 13 November 2026 (this section cut to what is open; git keeps the rest).

### Where it is

Scenes 5 of 7. Built and real (its decisions in `docs/DECISIONS.md`): the five rules
(`strategy`); sizing, cost and the gate (`orders`); the pretend broker (`broker`); the send
path, the ledger, the book and reconciliation on one comparison (`book`); the day's trading
(`day.trade`). Unfinished, raising NotImplementedError by design: `day.run`, the day's
record (phase 2); scenes 6 and 7 both read it, so they pass together.

### Next step

R-PAPER-2: any broker behind the send path and the day run, read once for each order. Then
the kill switch and its drill (EMG-02; his ruling: first of the lane's own book), the costs
whole (R-RUNGS-1), and the day's record (`day.run`), scene 6 moved onto the fourteen months.

### Requests to PAPER

- [ ] R-MONEY-4 (later, opened 2026-11-13 18:35 UK): `paper.differences` asks `book.differences`.

### Requests to DATA

- [ ] R-MONEY-2 (blocking, opened 2026-11-13 18:15): the scenes moved onto the fourteen months.
- [ ] R-MONEY-3 (later, opened 2026-11-13 18:15): a daily rate, pounds per dollar, in the store.

### Found, not fixed

- **Costs:** spread, slippage and UK tax are in no fill, round trip, `orders.cost` or the gate
  yet; money has no one rounding policy (to the penny); the fees are IBKR UK's fixed schedule,
  not the tiered one; scene 3 does not part the currency cost from commission.
- **Nobody is told of a mismatch yet.** Until someone acts, a line whose stop was cancelled is
  unprotected, and one partly sold by hand keeps a stop for more shares than are held.
- **The ledger** is not forced to disk, and a lost one reads as "no fills" without a word.
- **The gate** takes the book as a bare mapping, trusts the stop of an order built by hand,
  and sizes at the last close: a gap up at the open can fill above a fifth.
- **The day run** decides each line's whole history again every day (24 seconds in scene 5),
  reads the archive it is handed (R-DATA-3), and has no halt to read yet.
- **The rules:** a decision depends on where the history starts; "warming up" and "staying
  out" both read as hold; twenty days means twenty bars; the true range lives in `strategy`.
- **For the paper adapter:** fills must be the desk's own orders and stops only; orders still
  working must be counted by the gate and by reconciliation; a connection lost while reading
  is not a stated answer; a stop on a line the book lacks needs its own test there.
- **Untested at the pretend broker:** `inject` on any symbol; a planted position beside the
  desk's stop; a partial fill of one share; several stops sold on one open.

## PAPER

Last updated: 13 November 2026 (this section cut to what is open; git keeps the rest).

### Where it is

Read-only so far; nothing has been placed on paper. The account check (`desk/paper.py`, client
222, paper accounts only) found the account quiet on 13 November. All twenty lines are listed
at the broker (`desk/listing.py`); six London lines are priced there in pence (`Listing.floor`).

### Next step

R-MONEY-4: `paper.differences` asks `book.differences`, so the rule has one home; with it, a
holding matched by the broker's own number for the line. Then the fills and orders the broker
reports, read-only: each fill under the broker's id, its price back from the broker's unit, the
desk's own orders and stops told from anyone else's. Then placing, behind `Pretend`'s interface:
no order until that day's check is clean, run on a second day, and the kill switch is drilled.

### Requests to MONEY

- [ ] R-PAPER-2 (blocking, opened 2026-11-13 18:15): `book.send`, `book.collect` and `day.trade`
  accept any broker with `Pretend`'s interface, not `Pretend` by name, so the adapter stands in.

### Requests to DATA

- [ ] R-PAPER-3 (later, opened 2026-11-13 18:55 UK): each line's ISIN a fact on `Line`, confirmed
  from the issuer or the exchange, so the door knows the broker's line by it, not by its ticker.

### Done for other lanes

- R-DATA-5: done in #53 for its first half (this lane's test lines state their UK tax). Open:
  what the contract note of the first London product bought says of stamp duty (conformance).

### Found, not fixed

- **Each day:** nothing runs the account check or reads the listings daily, or refuses an order
  on an unlisted line; what the desk does with a held line that comes back unlisted is undecided.
- **Before a stop rests:** the gateway probably sends a client its own open orders unasked, which
  stops both readings; questions share a number space with orders; no real open order seen yet.
- **2MU** (parked) trades in £1 steps above £500 where the broker's rule says £5: whether the
  broker takes a stop on its own step there is unproven. See its conformance before it trades.
- **Prices:** a paper stop and the simulation's differ by up to one step; a broker price out of
  `Listing.floor` is a plain number, which the adapter must keep inside the door.
- **Unread at the broker:** each line's hours, smallest order and order kinds (in the listing's
  answer); daily bars for all twenty (DATA's check); SPCX is "SPACE EXPLORATION TECHN-CL A" there.
- **The gateway:** no overall time limit on a conversation; unproven whether one that lost its
  look-up or broker link tells a later client; some bad answers stop it with no plain sentence.
- **For a session he starts:** the live-port guard reads for one number, so would miss the
  desktop program's live port; deliberate breaks need Python's cache off (FAILURE_PATTERNS).

## DATA

Last updated: 13 November 2026 (the scenes on the whole fourteen months; this section cut).

### Where it is

Phase 1's data is in: the twenty lines, one archive client, one store with one writer, both venues'
calendars for 2010 to 2027, and the research list (1,065 tickers: 864 clean, 201 parked). The scenes
now see all fourteen months of rehearsal data (R-MONEY-2); scenes 1 to 5 pass on it.

### Next step

The lane's objective, the research list's parked fifth (`docs/PLAN.md`). Open for later: R-MONEY-3
(a daily pounds-per-dollar rate in the store) and R-PAPER-3 (each line's ISIN).

### Done for other lanes

- R-MONEY-1: done in #47
- R-MONEY-2: done in this pull request

### Requests to GRID

- [ ] R-DATA-1 (later, opened 2026-11-13 18:15): a cell takes a `Line` from `universe.UNIVERSE` and
  reads `store.read(root / line.venue, line.symbol)`: thirteen symbols are two companies, by venue.

### Requests to MONEY

- [ ] R-DATA-3 (later, opened 2026-11-13 18:15): the day run reads the archive through
  `archive.gather` and hands `store.prepare` its answers whole, so a refused line parks with its reason.
- [x] R-DATA-4 (later, opened 2026-11-13 18:40 UK): each `Line(...)` in its tests states its UK tax.
- [ ] R-DATA-6 (later, opened 2026-11-13 19:20 UK): scene 5 reads `CLEAN`, now the one name for the
  whole rehearsal data; `HISTORY` is the same thing, and then goes.

### Requests to PAPER

- [x] R-DATA-5 (later, opened 2026-11-13 18:40 UK): each `Line(...)` in its tests states its UK tax.

### Found, not fixed

- **UK tax (NS-05).** Nil for the five London products is unseen on a contract note. A line's tax
  still defaults to nil; that can go now. The research list's London shares pay 0.5%, unchecked.
- **Four of the twenty are parked:** 3LGO (no history), 2MU (five real crashes unrecorded), 5QQQ (an
  unadjusted consolidation), SGLN (garbled 2011). The archive is free, unofficial, unpaced (DAT-08).
- **The scenes' days** are now every day either venue trades; scenes 6 and 7 meet days only one does.
- **The research list** is today's members only (BT-09), has no kept home, keeps a departed ticker's
  files, loses a ticker's bars on a refused day, and leaves off three London members quoted in euros.
- **The store:** nothing fills `Line.real_moves` or `Line.suspended`; a wrong factor under 2-for-1
  passes; a bad print not a hundredfold out, and a freeze under five sessions, have no rule; parking
  lives only in what `store.prepare` returns. No test yet pins that L01's stamp duty is charged.

## GRID

Last updated: 13 November 2026. Took over the ladder lane's cell, batch and results on 13
November, when the operator split the ladder into GRID and RUNGS.

### Where it is

The ladder has its unit of work (`lab/cell.py`): one of the five strategies on one of the
twenty lines over a window of days. It runs the desk's own decisions, never a copy of them,
over the line's whole history up to the window's end, and records the days each trade was
bought and sold. Each record carries a fingerprint of the code that made it and of every
bar it read, so a later batch can keep results and re-run only what changed. It names no
price or profit yet: no result is reported without its costs (`docs/DECISIONS.md`).

It now has a batch service (`lab/batch.py`) that runs many cells in turn and writes each
result down as it finishes. A cell that fails is recorded with its error and the rest carry
on; a batch stopped part way, even in the middle of writing a line, takes up where it
stopped when started again, never running a finished cell twice. A failed cell is tried
again on the next start. A batch refuses to start when the code on disk is no longer the
code it loaded.

A result is now kept by what made it: the code and every bar the rule was shown. Each run
reads every cell's bars again and re-runs a cell only when its code or its bars have
changed; a bar corrected after a window's end leaves that window's result alone.

The fast grid engine is built (`lab/grid.py`, numpy) and proven against the desk's own
engine: for each of the five strategies it works out, for a line's whole history at once,
whether the strategy is in the market after every bar, and on the golden series and on
prices as long as the archive's it holds exactly what the desk holds, day by day. It never
guesses. The desk counts in exact decimals and the grid in floating point, so wherever two
numbers are too close for floating point to tell which is larger the grid refuses the cell
by name (`TooClose`) and gives no answer; the desk's own engine must decide it. On prices
like the archive's it refused nothing; on made-up prices on a coarse tick it refuses a
close exactly on a Supertrend band. Measured on 4,000 days of one line: the desk's engine
takes about 100 ms for the five rules, the grid 6 to 8 ms, after 17 ms once per line to
read its prices in. Two blind reviews found three ways to a wrong answer, all on prices no
market has; each is fixed and tested, and the second review's whole random comparison, run
again on the repaired engine, found no difference from the desk. Nothing uses the grid yet: the unit of work still runs the desk's own.

### Next step

Move the unit of work onto the grid (`lab/cell.py`): a cell's trades from the grid's
answer, and from the desk's own engine whenever the grid refuses, the same record either
way, the grid's file counted in the code version. Then auto-tune.

### Asked of the money lane

- **The five rules take no settings.** The grid's first pass is "every strategy at every
  setting", and the grid may only be trusted where it matches the desk's engine (canon B2).
  Until `desk/strategy.py`'s rules can be made at other settings (the window lengths, the
  RSI's bar, the bands' widths), the grid is proven, and so runs, at the published five only.

### Found, not fixed

- **What the blind reviews of the grid engine left** (three wrong answers found, each fixed
  and tested: an RSI on days that move a thousand-millionth of the price, a Supertrend band
  when a close sits far outside its day's range, and ties among prices of 26 digits and
  more; and six safeguards no test held, each now held by one). There was no third review
  of the last repairs; the second review's own random comparison was run again and is clean:
  - **A line with five or more identical closes in a row, at prices as long as the
    archive's, is refused for the RSI** (and twenty or more for the Bollinger rule): an
    average of equal long prices is a tie floating point cannot call. The desk's engine
    decides those cells, so the answer is right and only slower. The store drops a frozen
    feed, but a thinly traded research ticker may have such runs; worth counting on the
    research universe before the first pass.
  - Reading a line's prices in costs twice what the five rules do (17 ms against 8 ms on
    4,000 days), nearly all of it turning each decimal into a whole number. It is paid once
    per line, not per cell. And the Supertrend and the RSI still walk the days one at a
    time for Wilder's smoothing and the carried bands. Fine until the first pass is timed.
  - Deliberate breaks that survive, which no series found can show: the Supertrend's band
    carried on the day's own close for the day before's (no position differed on some 700
    series searched); a close set against its own day's upper band; the Bollinger check
    for whole prices whose squares pass 2**53 (it needs an exact tie among very large
    numbers); Wilder's smoothing on a series exactly as long as its window (nothing reads
    that value); and the margin of the Supertrend's upper band and of its carrying measured
    against the close alone, or against the day's prices and not all so far (the committed
    case is the lower band's; the review's random comparison covers the rest, outside the
    repository).
  - On whole-number prices, about thirty unchanged closes in a row fade the RSI's gain and
    loss to nothing and the grid refuses the line for that rule; the desk's engine decides.
  - The golden series are read from the money lane's `tests/unit/test_strategy.py`
    (`GOLDEN`, `_walk`, `_jumpy`, `_bars`, `START`): if that file renames them, the grid's
    test stops and the two lanes must move together.
- **A helper's working copy was left in the main folder.** The tool that gives a helper its
  own copy made it under `.claude/worktrees/` of the operator's main kestrel2 folder, with a
  branch `worktree-agent-ab11b126c53bfd69e` in the shared repository. This session did not
  go into that folder to remove it. It holds no change and can be deleted.
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
- **What the blind review of the batch left** (nothing blocking; its two findings on
  failed cells never retried and on cutting a torn line by rewriting the whole journal
  are fixed and tested):
  - That each line reaches the disk before the next cell starts (`os.fsync`) is not seen
    by any test; removing it leaves the tests green. Only a killed process would show it.
  - Nothing stops two processes working on one journal at once; the module says one at a
    time. A lock is owed when the batch is started by anything but a person.
  - A journal line corrupt in the middle fails loudly but names neither the file nor the
    line; a failed cell keeps its error's type and message, not where it was raised.
- **What keeping results by key left** (blind review, its one blocking finding fixed):
  - The unit of work's fingerprint misses two breaks no test drives: a bar whose volume
    alone changed, and two bars on one day (the order check's `<=` made `<`). Its contract
    test owes a case for each.
  - Every run reads and hashes each cell's bars, and a cell with no result hashes them
    twice (once for its key, once in its run). Fine until a benchmark says otherwise.
  - The journal keeps every old record and one line per failure per run; it only grows.
- **A cell runs all five strategies to keep one.** It asks `strategy.decide`, which decides
  every rule at once; a batch of the five on one line pays five times. Fine until a
  benchmark says otherwise.
- **A missing session older than sixty sessions no longer parks a line**, so research over
  years of history (the ladder) will meet gaps it must handle.

## RUNGS

Last updated: 13 November 2026 (this section cut to what is open; git, the decisions and
the scoreboard keep the rest).

### Where it is

The ladder has two rungs. The first (`lab/rung.py`) says whether a strategy earns on a line
after the broker's costs and the desk's own 10% stop by more than chance would give: at
least thirty trades, their average return two standard errors above nothing. The luck rung
(`lab/luck.py`) judges many first-rung verdicts as one set, each one's chance multiplied by
every trial it was picked from, against one combined 5%. Both are proven on made-up prices
only. **No winner on real prices is to be believed yet** (see below).

### Next step

In-sample and out-of-sample folds: a strategy's history cut into folds, each judged after
costs, the two side by side, the verdict on the worst fold; every fold a trial the luck rung
counts (canon B6, AG-01).

### Requests to MONEY

- [ ] R-RUNGS-1 (later, opened 2026-11-13 18:15): a sale's own cost, spread and slippage in
  `desk/orders.py`, from the desk's one cost model, so the first rung's costs are whole.

### Found, not fixed

- **The first rung's costs are not whole.** No spread, slippage or sale-only fees: a sale is
  charged as a buy of the same shares (R-RUNGS-1). One exchange rate serves a whole window,
  so a dollar line's verdict carries no currency gain or loss. Owed before real prices.
- **The luck rung's chance is honest only for bell-shaped trades.** Many small wins and a
  rare large loss, on few trades, read as far less chance than they are. The cure is the
  book's deflated Sharpe (LAD-03, LAD-08, LAD-09) and "failing fairly" (LAD-06, STR-12).
- **The count of trials is the caller's to give.** A cell that leaves no verdict must be
  stated, and nothing keeps the count from batch to batch: the register is a box in the book.
- **A verdict must not be kept by its record's key**, whose code version does not cover
  `lab/rung.py` or `desk/orders.py`.
- **A line whose one share costs more than its room** fails the whole verdict loudly.
- **Not held by a test, none able to arise from real numbers:** the 5% line exactly ("under"
  for "or under"), the first rung's bar of exactly 2, and its arithmetic setting. The
  chance asked for no trades, or a count given as a fraction, is not refused in plain words.
- **`rung.verdict`**, the first rung's pass rule as one function, is called by the first
  rung and by the luck rung's tests only.
