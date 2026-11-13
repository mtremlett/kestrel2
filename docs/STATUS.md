# Status

**Read this first, then `docs/PLAN.md`, then run `python check.py`.**

Five lanes run side by side (`docs/PLAN.md`). The shared part below is changed only by a
session the operator starts himself; each lane writes only in its own section, so that
parallel pull requests never touch the same lines. A lane's section says where it is, its
next step, what it found and did not fix, and any question it holds for the operator.

## Shared

Last updated: 13 November 2026.

### Where we are

Phase 2, with phase 3 begun alongside it by his ruling; the scenes count is in
`docs/PLAN.md`. Five lanes (MONEY, PAPER, DATA, GRID, RUNGS) run day and night on his PC,
each a chain of sessions started by a runner outside this repository, inside his plan's
included usage and stopping at 80% of its week. GitHub merges a pull request only when its
check is green and its branch holds all of main. Each merge sends him one Telegram line;
the runner adds a 07:00 line, an independent audit at 05:30, and a line whenever a lane
stops, stalls or needs him (`docs/DECISIONS.md`). This file keeps what is open: a fixed
item is removed, and git keeps it.

### Open questions for the operator

1. **A second GitHub account** for sessions to work through, so that the guards cannot be
   removed by the account that enforces them. He chose to start on his own account; open.

### Found, not fixed

- **CANON.md's 200-line limit is prose:** it is 224 lines, and no test holds it.
- **A Windows Update restart overnight stops the lanes until he logs in.** Starting the
  runner without a logon needs his password in Task Scheduler: his call. He pauses updates.
- **The lane guard judges whole files:** that a lane writes only in its own section of a
  shared document is checked by the daily audit alone.
- **A newer ruff calls the tree badly formatted:** run the check in the environment built
  from `requirements.txt`; the check does not say which tool versions it ran with.
- **The scenes rule trusts the error's name:** a test raising NotImplementedError itself
  would pass as unbuilt. None does; nothing checks that none does.
- **Unit tests sit within a few lines of the product's size**, and two lanes green alone
  can be red together (#28): each lane's next test needs as much product, or a test merged.

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

Last updated: 13 November 2026 (the unit of work on the grid engine).

### Where it is

Built and proven: the ladder's unit of work (`lab/cell.py`: one strategy on one line over a
window, the days each trade was bought and sold, keyed by its code and its bars), the batch
service that survives a bad cell and a restart and re-runs only what changed
(`lab/batch.py`), and the fast grid engine (`lab/grid.py`), which holds what the desk's
engine holds after every bar or refuses by name (`TooClose`). The unit of work now runs on
the grid: a cell's trades are the grid's answer, and the desk's own engine's wherever the
grid refuses, the same record either way. A cell on 4,000 days takes about 25 ms, against
the desk's engine's 95 ms. No price or profit is named.

### Next step

R-DATA-1: a cell takes a `Line` of the research list and reads its venue's folder. Then
auto-tune, so a pass can never take the PC down.

### Requests to MONEY

- [ ] R-GRID-1 (later, opened 2026-11-13 18:15): the five rules made at other settings (window
  lengths, the RSI's bar, the bands' widths) in `desk/strategy.py`. The grid's first pass is
  "every setting", and the grid is trusted only where it matches the desk's engine (canon
  B2); until then it runs at the published five only.

### Found, not fixed

- **The grid refuses runs of equal closes**: five or more for the RSI, twenty or more for
  Bollinger. The desk's engine decides those cells: right, only slower. Count them on the
  research universe before the first pass. The Supertrend and the RSI still walk the days.
- Deliberate breaks of the grid no series found can show: the Supertrend's band carried on
  the day's own close; a close against its own day's upper band; the Bollinger check past
  2**53; Wilder's smoothing on a series as long as its window; the upper band's margin.
- The golden series are read from the money lane's `tests/unit/test_strategy.py` (`GOLDEN`,
  `_walk`, `_jumpy`, `_bars`, `START`): if it renames them, the two lanes move together.
- A helper's empty working copy sits under `.claude/worktrees/` of the operator's main
  folder, with branch `worktree-agent-ab11b126c53bfd69e`. It can be deleted.
- The unit of work: its key leaves out the Python version and file paths; no test drives a
  bar whose volume alone changed, or two bars on one day; each cell reads its line's prices
  in again (17 of its 25 ms); a refused cell runs all five of the desk's rules to keep one.
- Blind review of the cell on the grid, nothing blocking: an infinite or not-a-number price
  fails the cell loudly (the store should pass none); a negative price could weaken the
  grid's refusal (no line has one); the desk's turn is tested on whole windows only.
- The batch: no test sees each line forced to disk (`os.fsync`); nothing stops two
  processes on one journal (a lock is owed before anything but a person starts it); a
  corrupt journal line names neither file nor line; bars are hashed twice for a new cell;
  the journal only grows. Research over years will meet gaps the store no longer parks.

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
