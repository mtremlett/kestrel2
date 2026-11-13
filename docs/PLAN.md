# The plan

**Current objective:** the money lane's — the kill switch and its drill (his ruling: first);
then the costs whole, then the day's record, with which scenes 6 and 7 pass together.

Scenes passing: **5 of 7**. Phase: **2-money-sim**.

The two lines above belong to the money lane: it alone moves the scenes count. The other
lanes' objectives are in their own books below. The operator's Telegram line
reads the ticked boxes under each `## Phase N` heading, so each lane's book sits inside its
phase.

---

## The five lanes

Five chains of sessions run side by side on the operator's PC, day and night, each session
starting when the one before it ends (his rulings, 13 November 2026, `docs/DECISIONS.md`).
A lane's session works on its lane's objective only, edits only the files its lane owns,
and writes only in its lane's parts of the shared documents: its section of
`docs/STATUS.md`, its book here, its table in `docs/SCOREBOARD.md` and its part at the end
of `docs/DECISIONS.md`. Each lane's book sits inside the phase it belongs to: DATA in
phase 1, MONEY in phase 2, PAPER in phase 3 (begun alongside phase 2, his ruling), GRID
and RUNGS in phase 4. So two lanes' pull requests never touch the same lines, and GitHub
merges neither until it holds the other.

| lane | owns |
|---|---|
| MONEY | `desk/strategy.py`, `orders.py`, `broker.py`, `book.py`, `day.py`; `tests/scenes/test_scenes.py`; their unit tests |
| PAPER | the paper-broker modules it registers in `desk/`; their unit tests |
| DATA | `desk/lines.py`, `venues.py`, `archive.py`, `store.py`, and the research list it registers; `tests/scenes/rehearsal.py`; their unit tests |
| GRID | `lab/cell.py`, `lab/batch.py` and the grid engine it registers; their `tests/unit/test_lab_*.py` |
| RUNGS | `lab/rung.py` and the rungs it registers; their `tests/unit/test_lab_*.py` |

