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

Last updated: 13 November 2026 (any broker behind the send path).

### Where it is

Scenes 5 of 7. Built and real (its decisions in `docs/DECISIONS.md`): the five rules
(`strategy`); sizing, cost and the gate (`orders`); the pretend broker (`broker`); the send
path, the ledger, the book and reconciliation on one comparison (`book`); the day's trading
(`day.trade`), behind which any broker can stand (`broker.Broker`). Unfinished, raising
NotImplementedError by design: `day.run`, the day's record; scenes 6 and 7 pass together on it.

### Next step

The kill switch and its drill (EMG-02; his ruling: first of the lane's own book), cancelling
a sixth question of any broker. Then the costs whole (R-RUNGS-1), and the day's record
(`day.run`), scene 6 checking the book against the broker's on every day.

### Done for other lanes

- R-PAPER-2: done in #64

### Requests to PAPER

- [ ] R-MONEY-4 (later, opened 2026-11-13 18:35 UK): `paper.differences` asks `book.differences`.

### Requests to DATA

- [x] R-MONEY-2 (blocking, opened 2026-11-13 18:15): the scenes moved onto the fourteen months.
- [ ] R-MONEY-3 (later, opened 2026-11-13 18:15): a daily rate, pounds per dollar, in the store.

### Found, not fixed

- **Costs:** spread, slippage and UK tax are charged nowhere yet; no one rounding policy (to
  the penny); fees are IBKR UK's fixed schedule, not tiered; scene 3 mixes currency and fees.
- **Nobody is told of a mismatch yet.** Until someone acts, a line whose stop was cancelled is
  unprotected, and one partly sold by hand keeps a stop for more shares than are held.
- **The ledger** is not forced to disk, and a lost one reads as "no fills" without a word.
- **The gate** takes the book as a bare mapping, trusts the stop of an order built by hand,
  and sizes at the last close: a gap up at the open can fill above a fifth.
- **The day run** decides each line's whole history again every day (24 seconds in scene 5),
  reads the archive it is handed (R-DATA-3), and has no halt to read yet.
- **The rules:** a decision depends on where the history starts; "warming up" and "staying
  out" both read as hold; twenty days means twenty bars; the true range lives in `strategy`.
- **For the paper adapter:** an order still working is in none of the five answers, so `place`
  must answer finally or the gate overbuys; a resting order that is no sell stop is unseen; a
  stop's level is never compared; a connection lost while reading is not a stated answer.
- **Untested at the pretend broker:** `inject` on any symbol; a planted position beside the
  desk's stop; a partial fill of one share; several stops sold on one open.

## PAPER

Last updated: 13 November 2026 (this section cut to what is open; git keeps the rest).

### Where it is

Read-only so far; nothing has been placed on paper. The account check (`desk/paper.py`, client
222, paper accounts only) found the account quiet on 13 November. All twenty lines are listed
at the broker (`desk/listing.py`); six London lines are priced there in pence (`Listing.floor`).

### Next step

Two boxes can start at once (PLAN notes, 13 November): paper-reports (R-MONEY-4 first, then
the broker's fills and orders, read-only) and paper-gateway (daily restart, weekly re-login).
The rest is one chain behind paper-reports: check, adapter, stops, drill, conformance. No order
until that day's check is clean on a second day and the kill switch is drilled.

### Requests to MONEY

- [x] R-PAPER-2 (blocking, opened 2026-11-13 18:15): done in #64.
- Open: R-MONEY-4 is a request, not a box; it changes `desk/paper.py`, as paper-reports does.

### Requests to DATA

- [x] R-MONEY-2 (blocking, opened 2026-11-13 18:15): the scenes moved onto the fourteen months.
- [ ] R-MONEY-3 (later, opened 2026-11-13 18:15): a daily rate, pounds per dollar, in the store.

### Found, not fixed

- **Costs:** spread, slippage and UK tax are charged nowhere yet; no one rounding policy (to
  the penny); fees are IBKR UK's fixed schedule, not tiered; scene 3 mixes currency and fees.
- **Nobody is told of a mismatch yet.** Until someone acts, a line whose stop was cancelled is
  unprotected, and one partly sold by hand keeps a stop for more shares than are held.
- **The ledger** is not forced to disk, and a lost one reads as "no fills" without a word.
- **The gate** takes the book as a bare mapping, trusts the stop of an order built by hand,
  and sizes at the last close: a gap up at the open can fill above a fifth.
- **The day run** decides each line's whole history again every day (24 seconds in scene 5),
  reads the archive it is handed (R-DATA-3), and has no halt to read yet.
- **The rules:** a decision depends on where the history starts; "warming up" and "staying
  out" both read as hold; twenty days means twenty bars; the true range lives in `strategy`.
- **For the paper adapter:** an order still working is in none of the five answers, so `place`
  must answer finally or the gate overbuys; a resting order that is no sell stop is unseen; a
  stop's level is never compared; a connection lost while reading is not a stated answer.
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

Last updated: 13 November 2026 (a cell names its line and venue).
### Where it is

Built and proven: the unit of work (`lab/cell.py`), the restart-safe batch (`lab/batch.py`) and
the fast grid engine (`lab/grid.py`: the desk's position after every bar, or a refusal by name,
`TooClose`). A cell runs on the grid (25 ms on 4,000 days, the desk's 95) and holds its whole
`Line`: one symbol can be two companies (BA; thirteen such), so bars come from the line's own
venue's folder and the journal names symbol and venue. No price or profit is named.

### Next step

Auto-tune (`lab/tune.py`), so a pass can never take the PC down; it can run beside the key
box (BT-04). Then the first pass, which runs at the published five settings on the 864 clean
tickers until R-GRID-1 and the data lane's parked fifth land; then the week, the weekend.

### Done for other lanes

- R-DATA-1: done in #73

### Requests to MONEY

- [ ] R-GRID-1 (later, opened 2026-11-13 18:15): the five rules made at other settings (window
  lengths, the RSI's bar, the bands' widths) in `desk/strategy.py`; the grid is trusted only
  where it matches the desk's engine (canon B2), so it runs at the published five until then.

### Requests to RUNGS

- [ ] R-GRID-2 (later, opened 2026-11-13 20:04 UK): make each cell from a Line (`Cell(name, line,
  start, end)`) in `tests/unit/test_lab_rung.py` and `test_lab_luck.py`, and price in `lab/rung.py`
  with `c.line`: a research-list cell cannot be priced today. Then GRID drops `Cell.symbol`.

### Found, not fixed

- **The grid refuses runs of equal closes** (five+ for the RSI, twenty+ for Bollinger); the
  desk's engine decides those cells, only slower. Count them before the first pass.
- Deliberate breaks of the grid no series found can show: the Supertrend's band on the day's
  own close; a close against its day's upper band; the Bollinger check past 2**53; Wilder's
  smoothing as long as its window; the upper band's margin.
- The golden series are read from `tests/unit/test_strategy.py` (`GOLDEN`, `_walk`, `_jumpy`,
  `_bars`, `START`): if the money lane renames them, the two lanes move together.
- A helper's empty copy under `.claude/worktrees/` (branch `worktree-agent-ab11b126c53bfd69e`) can go.
- The unit of work: its key leaves out the Python version and file paths; no test drives a
  bar whose volume alone changed, or two bars on one day; a refused cell runs all five rules;
  a cell does not check its line is on the research list (no prices fails that cell loudly).
- The batch: no test sees each line forced to disk; nothing stops two processes on one
  journal (a lock is owed); bars hashed twice for a new cell; the journal only grows.

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
