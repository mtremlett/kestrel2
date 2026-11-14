# Status

**Read this first, then `docs/PLAN.md`, then run `python check.py`.**

Five lanes run side by side (`docs/PLAN.md`). The shared part below is changed only by a
session the operator starts himself; each lane writes only in its own section, so that
parallel pull requests never touch the same lines. A lane's section says where it is, its
next step, what it found and did not fix, and any question it holds for the operator.

## Shared

Last updated: 14 November 2026.

### Where we are

Phase 2 under way. All seven scenes pass: scenes passing 7 of 7.

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
   on his own account now; on 14 November he said leave it for now. Ask again before going
   live.

### Found, not fixed

- **Two of the line limits are prose, not guards.** CLAUDE.md says its 80 lines and
  CANON.md its 200 are held by a guard; no test reads either, and CANON.md is 224 lines.
- **The runner's own lines to his phone wait for his key.** A lane that halts, pauses at
  the weekly cap or needs his decision, and the 07:00 line, are sent by the runner on his
  PC from a file holding the bot key, which he copies beside the runner himself. Until he
  does, they are written to the runner's log only.
- **A Windows Update restart overnight stops the lanes until he logs in.** The runner
  starts at his logon; starting it without one needs his password in Task Scheduler.
  His ruling of 14 November: no password; updates stay paused.
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
Scenes 7 of 7. Built: the five rules; sizing, cost model, gate (`orders`); pretend broker; send path,
ledger, book, reconciliation (`book`); the day (`day.trade`, `run`, `publish`); kill switch; `emergency`;
invariants (#132); SimCity (#134, `desk/simcity.py`): 51 parts censused, ten promises; **its night is RED**.

### Next step
money-working (the send path counts orders still working: six lines held against five; turns SimCity
green), money-restop, halts, the gate's other limits, then fills (money-fills). Boxes adding a public
function need the SimCity files (a function no scenario runs turns the check red).

### Done for other lanes
- R-PAPER-2: done in #64
- R-RUNGS-1: done in #101

### Requests to PAPER
- [ ] R-MONEY-7 (later, 2026-11-13): a typed command calling `kill.pull`, sending `Killed.words()` to
  Telegram; with a supervised desk, one lock across the send path's last read.
- [ ] R-MONEY-8 (blocking, 2026-11-14): the paper day calls `day.trade` (today, real data) and
  `day.publish`, never `day.run`; the adapter refuses an order not dated the session before the
  broker's today. Missed day: `book.record_rates`, `day.publish`.
- [ ] R-MONEY-9 (later): a stop's fills get the order's id plus "-stop". R-MONEY-10 (later): in
  conformance set paper fills beside `orders.charges` and the assumed 0.05% spread; say if fills carry it.
- [ ] R-MONEY-11 (later, 2026-11-14): when you hold `desk/clearance.py`, say so; `book._write` then goes public.
- [ ] R-MONEY-15 (blocking, opened 2026-11-14 03:30 UK): no unattended paper order until the send path
  counts orders still working (money-working); the adapter must then say which are working.

### Requests to DATA
- [x] R-MONEY-2 (blocking, opened 2026-11-13 18:15): the scenes moved onto the fourteen months.
- [ ] R-MONEY-3 (later): a daily rate, pounds per dollar, in the store. R-MONEY-16 (later, 2026-11-14):
  rehearsal lines not all one shape, so the 50/200-day rule holds a line.
- [ ] R-MONEY-12 (later, 2026-11-13): on the master, the market's lines: the yardstick's twin (VUSA), one in New York hours.

### Requests to RUNGS
- [ ] R-MONEY-13 (later): the first rung prices each leg with `orders.charges`; today a sale is charged as a purchase.
- [ ] R-MONEY-14 (later, 2026-11-14): AG-04 must not add the records' market column (£783.73 added,
  £420.64 held): compound the days or read the two closes.

### Found, not fixed
- **No clock on the day path:** an old day with no record and no later fill is not known old (R-MONEY-8).
- **Costs:** spread and slippage assumed; fills carrying their own spread must not have it taken off
  twice (TRD-09); a stop's fill is known by name. **Records:** a withheld day shows twice if added.