The table is a summary; `manifest.toml` is the source the check enforces (its `[lanes]`
table, and each lane's heading over its modules). A lane's branch that changes any other
file fails the check (`tests/guards/test_lanes.py`), and no change adds more than 300 net
lines to `desk/` and `lab/` together.

**A lane that needs another lane's file changed does not touch it.** It writes a numbered
request in its own STATUS section, under `### Requests to <LANE>`:
`- [ ] R-<ITS LANE>-<n> (blocking|later, opened YYYY-MM-DD HH:MM): what is needed and why`.
The owning lane records `- R-<LANE>-<n>: done in #NN` (or `declined, because ...`) under
`### Done for other lanes` in its own section, and the asker then ticks its request. The
runner puts each lane's open requests at the top of its next session; a blocking one is
that session's objective, before its own book. The 07:00 line counts the open requests,
and one open for more than a day is sent to the operator.

A new module is registered in `manifest.toml` under its lane's heading. A file no lane owns
(`check.py`, `announce.py`, the guards, `BUDGET.json`, `CLAUDE.md`, `CANON.md`,
`docs/SCENES.md`, `docs/FAILURE_PATTERNS.md`, the shared parts of the documents) is changed
only by a session the operator starts himself. A lane that needs one changed, or finds a
new recurring failure, writes it in its STATUS section and carries on with what it can.

---

## Phase 0 — foundations

The machinery that refuses, before any desk code.

- [x] Repository created, public, with main protected on GitHub
- [x] Direct push to main proven to be refused
- [x] The one check: format, lint, strict types, guards
- [x] Twelve guards, each driven against a deliberate violation
- [x] GitHub runs the check on a clean machine with no access to the operator's PC
- [x] A phase-by-phase size ceiling, and a module manifest that walls the core
- [ ] The documents: this one, the canon, the scenes, the architecture
- [x] The scenes approved by the operator
- [x] The scenes written as failing tests
- [ ] A git hook running the fast check before each commit
- [ ] An independent reviewer that never sees the reasoning
- [x] One Telegram line to the operator for each change that lands on main (his request,
      13 November: he follows progress without reading GitHub)
- [ ] Standing guards still owed, each built by a session he starts (the spec's NOW rows):
      a secret scan on every change (OPS-11); a number with a second home caught (CODE-04);
      dead modules and duplicates caught (TST-11); a stale green treated as red (GOV-13);
      the deliberate breaks automated as mutation tests on the money path (TST-20)

## Phase 1 — data

One store, one writer, cleaned on entry.

- [x] The twenty lines chosen and in the instrument master (his ruling, 13 November)
- [x] Daily bars for the twenty lines, from a free archive, re-fetched and re-checked:
      sixteen clean, four parked with named reasons (`docs/STATUS.md`)
- [x] Cleaning on entry: units, duplicates, gaps, impossible prices; a split the archive
      did not adjust parks the line, it is not adjusted
- [x] Market calendars per venue; a UK holiday is not a US holiday (2010 to 2027)
- [x] Parking a bad line, with a reason, a date and a way back out
- [x] **Scene 1 passes**

### The data lane's book — the research universe first, then the parked lines and the store's findings

**Lane objective:** the research list's parked fifth. The list is built and fetched (1,065
tickers: the S&P 500, the Nasdaq 100, the FTSE 350 and 200 most-traded US funds, daily since
2010, through the one store's checks, apart from the twenty trading lines), and 201 of them
park for a large one-day move nobody has recorded, most on real days of a real market.
Decide and build how research reads them, without loosening the store the desk trades on.
The grid lane needs it.

- [x] The rehearsal data in a file of its own (`tests/scenes/rehearsal.py`)
- [x] The rehearsal data lengthened to about fourteen months, the five rules buying and
      selling in it on every clean line, its UK and US holidays respected; the spoilt line's
      faults kept within the last sixty sessions (`docs/DECISIONS.md`, the data lane's)
- [ ] The scenes moved onto the whole fourteen months (`SCENES_FROM` back to `FIRST`), once
      the money lane's scene 2 counts each line's own sessions; until then they see its
      last six weeks
- [x] One line the archive refuses is parked, not the whole fetch stopped (`archive.gather`, `store.Refused`)
- [x] The research list: 1,065 tickers with their venue and currency (the four lists
      overlap, so not 1,500), kept apart from the instrument master's twenty trading lines;
      being on it makes nothing tradable (`lab/universe.py`)
- [x] The research list's daily bars since 2010, fetched and kept through the one store's
      checks, a bad ticker parked with its reason (`universe.keep`): 864 clean, 201 parked
- [ ] The research list's parked fifth: 201 tickers' large one-day moves confirmed, or a
      rule for research that needs no confirmation
- [ ] The archive spared: fetching slow and resumable, with backoff, each raw answer cached
      in the folder `KESTREL2_DATA` names (outside the repository and every worktree); while
      the archive refuses, `{"refusing_since": <time>}` written to `KESTREL2_DATA/archive.json`
      (null once it answers), so the runner tells the operator after six hours, and other work
      done meanwhile rather than retrying
- [ ] A home for the research store on his PC, refreshed nightly, a ticker that left a list
      cleared out, and the day and list it reflects written beside it
- [ ] The lists' members year by year, so a study of the past is not the survivors' alone
- [ ] The full research universe, 5,000 and more, once the grid's first pass works
- [ ] 2MU's five real moves recorded from a second source, or its reason confirmed
- [ ] 5QQQ's consolidation of 22 August 2024 handled, or its reason confirmed
- [ ] SGLN's garbled weeks of 2011 handled, or its reason confirmed
- [ ] 3LGO's missing history, and a rule for when enough has gathered
- [x] A frozen feed: a week of one bar repeated is dropped and parks a recent line
- [x] A suspension recorded on its line is no gap
- [x] A one-day crash is kept and parks until recorded; only a hundredfold bar is a wrong unit
- [ ] A stretched bar's changes recorded beside it
- [ ] A line's bars and its fault record written together, so a crash cannot part them
- [ ] The window before mid-April 2010 prepared
- [ ] A pence history the archive calls pounds caught
- [ ] The calendars carried past 2027, before 2027 ends
- [ ] **First, by his ruling of 13 November:** SPY, QQQ and GLD leave the twenty for their
      UK-listed twins an ISA can hold: VUAG (S&P 500), EQQQ (Nasdaq 100) and IDTL (US
      Treasuries 20+ years), each on the London venue; every line carries an ISA and
      retail-buyable flag; the "simply holding the market" yardstick re-pointed (UNI-09)
- [ ] Polite fetching: the archive's limits measured, slow and resumable requests, backing
      off on refusals, raw responses cached, an alert after six hours refused (DAT-08)
- [ ] Coverage and quality measured: history at least twice the longest lookback for every
      line, five years by the A-GATE; a quality score per line and desk-wide, and a cap on
      the share of lines parked (DAT-03, DQ-01)
- [ ] A second source: a gap filled and a failing feed replaced from a ranked second
      source, with a staleness alarm and a register of sources; the twenty lines' bars
      checked against the broker's price of record each day once PAPER connects (DQ-03,
      DAT-07, DAT-01, DAT-02)
- [ ] The store's keeper: its cadence, a dated receipt for each run, a restart drill; each
      bar's source and arrival time kept (DQ-12, DQ-10)
- [ ] Half-days and auction times in the calendars (DQ-11)
- [ ] Dividends and corporate actions: total-return history for the ladder, the paper
      profit and the hold-the-market yardstick (UNI-07)
- [ ] Survivorship: the research list taken as it stood on each past date, with the names
      that left it, or the bias measured and stated on every verdict (BT-09)
- [ ] UK stamp duty and taxes confirmed line by line, in one table by instrument type
      (NS-05)
- [ ] Leveraged-product lifecycle watched: an issuer's closure, a compulsory redemption or
      an ISA eligibility change on any line held or researched raises an alert (BIC-11)
- [ ] Disk watched; old research files roll off by rule (OPS-07)

## Phase 2 — the money path, in simulation

- [x] One strategy template; the five frozen daily strategies (his choice: five textbook
      rules, 13 November) - **scene 2 passes**
- [x] Sizing from one capital number; stops set at entry; a leveraged line sized by what
      it controls (his rulings, 13 November: a fifth each, a stop where the market has
      fallen 10%) - **scene 3 passes**
- [ ] **Scenes 2 to 7 pass in simulation**, by the money lane's book below; the data
      lane's lengthened rehearsal data (phase 1) comes first

### The money lane's book — scenes 4 to 7, in order

**Lane objective:** the kill switch, by his ruling of 13 November ("kill switch first"):
one command stops all new orders and cancels the open ones, the desk says so, and the drill
is run against the pretend broker (the step below, EMG-02). The paper lane sends no order
until it is drilled. After it, in order: the costs whole in the desk's one cost model
(`desk/orders.py`): what a sale itself costs, and spread and slippage on both legs, the
stop's sale included, each a stated assumption recorded in `docs/DECISIONS.md`; the rungs
lane waits for them too. Then the day's record (`day.run`), once the data lane has put
each line's UK tax on the line: scenes 6 and 7 read the same record, so they pass together
(`docs/DECISIONS.md`, the money lane's). The pretend broker, the send path, the book, the
day's trading and reconciliation are built.

- [x] The pretend broker: fills at the day's prices, rejects, partial fills, disconnection,
      a crash, resting stops, positions, and a position injected behind the desk's back
- [x] The send path: every order through the one gate, sent once however often the desk
      restarts, its fills recorded under the broker's ids - **scene 4 passes**
- [x] The book built from the broker: what is held and what is left, so the gate enforces
      at most five holdings and two buys of one line share one fifth
- [x] The day run: decisions dated that day only, a rule's position read from the book,
      round trips with commission and conversion - **scene 5 passes** (on the fourteen
      months; spread, slippage and UK tax come with the day record)
- [x] Reconciliation, before every order: the desk's book against the broker's positions
      and resting stops, each line that differs named; nothing bought, and no such line
      sold, while they differ (`book.reconcile`, on the send path)
- [ ] The costs whole: a sale's own cost, and spread and slippage on both legs, the stop's
      sale included, in the one cost model; UK tax from a fact on each line (asked of the
      data lane)
- [ ] The day's record (`day.run`): the day reconciled at its end, a mismatch named and its
      profit withheld; else the profit after every cost line, to one rounding policy, beside
      what holding the market earned; the same days replayed to the same records. Scene 6's
      days moved onto the fourteen months, its book checked against the broker's every day -
      **scenes 6 and 7 pass**
- [ ] SimCity, small: one command runs the whole desk's day over all fourteen months of
      rehearsal data against the pretend broker with its faults, every night, and writes one
      record; a census names every part of the money path and turns red when one has no
      scenario
- [ ] **The kill switch, before the paper lane sends any order:** one command stops all new
      orders and cancels the open ones, and the desk says so; drilled before FIRST-LIGHT's
      first day and then monthly (EMG-02, canon B1)
- [ ] Emergencies in numbers: an emergency, a crash and a black swan each defined by
      measured falls, each with its action (EMG-01)
- [ ] Halts: a halt is a typed record; while one is in force the desk buys nothing and
      says so every day until it is lifted, and the day's verdict reads it; each morning
      one list of every blocker and every signal it blocked (FIL-08, NS-06, FIL-04, TRD-01)
- [ ] The gate's other limits from canon B1: a day's and a week's loss and an order rate,
      refused at the gate (EMG-04 when live)
- [ ] A position the desk did not make is named and then sold on paper (TRD-06); no signal
      is left half-processed at the day's end (TST-08)
- [ ] Each strategy's declaration typed: its bar, holding period, test universe and data;
      a short sale cannot be built at all (STR-03, STR-06)
- [ ] SimCity widened: a hundred seeded worlds with faults and drills, not one rehearsal
      world (TST-05, TST-22)
- [ ] Small and illiquid trades: a trade whose expected gain is under twice its round-trip
      cost is flagged, and no position is above 1% of its line's twenty-day traded value
      (SIZ-10, TRD-10)
- [ ] Time and gaps: a time stop after the strategy's declared holding period; a gap that
      jumps the stop held against the loss limit; a hold limit and gap sizing for the
      leveraged lines (STP-11, STP-10, SIZ-09)
- [ ] Fills realistic: spread and slippage in every fill, from the one cost model (TRD-09)
- [ ] The money invariants property-tested, seeded: positions equal the sum of fills,
      equity equals cash plus market value, profit equals realised plus unrealised less
      costs, orders move only through valid states, sending is idempotent (TST-04, canon B4)
- [ ] The golden reference run committed; a change to a size, a stop or a threshold is
      replayed on it before it lands (TST-21, GOV-09, canon B5)
- [ ] Every trade's whole story: signal, intent, risk decision, order, fill and the bar it
      read, linked by ids; profit attributed by strategy, line, holding time and cost
      (TRD-11, TRD-12, DQ-08)
- [ ] Money honestly counted: interest on idle cash, with the risk-free rate in every
      Sharpe; currency gains and losses on dollar holdings reported apart from trading
      profit; a fall from the book's highest point alerted on paper (BIC-03, BIC-04, BIC-05)

## Phase 3 — the money path, on paper

Begun alongside phase 2 by his ruling of 13 November: "Five lanes, phase 3 now".

- [ ] **FIRST-LIGHT: ten consecutive clean trading days**

### The paper lane's book

**Lane objective:** the real paper-broker adapter behind the same interface as
`broker.Pretend`, in `desk/paper.py` with the standard library alone, built from what it
reads towards what it sends: first each of the twenty lines as the broker knows it (its
name, exchange and price step there), then the fills and orders the broker reports, then
placing. It sends no order until that day's read-only check (`paper.mismatches`) has come
back clean, and the check has been taught the desk's own resting stops. The account is the
old desk's (his ruling, 13 November), reached through IB Gateway's paper port 4002 on his
PC with the desk's own client id (222), never 4001.

- [ ] The Gateway known before any order: its daily restart and the weekly re-login handled
      unattended. A re-login that needs his phone or password is his: a reminder line at the
      right time, never a workaround. The old desk's gateway alarms are a quarry only. (The
      runner already watches port 4002 and the account, read-only, and tells him when it stops
      answering.)
- [x] The read-only check of the paper account's positions and open orders against the
      desk's book, every mismatch named (`desk/paper.py`); run on the real account on 13
      November: quiet, no shares held and no order resting
- [ ] The check run every day and before any order: the adapter refuses to send until
      that day's check is clean, and tells the desk's own resting stops from anyone else's
- [ ] The real paper-broker adapter behind the same interface as `broker.Pretend`, speaking
      to IB Gateway with the standard library alone (`desk/` imports nothing else)
- [ ] Stops resting at the broker, each rounded down to its line's price step
- [ ] Conformance trades, on paper, one London and one US line, each in its market's hours:
      a market buy at the open; the resting stop placed, triggered, and cancelled on a sale;
      a partial fill if the paper broker gives one; a rejection. Each real result recorded
      beside the pretend broker's, and the pretend broker fixed where they differ
- [ ] Unattended running, and recovery from a restart
- [ ] Morning and evening messages, and an alarm on silence
- [ ] **No paper order until the money lane's kill switch has been drilled** (EMG-02)
- [ ] The desk's own process supervised: one supervisor, restarts proven by killing it,
      health judged from outside by dated receipts, surviving a reboot, a dropped network
      and a broker disconnect; a ledger of operator actions proving seven days without one,
      bar the ruled Gateway re-login (OPS-01, OPS-02, OPS-04, OPS-10, NS-01)
- [ ] The running process always on main's latest code, and a money-path change reaching
      it only at a safe point, never mid-send (OPS-05, OPS-16)
- [ ] The messages: a start-of-day card by 05:40; an end-of-day summary with the profit,
      the streak and the verdict; a line on every change of state and "the desk is not
      trading" by 09:30 UK; urgency levels without storms; one messenger with a delivery
      record, the merge line and the runner's alerts behind the same door (MSG-02, MSG-03,
      MSG-04, MSG-09, MSG-11)
- [ ] The day's extras: missed winners, blocked signals, and the running cost set against
      net profit each week (MSG-13, NS-14)
- [ ] FIRST-LIGHT counted by the desk itself: ten consecutive clean days, and a day that
      sent nothing cannot be green (NS-10)
- [ ] An independent watcher of the supervisor, which is restarted weekly (OPS-03)
- [ ] Backups: the fill ledger and the day records copied twice, one copy off the PC, and a
      restore drilled every quarter (DQ-05, DQ-09)

## Phase 4 — the ladder

Runs now as two lanes, GRID and RUNGS, by his ruling of 13 November. `lab/` may use numpy
and nothing else beyond the standard library and `desk/`. Its ceiling rises from 1,500 to
7,000 lines (`BUDGET.json`, his ruling) when he merges the pull request that carries it.

### The grid lane's book

**Lane objective:** the fast grid engine (`lab/`, numpy), proven first by a parity test
against the desk's own engine on the golden data: the same decisions, day by day, or it is
removed (canon B2).

- [x] The unit of work, keyed by code and data version (`lab/cell.py`)
- [x] A batch service that survives a bad cell and a restart (`lab/batch.py`)
- [x] Results kept, keyed by code and data version; only what changed is re-run (`lab/batch.py`)
- [ ] The fast grid engine, its parity with the desk's engine proven on the golden data
- [ ] Auto-tune, so a pass can never take the PC down: a hard memory ceiling held by
      Windows itself (a Job Object on the workers, about 60% of the 64 GB); workers sized
      to free cores, two of the eight threads left free while markets are open (UK 08:00 to
      21:00 on trading days) and one overnight and at weekends; batches sized from measured
      memory per cell, bars read per ticker, never the whole universe; backing off under
      about 25% free memory or above about 85% CPU and stepping back up with room; peak
      memory and CPU logged for each pass. Proven: a deliberately memory-hungry cell is
      killed by the ceiling, the PC stays responsive and the batch carries on
- [ ] The grid's first pass over the research universe: every strategy at every setting on
      every ticker, each cell kept by code and data version
- [ ] Runs seven days without stopping
- [ ] The cell's key carries the cost model's version and the rung's code, so a change to
      either re-runs what it touches (BT-04)
- [ ] Each strategy judged on its own declared universe; the everything-on-everything grid
      kept as a transfer study, never a verdict; sweeps on the declared universe (LAD-01,
      LAD-13)
- [ ] A full sweep within a weekend, its time measured (LAD-10)

### The rungs lane's book

**Lane objective:** luck correction that counts every trial: a winner is corrected for how
many trials it was picked from, and every rung records that count (canon B6, AG-01).

- [x] The first rung proven: it catches a planted edge and rejects a planted non-edge, after
      the broker's costs and the desk's own stop (`lab/rung.py`)
- [ ] Its costs whole: spread, slippage and the sale's own fees, from the desk's one cost
      model once the money lane has them; and a rate of exchange for each day
- [ ] Luck correction counting every trial
- [ ] In-sample and out-of-sample folds, side by side after costs, the worst fold reported
      and judged on
- [ ] Plateaus over peaks: the centre of a plateau promoted, never a lone peak
- [ ] Reproduces a published strategy's own published result
- [ ] Failing fairly: too few effective trades is "not enough evidence", never a fail; a
      check that the code is the published rule; no trades at all is a fault in the test
      (LAD-06, STR-12)
- [ ] The luck test fixed before any result: a deflated Sharpe with bands of 0.90 and 0.50,
      one combined 5% test across the set, a daily Sharpe above 2 flagged, and one verdict
      rule over the named rungs (LAD-03, LAD-08, LAD-09)
- [ ] Periods and regimes: replays across periods and regimes; a strategy never failed for
      working in only one; out-of-regime trades tagged on paper (LAD-05, REG-03, STR-20)
- [ ] Each indicator known-answer tested against a published reference series (STR-14)
- [ ] Before paper: a kill condition declared for each strategy; promotion only after at
      least thirty effective paper trades, net positive (STR-17, LAD-11)
- [ ] At least three ladder-passed strategies and a feasibility number before A-GATE paper
      (NS-04)
- [ ] The edge judged against the market risk it took (its beta, or a leverage-matched
      benchmark), and the book's concentration measured as its number of independent bets,
      with the A-GATE profit split by correlated cluster (BIC-01, BIC-02)
- [ ] His paramount case: long and inverse leveraged-ETP trend strategies through the ladder
      (STR-18)
- [ ] Stress scenarios: the 2020 crash, flash crashes, a leveraged product's gap (2008 lies
      before the history) (TST-06)

