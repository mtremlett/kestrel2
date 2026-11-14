# Status

**Read this first, then `docs/PLAN.md`, then run `python check.py`.**

Five lanes run side by side (`docs/PLAN.md`). The shared part below is changed only by a
session the operator starts himself; each lane writes only in its own section, so that
parallel pull requests never touch the same lines. A lane's section says where it is, its
next step, what it found and did not fix, and any question it holds for the operator.

## Shared

Last updated: 14 November 2026.

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
engine) and RUNGS (the ladder's rungs). Every lane runs on Fable until 97% of Fable's own
allowance is used or Fable refuses a session, then on Opus until a Fable reset (his ruling
at 20:12 on 13 November, which replaced the earlier 45%). A
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

Last updated: 14 November 2026 (the costs whole, the emergencies, the day's record).
### Where it is
Scenes 7 of 7. Built: the five rules; sizing, the one cost model (five lines), gate (`orders`); the
pretend broker; send path, ledger, book, reconciliation (`book`); the day (`day.trade`, `day.run`,
`day.publish`: the record to the penny in `records.csv`); the kill switch; `emergency` (EMG-01).

### Next step
SimCity small (money-simcity), halts, the gate's other limits, the money invariants.

### Done for other lanes

- R-PAPER-2: done in #64
- R-RUNGS-1: done in #101

### Requests to PAPER
- [ ] R-MONEY-7 (later, opened 2026-11-13 21:39 UK): a typed command calling `kill.pull`, sending
  `Killed.words()` to Telegram; with a supervised desk, one lock across the send path's last read.
- [ ] R-MONEY-8 (blocking, opened 2026-11-14 00:45 UK): the paper day calls `day.trade` (today, real
  data) and `day.publish`, never `day.run`; the adapter refuses an order not dated the session
  before the broker's today. Missed day: `book.record_rates`, `day.publish`.
- [ ] R-MONEY-9 (later, opened 2026-11-13 22:11 UK): a stop's fills get the order's id plus "-stop".
- [ ] R-MONEY-10 (later, opened 2026-11-13 22:11 UK): in conformance set paper fills beside
  `orders.charges` and the assumed 0.05% spread a leg; say if fills already carry the spread.
- [ ] R-MONEY-11 (later, opened 2026-11-14 00:20 UK): when you hold `desk/clearance.py`, say so; the
  ledger's writer `book._write` then becomes public (`book.write`).

### Requests to DATA
- [x] R-MONEY-2 (blocking, opened 2026-11-13 18:15): the scenes moved onto the fourteen months.
- [ ] R-MONEY-3 (later, opened 2026-11-13 18:15): a daily rate, pounds per dollar, in the store.
- [ ] R-MONEY-12 (later, opened 2026-11-13 22:56 UK): on the master, the lines standing for the
  market: the yardstick's twin (VUSA) and one trading in New York's hours.

### Requests to RUNGS
- [ ] R-MONEY-13 (later, opened 2026-11-13 22:11 UK): the first rung prices each leg with
  `orders.charges(line, leg, shares, price, fx)`; today it charges a sale as a purchase.
- [ ] R-MONEY-14 (later, opened 2026-11-14 00:20 UK): AG-04 must not add the records' market column
  (£783.73 added, £420.64 held): compound the days or read the two closes.

### Found, not fixed
- **No clock on the day path:** an old day with no record and no later fill is not known old (R-MONEY-8).
- **Costs:** spread and slippage assumed, not measured; fills carrying their own spread must not
  have it taken off twice (TRD-09); a stop's fill is known by name, not a typed word.
- **Records:** a withheld day shows twice if added; a damaged `records.csv` row is not named.
- **Emergencies:** one bad VUAG price could call for selling all (R-MONEY-12); market unread
  after London closes; 5QQQ can have no emergency.
- A sale can exceed the holding; nothing reads a declaration yet; a mismatch tells nobody yet;
  the day run has no halt. A helper's empty copy under `kestrel2\.claude\worktreesgent-a208b88dff47c8527` can go.

## PAPER

Last updated: 14 November 2026 (folds #100, #104, #110, #113).

### Where it is

Nothing placed on paper. The desk reads the account, the twenty lines, fills and orders; knows the Gateway's week
(`desk/gateway.py`); keeps a dated daily check (`desk/clearance.py`); and `desk/placing.py` answers all six broker
questions for a sale: refused unless line listed, kill switch drilled within 31 days, check clean, Gateway ready.

### Next step

paper-adapter's rest = paper-stops: a buy sent only with its stop (one stop for all shares held, on the price step);
a sale takes shares off it. Needs `desk/paper.py` to read a stop's level: do it under paper-adapter's claim, tick both.
Then paper-conformance. `Paper.place` raises NotImplementedError for a buy and for a sale on a line under the desk's stop.

### Requests to MONEY

- [ ] R-PAPER-4 (later, 2026-11-13 20:05): `book.differences` names an entry at no shares beside another carrying the shares.
- [ ] R-PAPER-5 (later, 2026-11-13 21:10): the ledger keys a fill by whole id; the broker's ".01" to ".02" would double it.
- [ ] R-PAPER-7 (later, 2026-11-13 22:45): one public keeper of dated records (the check borrows `book._write`, `_turn`).
- [ ] R-PAPER-8 (later, 2026-11-13 23:30): the day's run collects fills at day's end too (broker tells today only).
- [ ] R-PAPER-9 (later, 2026-11-13 23:30): word `Broker.stops` as the desk's own stops only, or say others are needed.
- [ ] R-PAPER-10 (later, 2026-11-14 00:30): when `place` raises other than "never received"/refusal, pull the kill switch
  or tell him at once? Today the day stops and the next start asks the broker.

### Requests to DATA

- [ ] R-PAPER-3 (later, 2026-11-13 18:55): each line's ISIN a fact on `Line`, confirmed from issuer/exchange.
- [ ] R-PAPER-6 (later, 2026-11-13 22:10): `desk/venues.py` gives a venue's wall clock publicly; `desk/gateway.py` drops its copy.

### Done for other lanes

- R-DATA-5: done in #53 (first half). Open: what the first London contract note says of stamp duty (conformance).
- R-MONEY-4: done in #75
- R-MONEY-5: done in #110
- R-MONEY-6: done in #113 (running the drill at each desk start is left to unattended running)

### Found, not fixed

- **Nobody sends his lines yet:** Sunday reminder and "his login" wait for the messenger; Sunday 15 Nov shows whether the
  Gateway stops answering at the weekend reset. A lasting "unwell" has no listener.
- **Nothing runs the day:** no caller of the check, `gateway.known` or daily fills; a clean check lasts the UTC day;
  a run at 00:00-01:00 UK summer is dated yesterday; a future-dated row refuses all orders.
- **Unseen on a real order:** open-order shape, cancel answers, refusal on entry, part fills, unasked news mid-reading.
- **Placing:** IDTL not found at the broker; no overall limit on the last-word wait or a conversation; an error after
  sending leaves the order as the broker has it; no account named; a stop's level never compared; a zero-share stop reads as agreeing.
- **Stale words:** `manifest.toml` says placing "is not built"; `desk/gateway.py` says "nothing calls it yet".
- **Unread at the broker:** hours, smallest order, order kinds; daily bars; SPCX's name; 2MU's step (£1 vs £5).
- **For a session he starts:** the live-port guard misses the desktop live port; breaks need Python's cache off.

## DATA

Last updated: 13 November 2026 (research reads the parked fifth; the next twelve boxes noted).

### Where it is

The twenty lines, one archive client, one store, both calendars to 2027, the research list (1,065:
864 clean, 201 parked by the store). Research reads all 1,065 through `universe.read` (#80): 21 cut at a
change of scale, 383 moves read as the market's, named in `History.moves`; the grid does not yet (R-DATA-7).

### Next step

Boxes noted for side-by-side sessions (#66): data-isa-twins, data-parked-fifth (open: R-DATA-7; five
tickers misjudged: WWH, SHC, ECHO, MRNA, ROR), data-fast-store, data-hours; then the keeper. Later: R-MONEY-3, R-PAPER-3.

### Done for other lanes
- R-MONEY-1: done in #47
- R-MONEY-2: done in #60

### Requests to GRID
- [ ] R-DATA-1 (later, opened 2026-11-13 18:15): a cell takes a `Line` from `universe.UNIVERSE` and
  reads `store.read(root / line.venue, line.symbol)`: thirteen symbols are two companies, by venue.
- [ ] R-DATA-7 (later, opened 2026-11-13 20:20 UK): with R-DATA-1, a cell reads
  `universe.read(root, line).bars`, not `store.read`, and keeps `History.moves` and `.rescaled`.

### Requests to MONEY
- [ ] R-DATA-3 (later, opened 2026-11-13 18:15): the day run reads the archive through
  `archive.gather` and hands `store.prepare` its answers whole, so a refused line parks with its reason.
- [x] R-DATA-4 (later, opened 2026-11-13 18:40 UK): each `Line(...)` in its tests states its UK tax.
- [ ] R-DATA-6 (later, opened 2026-11-13 19:20 UK): scene 5 reads `CLEAN`, now the one name for the
  whole rehearsal data; `HISTORY` is the same thing, and then goes.

### Requests to PAPER
- [x] R-DATA-5 (later, opened 2026-11-13 18:40 UK): each `Line(...)` in its tests states its UK tax.
- [ ] R-DATA-9 (later, opened 2026-11-13 20:20 UK): at `desk/paper.py`, a read-only question for a
  line's newest five-minute bars, and whether the paper account gets live market data or delayed.

### Requests to RUNGS
- [ ] R-DATA-8 (later, opened 2026-11-13 20:20 UK): a verdict states how many trades were held through
  a day in `History.moves` (about a hundred London bad prints), shown with and without them.

### Found, not fixed

- **UK tax (NS-05).** Five London products unseen on a contract note; London shares 0.5%, unchecked.
- **Parked of the twenty:** 3LGO, 2MU, 5QQQ, SGLN. The archive is free, unpaced (DAT-08).
- **The research list:** today's members only (BT-09), no kept home; scale changes under the store's
  belief are UNI-07; a crash won back next open cuts history (ROSE); raw answers unread.
- **The store:** nothing fills `Line.real_moves` or `.suspended`; a bad print under a hundredfold and a
  freeze under five sessions have no rule.

## GRID

Last updated: 13 November 2026 (the first pass run; a key per rung; the auto-tune).
### Where it is

Built and proven: the cell, the restart-safe batch, the fast grid engine, a key per rung
(`lab/cell.py`: costs move verdict keys, not trades'), the auto-tune (`lab/tune.py`: Windows
memory ceiling, workers sized to the cores, back-off, busy flag) and the pass (`lab/sweep.py`).
The first pass ran for real: 5,325 cells (1,065 tickers x 5 strategies) in 200 s, a second in 45 s.

### Next step

grid-week (seven days without stopping): needs a command of its own for the runner, a lock on
one folder of journals, a journal per worker, and failed cells not growing the journal each pass.

### Done for other lanes

- R-DATA-1: done in #73

### Requests to MONEY

- [ ] R-GRID-1 (later, opened 2026-11-13 18:15): the five rules at other settings in
  `desk/strategy.py`; the grid runs the published five until then (canon B2).

### Requests to RUNGS

- [ ] R-GRID-2 (later, opened 2026-11-13 20:04 UK): make each cell from a Line in
  `test_lab_rung.py`, `test_lab_luck.py`, and price in `lab/rung.py` with `c.line`. Then GRID drops `Cell.symbol`.
- [ ] R-GRID-3 (later, opened 2026-11-13 21:10 UK): stamp each verdict with `record.key.rung("lab.rung")`
  and each luck correction with `.rung("lab.luck")` in `lab/rung.py`; include the capital setting
  and exchange rate in what a kept verdict is found by. Needed before any verdict is kept.

### Requests to DATA

- [ ] R-GRID-4 (later, opened 2026-11-13 21:35 UK): a public "UK clock time of a moment" in
  `desk/venues.py`, so `lab/tune.py` drops its own summer-time rule.
- [ ] R-GRID-5 (later, opened 2026-11-13 22:20 UK): the research store's home (data-research-home)
  built on this PC (the first pass used a scratch copy); R-DATA-7's second half is still owed.

### Found, not fixed

- **The grid refuses runs of equal closes**; the desk's engine decides them, slower. Not yet counted.
- Grid breaks no series found can show: Supertrend's band on the day's close; Bollinger past 2**53;
  Wilder's smoothing as long as its window; the band's margin. Golden series live in `test_strategy.py`.
- Cell/batch: key leaves out Python version and paths; capital and exchange rate are in no key; no lock
  on a journal. Unit-test lines equal product lines (2,861): more test than product turns the check red.
- Tune: the proof uses one worker; priority and kill-on-exit untested; a worker that never finishes
  holds the pass; batch size follows only the last batch; the busy flag's write can fail.
- First pass: survivors only; refusals and run/kept/failed counts not logged. Scratch copies owed removal: `.claude/worktrees/` helpers, `C:	mp	unebreaks`, `C:	mp	unedriver`.

## RUNGS

Last updated: 14 November 2026 (cut to what is open; git, decisions and scoreboard keep the rest).

### Where it is

The ladder has its rungs, each proven on made-up prices only: the first (`lab/rung.py`: the
desk's one cost model, a day's rate for each fill, four answers - passed, failed, not enough
evidence, a fault in the test - and no verdict on code that is not the published rule,
`lab/published.py`); luck; folds; the register of trials; the deflated Sharpe with one
verdict rule; plateaus (`lab/plateau.py`); periods and regimes (`lab/regime.py`). **No winner
on real prices is to be believed yet.**

### Next step

Reproduce a published strategy's own result; then each indicator against a published
reference series (STR-14). Unit tests sit at the product's size (guard); keep them no longer.

### Requests to MONEY

None open (R-RUNGS-1, the sale's own cost: done in #101, used in #115).

### Requests to GRID

- [ ] R-RUNGS-2 (later, opened 2026-11-13 21:22 UK): the declared sweep enters every cell in
  the register (`trials.enter`) before the batch runs, at one fixed path in the data folder.
- [ ] R-RUNGS-4 (later, opened 2026-11-14 00:35 UK): a kept verdict's key should take in the
  rates it was priced with (with the capital, R-GRID-3).

### Requests to DATA

- [ ] R-RUNGS-3 (blocking, opened 2026-11-14 00:35 UK): a kept daily rate of pounds per dollar
  for every trading day of the research history (one per day, above nothing), readable as day
  to rate, so a dollar line can be judged.

### Found, not fixed

- **Nothing calls the new rungs yet**; rules carry no settings, nothing supplies the regime
  weather (REG-01). `luck.correct` is still a door beside the register, which has no lock or
  home path. Plateau and regime read pass or not only. The regime tag reaches paper only when
  promotion hands home regimes to the desk. Folds fail a one-regime specialist whose fold falls
  in its bad weather; the yearly Sharpe flag reads a regime's years from the whole window.
- **A verdict must not be kept by its record's key**: no rates, capital or `lab/rung.py` code.
- **Tests still make cells from a symbol** (R-GRID-2, half done). Spread and slippage are
  assumed figures, not measured on paper fills.
- **Smaller:** a fold-boundary trade counts in neither fold; a window of no days holding two
  trades divides by zero, unnamed; a line whose one share costs more than its room fails the
  whole verdict loudly; a rule changed under its old name is not a new trial; regime names
  differing only by capitals are two regimes; weathers tried per rule are the caller's count.
- **Unheld by a test (none can arise from real numbers):** the 5% line and the bar of 2, exactly.