- **Emergencies:** one bad VUAG price could call for selling all (R-MONEY-12); 5QQQ can have none.
- **Pretend broker:** no fault reaches a sale or fills in two executions; order state is untyped.
- **SimCity (#134):** a stop cancelled by hand is never put back (money-restop); no nightly run on his PC
  yet; no code or data version in its record.
- A sale can exceed the holding; nothing reads a declaration yet; a mismatch tells nobody yet; no halt.

## PAPER

Last updated: 14 November 2026 (folds #100, #104, #110, #113, #123, #128, #135).

### Where it is

First real paper orders sent 14 Nov (#135), markets shut: one share with its stop on every line (59 orders), all cancelled,
nothing bought. Proven: buy+stop, stop step/unit on 19 lines, cancel, refusal, lone stop, kill switch. No fill seen. Nothing constructs the adapter in the product yet.

### Next step

Order: paper-conformance in-hours half (fills, triggered stop, sale, part fill, SPY in hours; needs open markets; record and
driver in KESTREL2_DATA/conformance; out of hours take R-MONEY-8), then supervision, main's code, cards.

### Requests to MONEY

- [ ] R-PAPER-4 (later, 2026-11-13 20:05): `book.differences` names an entry at no shares beside another carrying the shares.
- [ ] R-PAPER-5 (later, 2026-11-13 21:10): the ledger keys a fill by whole id; the broker's ".01" to ".02" would double it.
- [ ] R-PAPER-7 (later, 2026-11-13 22:45): one public keeper of dated records (the check borrows `book._write`, `_turn`).
- [ ] R-PAPER-8 (later, 2026-11-13 23:30): the day's run collects fills at day's end too (broker tells today only).
- [ ] R-PAPER-9 (later, 2026-11-13 23:30): word `Broker.stops` as the desk's own stops only, or say others are needed.
- [ ] R-PAPER-10 (later, 2026-11-14 00:30): when `place` raises other than "never received"/refusal, pull the kill switch or tell him at once?
- [ ] R-PAPER-11 (later, 2026-11-14 01:25): `place` can raise "word, fills and account do not agree" after an order has gone; should the send path tell him at once and stop buying?
- [ ] R-PAPER-12 (later, 2026-11-14 01:25): word "a sale takes its shares off that stop" to allow two steps, or say if the pretend broker must.
- [ ] R-PAPER-13 (later, 2026-11-14 02:50): the pretend broker refuses a repeated order id; the real one took it as new. Make it so, or `place` must refuse.
- [ ] R-PAPER-14 (later, 2026-11-14 02:50): no buy on a line with `Line.retail` False (SPY, QQQ); the broker refuses them, 15 s each, daily.
- [ ] R-PAPER-15 (later, 2026-11-14 02:50): a working buy has its stop listed at the real broker, so `book.reconcile` names the line; pretend has none. Match it, or `Broker.stops` leaves it out.

### Requests to DATA

- [ ] R-PAPER-3 (later, 2026-11-13 18:55): each line's ISIN a fact on `Line`, confirmed from issuer/exchange.
- [ ] R-PAPER-6 (later, 2026-11-13 22:10): `desk/venues.py` gives a venue's wall clock publicly; `desk/gateway.py` drops its copy.
- [ ] R-PAPER-16 (later, 2026-11-14 02:50): IDTL in dollars is unlisted at the broker (needs its name or ISIN, with R-PAPER-3); SPY, QQQ can leave the lines.

### Done for other lanes
- R-DATA-5: done in #53 (first half). Open: what the first London contract note says of stamp duty (conformance).
- R-MONEY-4: done in #75; R-MONEY-5: done in #110
- R-MONEY-6: done in #113 (running the drill at each desk start is left to unattended running)

### Found, not fixed

- **Nobody sends his lines yet**; Sunday 15 Nov shows the weekend reset. **Nothing runs the day**: a run at 00:00-01:00 UK
  summer is dated yesterday; a future-dated row refuses all orders.
- **Unseen at the real Gateway (needs open markets):** a fill (shape, clock, fee, lag), a triggered stop, a sale taking shares
  off the stop, a part fill, the stop behind a part-filled buy; a just-filled buy told again could carry a reason on a whole fill. Whether the weekend reset keeps the day's orders: Sunday.
- **A refused order costs 15 s** (broker says "Inactive", then the reason; the desk waits out silence). A lone refused stop gives an error, not the reason. Unasked open orders arrive before "ready"; if one came after, a reading could miss another program's order.
- **After an error part-way through an order nothing settles the line again** (reuse `Paper._settle`); a false alarm or rare silent pass.
- **Placing:** no overall time limit; the kill switch cancels a buy, not its stop.
- **Stale words:** `manifest.toml` says placing "is not built"; `desk/gateway.py` says "nothing calls it yet". Unread at the broker: hours, smallest order, order kinds; 2MU's step (£1 vs £5). Live-port guard misses the desktop port.

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

Last updated: 14 November 2026 (the grid's week built, started and moved onto its fix).
### Where it is

Built and proven: the cell, the batch, the fast grid engine, a key per rung, the auto-tune
(`lab/tune.py`), the pass and the hourly week (`lab/sweep.py`). A pass: 5,325 cells in 2 to 4 min.

### Next step

grid-week: the seven-day run is going (pid in `C:\tmp\kestrel2_week\pid.txt`). Nothing to build. On or after
20 Nov 23:45 UK read `sweep.unbroken(Path(KESTREL2_DATA))`: 7 days ticks it. If it died, restart within the hour:
`python -B -m lab.sweep C:\tmp\kestrel2_grid\store %KESTREL2_DATA%\grid\cells %KESTREL2_DATA% --days 7`
from `C:\tmp\kestrel2_week\code`. grid-declared can start now (it waited only on the shared file).

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
- Grid breaks no series found can show (Supertrend band, Bollinger past 2**53, Wilder window, band margin).
- Cell/batch: key leaves out Python version, paths, capital and exchange rate. Unit-test lines equal product lines.
- Tune: the proof uses one worker; priority and kill-on-exit untested; batch size follows the last batch only.
- Week: no limit on a pass's time; a torn `week.jsonl` line needs hand-mending; results grow ~9 MB a day
  (pruning owed, R-GRID-1); an outside pass on the same folder, a PC restart not followed within the hour,
  or the scratch store `C:\tmp\kestrel2_grid\store` cleared breaks the run (data-research-home fixes the last).
- Log counts tickers as "cells"; refused cells uncounted; busy flag stale if a pass is killed outright.
  Scratch copies owed removal: `.claude/worktrees/` helpers, `C:\tmp\unebreaks`, `C:\tmp\unedriver`.

## RUNGS

Last updated: 14 November 2026 (cut to what is open; git, decisions and scoreboard keep the rest).
### Where it is

Rungs proven on made-up prices only: first (`lab/rung.py`), luck, folds, trials, deflated Sharpe, plateaus,
regimes; built but called by nothing yet: author's result (`reproduce`), promotion, market rung, book
concentration (`bets`, #136), stress (`stress`, #140), indicator tables (`published`, #145, #154: 250 numbers).
The first rung refuses a rule with an author's figure on file until reproduced (#139).
**No winner on real prices is to be believed yet; no real author's figure is on file.**

### Next step

Open boxes (PLAN): rungs-trustworthy (name market rung; wire bets, stress), rungs-indicators (R-RUNGS-6, 12).
**rungs-reproduce is BLOCKED, hand it out no more** (#143, #149): waits on the book (his spend; recommended
yes, Connors and Alvarez 2008; its RSI table may be of another rule), R-RUNGS-5, R-RUNGS-10. Free: Connors'
"RSI 25" figure, uncoded. Unit tests stay at the product's size. Ruled 14 Nov (DECISIONS):
concentration shown on every report, no A-GATE mark yet; no book for now.

### Requests to MONEY

- [ ] R-RUNGS-6 (blocking, 01:20): the indicators of `desk/strategy.py` public and by name (STR-14).
- [ ] R-RUNGS-12 (blocking, 07:55): narrows R-RUNGS-6 to a public RSI and Bollinger lower band; keep `_Window`,
  `_Wilder`, `_Rsi2`, `_Supertrend`, `_gain`, `_loss`, `_range` meanwhile.
- [ ] R-RUNGS-7 (later, 01:50): the day's run reads each candidate's `promotion.standing`, buys nothing for a killed one.
- [ ] R-RUNGS-8 (later, 01:50): `orders.strategy_of` refuses an unreadable id, naming it.
- [ ] R-RUNGS-10 (later, 04:50): Connors' Double 7's as a desk rule (first reproduction's rule).
- [ ] R-RUNGS-11 (later, 04:48): the gap loss limit (STP-10) one named number in `desk/orders.py`.

### Requests to GRID

- [ ] R-RUNGS-2 (later, 13 Nov): the declared sweep enters every cell in the register before the batch runs.
- [ ] R-RUNGS-4 (later, 00:35): a kept verdict's key takes in the rates it was priced with.

### Requests to DATA

- [ ] R-RUNGS-3 (blocking, 00:35): a kept daily pounds-per-dollar rate for every research day.
- [ ] R-RUNGS-5 (blocking, 01:20): SPY and US sessions back to January 1993, saying if dividend-adjusted.
- [ ] R-RUNGS-9 (blocking, 04:50): with R-RUNGS-5, SPY from 29 Jan 1993 kept as traded and adjusted, labelled.

### Found, not fixed

- **Nothing calls the new rungs yet**; no settings on rules, no regime weather (REG-01); `luck.correct` is a
  door beside the register. **Reproduction:** `folds.judge`, `regime.judge` cannot pass one on; Bollinger,
  50/200 cross, Supertrend have no author's test (ruling owed); Double 7's figure not on file.
- **Promotion:** fall sees sold shares only; `DEEPEST` belongs to the A-GATE. **Market/stress:** calm-storm
  alternation passes a rider twice as often; "days end at first unjudged trade" lives twice, belongs in `rung.py`.
- **Bets:** a young line (<120 moves) stops it; clusters near 0.5 flip year to year. **Indicators:**
  `published.py` at its 400-line cap; RSI ratio, band line, carried band unheld; tables run flat only;
  no fresh-low table for the channel. Scratch owed removal in `C:/tmp`: repro*, promo*, market*, bets*, rungs*, ind*.