## Phase 5 — the edge

- [ ] Candidates through the ladder, leveraged index lines included
- [ ] The operator's hand tickers judged honestly, with their own rules
- [ ] Small-size paper trading as out-of-sample proof
- [ ] The stops deferred from the scenes: ratcheting stops, and one protective sell across
      every position in a crash, the 3LGO lesson (STP-03, STP-07)
- [ ] **A-GATE** (AG-01 to AG-06, his ruling of 13 November, `docs/DECISIONS.md`):
      luck-corrected on years of history through the ladder; then sixty consecutive
      paper days averaging at least £100 a day net of every cost, inside the range the
      history predicted, ahead of simply holding the market, never more than £1,500
      below the highest point, every day reconciled. Thirty days suffice only on the
      "excellent" terms fixed in advance there: £150 a day, a fall under £750, twenty
      trades, the best three days under a third of the profit.

## Phase 6 — the operator's own account, and widening

- [ ] Read-only signals for the tickers he trades by hand
- [ ] Market weather; more lines; more strategies, a few at a time through the ladder
- [ ] His Trading 212 account read every fifteen minutes, his held names tracked, and his
      stops, take-profits and sell alerts messaged for held names only; buy signals for his
      hand tickers on their own rule and hourly bars; help cutting green-to-red falls; the
      desk's best signals sent to him (LIV-01, LIV-02, LIV-03, LIV-04, LIV-07, LIV-05,
      LIV-09, DAT-11)
- [ ] Market weather: a daily regime label on every verdict and trade; layers added only
      once each proves it predicts, is scored against what followed and confirmed against
      whipsaw; when the weather turns, stops tighten, leverage pauses, cash rises (REG-01,
      REG-02, REG-07, REG-08, REG-09, REG-04, STP-05, EMG-03)
- [ ] More strategies: several winners for every regime, about five a regime then hundreds;
      swing and momentum at more than one holding time; a shadow book for each strategy;
      trading compared with its ladder result every month (REG-05, STR-07, TRD-05, STR-05,
      STR-13)
- [ ] Signals graded, the best grade proven to win more; sizing by bounded multipliers and
      fractional Kelly under a hard cap (FIL-01, FIL-07, SIZ-02, SIZ-03)
- [ ] The universe: a weekly refresh resolved by the broker, six thousand names refreshed in
      five minutes; an earnings and events calendar, point-in-time, for rules and stops; a
      full research simulation with synthetic markets and calibrated fills (UNI-01, DAT-05,
      BIC-06, TST-23)

## Phase 7 — going live

- [ ] The go-live requirements, and his one signature
- [ ] Before any real money: hard limits, and daily and weekly loss breakers that act; caps
      by name, sector, correlated group and total leverage; only strategies through every
      rung; a fall from the high point stops new entries; no open serious fault (MIG-06,
      EMG-04, SIZ-08, MIG-07, BIC-05, MIG-01)
- [ ] The ISA made real: its rules, the currency, the Trading 212 transfer, the yearly
      subscription limit, and paper re-scored at the size real money can reach (MIG-05,
      BIC-07)
- [ ] A ramp, not a switch: live compared with paper every day, a gap pausing the ramp
      (MIG-03, MIG-04)
- [ ] The desk rebuilt on a clean PC within two hours, its stops resting at the broker
      meanwhile (OPS-15)
- [ ] Records kept for their statutory years and reconciled each year to the broker's
      statements; if he does not acknowledge for a set number of days, no new positions,
      and a named second person can sell everything (BIC-08, BIC-09)
- [ ] Beyond: a thousand pounds a day net, money in any weather with cash a valid
      position, and the size at which each strategy's costs erase its edge (NS-03, NS-07,
      BIC-10)

---

## The requirements

Every requirement of his spec (`DESK_REQUIREMENTS_V2`, 226 rows, ratified 31 October 2026)
and the eleven best-in-class additions he took on 13 November (BIC-01 to BIC-11,
`docs/DECISIONS.md`) has one home: a step in a lane's book or a phase above, the standing
practice listed here, or a decision in `docs/DECISIONS.md` that dropped or replaced it. A
guard (`tests/guards/test_requirements.py`) fails the check when any of the 237 has none.

**Standing, delivered by the canon, the guards, the scenes or code already built:** BT-08
BT-10 BT-15 CODE-01 CODE-02 CODE-03 CODE-05 CODE-06 CODE-07 CODE-08 CODE-09 DQ-02 DQ-06
DQ-07 EMG-06 FIL-03 FIL-06 GOV-01 GOV-02 GOV-04 GOV-05 GOV-06 GOV-10 GOV-14 LAD-02 LAD-04
LAD-07 LAD-12 LIV-06 MIG-02 MSG-08 NS-08 NS-11 NS-12 OPS-08 OPS-09 OPS-12 OPS-14 SIZ-01
SIZ-06 SIZ-11 STP-02 STP-06 STP-08 STP-09 STR-01 STR-02 STR-04 STR-08 STR-16 TRD-02 TRD-04
TRD-07 TRD-08 TRD-13 TRD-15 TST-01 TST-10 TST-12 TST-13 TST-17 TST-19 UNI-02 UNI-04 UNI-06

---

## Rules of the plan

A batch is one session, one lane, one objective, one merge. A batch that adds net lines must name
the scene it advances. No new capability until every scene passes.

Estimates are from size, not measurement, and are re-made after phase 0 and after the
first three sessions of phase 2. Actual against estimate is reported every week.
