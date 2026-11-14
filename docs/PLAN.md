# The plan

**Current objective:** the money lane's — the kill switch and its drill (his ruling: first
of its own book); then the costs whole, then the day's record, with which scenes 6 and 7
pass together.

Scenes passing: **7 of 7**. Phase: **3-money-paper**.

The two lines above belong to the money lane: it alone moves the scenes count. The other
lanes' objectives are in their own books below. The operator's Telegram line
reads the ticked boxes under each `## Phase N` heading, so each lane's book sits inside its
phase.

---

## The five lanes

Five lanes of sessions run side by side on the operator's PC, day and night, up to twelve
sessions at once: MONEY and DATA three each, PAPER, GRID and RUNGS two each (his rulings,
13 November 2026, `docs/DECISIONS.md`). A lane's session edits only the files its lane
owns, and of those only its claim. Each lane's parts of the shared documents are its
section of `docs/STATUS.md`, its book here, its table in `docs/SCOREBOARD.md` and its part
at the end of `docs/DECISIONS.md`. Each lane's book sits inside the phase it belongs to: DATA in
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

**The runner hands out the work, and a claim holds it.** A box of a book carries a note at
the end of its text: `{id: money-kill; files: desk/kill.py, tests/unit/test_kill.py; after:
money-costs}`. The id is unique; `files` names every file the box changes (globs allowed,
`docs/PLAN.md` only for a box that moves the scenes count, `*` for one that must hold all
the lane's files); `after` names the boxes, of any lane, done first; `waits` names what
the box waits on outside the lane: a request (`R-RUNGS-6`), a date (`2026-11-21`) or
`operator`. The runner gives a session the first box whose `after` boxes are done, whose
waits are met and whose files no running session holds; its files are the session's claim.
A box blocked outside the lane is never handed out again: the session says `Waits: ...` in
its pull request, or the doctor finds it, and the runner holds it back until the request is
done or the date comes, freeing the boxes after it that do not truly need it. A box with no note is serial work: one session,
alone in its lane, claim `*`. A lane whose next five boxes are not all noted is asked to
note them first. The claim is in the session's pull request as `Claim: ...`, and the check
refuses a change outside it and a lane's pull request without one
(`tests/guards/test_lanes.py`, which also refuses a note it cannot read).

**Sessions do not write the shared documents; the lane's scribe does.** A session's pull
request carries `Ticks:` (the ids it finished), its status, scoreboard line, decisions,
what remains and its requests to other lanes. About every two hours a small scribe session
per lane folds the landed descriptions into the lane's parts of the four documents: it
ticks the boxes, numbers the requests and keeps the STATUS section under 50 lines.

**A lane that needs another lane's file changed does not touch it.** Its request is folded
into its own STATUS section, under `### Requests to <LANE>`:
`- [ ] R-<ITS LANE>-<n> (blocking|later, opened YYYY-MM-DD HH:MM): what is needed and why`.
The owning lane names the request in its `Ticks:` line (or declines it, saying why), its
scribe records it under `### Done for other lanes`, and the asker's scribe ticks it. The
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
- [ ] **Self-contained and portable** (his ruling, 14 November): the desk runs only from its
      own folders (this repository, its runner, its data folder and its notes) and reads
      nothing in any other repository or store at run time. Whatever it needs from the old
      desks is copied in through the one store's checks or ported as code under its own
      test. Every path comes from one setting; the database has a generic name (`market.db`)
      behind the one store, so it can later be a server database. A guard fails a change that
      names a folder outside these (OPS-15)
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
The grid lane needs it. The money lane's blocking requests are done: R-MONEY-1 (each line's
UK tax) and R-MONEY-2 (the scenes on the whole fourteen months).

- [x] The rehearsal data in a file of its own (`tests/scenes/rehearsal.py`)
- [x] The rehearsal data lengthened to about fourteen months, the five rules buying and
      selling in it on every clean line, its UK and US holidays respected; the spoilt line's
      faults kept within the last sixty sessions (`docs/DECISIONS.md`, the data lane's)
- [x] The scenes moved onto the whole fourteen months, each line on its own venue's
      calendar; the six-week window is gone (R-MONEY-2)
- [x] One line the archive refuses is parked, not the whole fetch stopped (`archive.gather`, `store.Refused`)
- [x] The research list: 1,065 tickers with their venue and currency (the four lists
      overlap, so not 1,500), kept apart from the instrument master's twenty trading lines;
      being on it makes nothing tradable (`lab/universe.py`)
- [x] The research list's daily bars since 2010, fetched and kept through the one store's
      checks, a bad ticker parked with its reason (`universe.keep`): 864 clean, 201 parked
- [ ] **First, by his ruling of 13 November:** SPY, QQQ and GLD leave the twenty for their
      UK-listed twins an ISA can hold: VUAG (S&P 500), EQQQ (Nasdaq 100) and IDTL (US
      Treasuries 20+ years), each on the London venue; every line carries an ISA and
      retail-buyable flag; the "simply holding the market" yardstick re-pointed (UNI-09)
      (built in #85: the three twins, both flags, yardstick VUAG, GLD out; remains: SPY and QQQ
      leave the master once GRID's and RUNGS's tests stop naming them (the requests to GRID and RUNGS);
      IB1T is not ISA-holdable, for the operator)
      {id: data-isa-twins; files: desk/lines.py, tests/unit/test_lines.py, tests/unit/test_lab_universe.py; waits: R-RUNNER-4, R-RUNNER-5}
- [x] The research list's parked fifth: 201 tickers' large one-day moves confirmed, or a
      rule for research that needs no confirmation (rule built in `universe.read`, #80; remains:
      the grid reads through it (R-DATA-7) and the rungs count the named moves (R-DATA-8); the
      2.5 times re-measured on the full universe; WWH, SHC and three windfalls settled by a
      second source; a home for the research store)
      {id: data-parked-fifth; files: lab/universe.py, tests/unit/test_lab_universe_parked.py}
- [x] One fast store for hot and deep data, standard library only: SQLite in WAL mode with
      one writer and many readers, held to benchmarks set now: a five-minute round for every
      line written in under a second, a line's last week read in under 50 ms, a line's daily
      history read in under 200 ms (DAT-04)
      {id: data-fast-store; files: desk/bars.py, tests/unit/test_bars*.py, manifest.toml}
- [x] Half-days and auction times in the calendars (DQ-11)
      {id: data-hours; files: desk/venues.py, tests/unit/test_venues*.py}
- [x] A five-minute store, started now because the free archive keeps only about sixty days
      of five-minute bars: each evening the twenty lines' five-minute bars are saved through
      the same checks; the last week kept hot for reading, everything older archived, none
      thrown away (DAT-11)
      {id: data-five-minute; files: desk/archive.py, tests/unit/test_archive*.py, desk/bars.py, tests/unit/test_bars*.py; after: data-fast-store}
- [ ] **Hot every five minutes, paramount (his ruling, 13 November evening):** during each
      venue's trading hours the keeper fetches every clean line's newest five-minute bar
      every five minutes, checks it on entry, and updates every indicator the rules and the
      crash watch read; a line whose bar is late, missing or out of line is parked at once
      and not traded, and the other lines carry on; a line that comes clean comes back by
      itself. The source's delay is measured and shown, never hidden (DQ-12, DAT-07, DAT-11)
      {id: data-keeper; files: desk/keeper.py, tests/unit/test_keeper*.py, desk/bars.py, tests/unit/test_bars*.py, manifest.toml; after: data-five-minute, data-hours}
- [ ] The archive spared: fetching slow and resumable, with backoff, each raw answer cached
      in the folder `KESTREL2_DATA` names (outside the repository and every worktree); while
      the archive refuses, `{"refusing_since": <time>}` written to `KESTREL2_DATA/archive.json`
      (null once it answers), so the runner tells the operator after six hours, and other work
      done meanwhile rather than retrying
      {id: data-archive-spared; files: desk/archive.py, tests/unit/test_archive*.py}
- [ ] Polite fetching: the archive's limits measured, slow and resumable requests, backing
      off on refusals, raw responses cached, an alert after six hours refused (DAT-08)
      {id: data-polite; files: desk/archive.py, tests/unit/test_archive*.py; after: data-archive-spared}
- [ ] Kept hot, always: the runner runs the store's keeper after the US close and before the
      London open on every trading day, a dated receipt each time; a line staler than one
      session raises an alert, and a keeper that misses its slot raises one too (DQ-12,
      DAT-07)
      {id: data-kept-hot; files: desk/keeper.py, tests/unit/test_keeper*.py; after: data-keeper}
- [ ] The store's keeper: its cadence, a dated receipt for each run, a restart drill; each
      bar's source and arrival time kept (DQ-12, DQ-10)
      {id: data-keeper-receipts; files: desk/keeper.py, tests/unit/test_keeper*.py, desk/bars.py, tests/unit/test_bars*.py; after: data-kept-hot}
- [ ] A home for the research store on his PC, refreshed nightly, a ticker that left a list
      cleared out, and the day and list it reflects written beside it
      {id: data-research-home; files: lab/universe.py, tests/unit/test_lab_universe*.py; after: data-parked-fifth, data-isa-twins}
- [ ] The lists' members year by year, so a study of the past is not the survivors' alone
      (S&P 500 and Nasdaq 100 built in #96, `lab/members.py`; remains: the FTSE 350 and the funds,
      joining the lists' records up, a second source for 2010 to 2014)
      {id: data-members; files: lab/members.py, tests/unit/test_lab_members*.py, manifest.toml}
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
- [ ] Coverage and quality measured: history at least twice the longest lookback for every
      line, five years by the A-GATE; a quality score per line and desk-wide, and a cap on
      the share of lines parked (DAT-03, DQ-01)
- [ ] A second source: a gap filled and a failing feed replaced from a ranked second
      source, with a staleness alarm and a register of sources; the twenty lines' bars
      checked against the broker's price of record each day once PAPER connects (DQ-03,
      DAT-07, DAT-01, DAT-02)
- [ ] Dividends and corporate actions: total-return history for the ladder, the paper
      profit and the hold-the-market yardstick (UNI-07)
- [ ] Survivorship: the research list taken as it stood on each past date, with the names
      that left it, or the bias measured and stated on every verdict (BT-09)
- [x] Each line's UK tax a fact on the line, from one table of two rates: nil for a fund or
      an exchange-traded product, stamp duty for a UK share; the twenty lines each state nil,
      and one London line of the rehearsal data pays it (R-MONEY-1)
- [ ] UK stamp duty and taxes confirmed line by line, in one table by instrument type
      (NS-05): the table is built and the five London funds confirmed; still owed, the five
      London products seen on a contract note, the research list's London shares name by
      name, Ireland's 1%, and the default removed (R-DATA-4, R-DATA-5)
- [ ] Leveraged-product lifecycle watched: an issuer's closure, a compulsory redemption or
      an ISA eligibility change on any line held or researched raises an alert (BIC-11)
- [ ] Disk watched; old research files roll off by rule (OPS-07)
- [ ] **Two databases, both owned by the one store** (his ruling, 14 November), in the desk's
      data folder, never in this public repository: `market.db`, long-term, every timeframe
      from an hour up plus all imported intraday history; and `market_hot.db`, live 1-minute
      bars for the twenty lines and a watchlist of up to 100 within his IBKR line allowance.
      The hot keeper runs every minute in each venue's hours, IBKR first, with the free
      archive as a check; each night the day's hot bars roll into `market.db`. Every useful
      store on C: (`kestrel2_notes\data_register.md`, tagged IMPORT) is consolidated into
      `market.db`, each source marked verified there. One consistent snapshot of both
      databases and the ledger is written each night for his own backup to carry (DAT-11,
      DQ-12, DQ-05)
- [ ] The old stores consolidated, never lost: once the one store holds their bars, verified by
      counts and checksums per ticker and timeframe and by one restore drill, the originals
      are deleted from C: with his explicit yes, asked then (never copied to E:, his backup
      drive). His mark_the_trend programs are retired (his word, 14 November), so
      `C:\mtt_cache` is treated like the other stores (DQ-05, OPS-07)
- [ ] **The old desk's stores as a head start, now** (his ask, 14 November): its daily and
      five-minute bars (Stooq and IBKR stores, and its per-ticker matrices) read in through
      the one store's checks, every bar re-checked, each kept with its source; where a fresh
      bar from the archive or the broker differs, the fresh one wins and the difference is
      counted. Its stored indicators are not copied: indicators are recomputed from bars, and
      the old values serve only as a cross-check of the recomputation (DAT-03, DAT-01)
- [ ] The hot bars' first source is the broker: he already pays for IBKR's market data, so
      the five-minute keeper reads live bars through IB Gateway's paper port, read-only, and
      the free archive is the second source and the check on it; first prove, read-only,
      that the paper account sees his live data and not the delayed kind, and if it does
      not, say which setting he must turn on (DAT-02, DAT-07)
- [ ] Deep history: daily bars back to 2000 wherever the archive has them, the calendars
      carried back first; the old desk's Stooq store used only as a head start, every bar
      re-checked on entry (DAT-03, BT-09)

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
until it is drilled. Cancelling is a sixth question of any broker (`broker.Broker`), so the
paper adapter answers it too. After it, in order: the costs whole in the desk's one cost model
(`desk/orders.py`): what a sale itself costs, and spread and slippage on both legs, the
stop's sale included, each a stated assumption recorded in `docs/DECISIONS.md`; the rungs
lane waits for them too. Then the day's record (`day.run`), once the data lane has put
each line's UK tax on the line: scenes 6 and 7 read the same record, so they pass together
(`docs/DECISIONS.md`, the money lane's). The pretend broker, the send path, the book, the
day's trading and reconciliation are built, and any broker can stand behind them.

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
- [x] One rule for "is the book the broker's?", for the pretend broker and the paper account
      alike, entry by entry, the resting stops through it too (`book.differences`; the
      paper lane's R-PAPER-1)
- [x] Any broker behind the send path and the day run, not the pretend one by name, giving
      its holdings and stops as entries, read once for each order (`broker.Broker`; the
      paper lane's R-PAPER-2)
- [x] **The kill switch, before the paper lane sends any order:** one command stops all new
      orders and cancels the open ones, and the desk says so; drilled before FIRST-LIGHT's first
      day and then monthly (EMG-02, canon B1) {id: money-kill; files: desk/kill.py,
      desk/broker.py, desk/book.py, tests/unit/test_kill*.py, tests/unit/test_broker*.py,
      tests/unit/test_book*.py, tests/unit/test_day*.py, manifest.toml}
- [x] The costs whole: a sale's own cost, and spread and slippage on both legs, the stop's sale
      included, in the one cost model; UK tax from a fact on each line (asked of the data lane)
      {id: money-costs; files: desk/orders.py, desk/book.py, tests/unit/test_orders*.py,
      tests/unit/test_book*.py, tests/scenes/test_scenes.py; after: money-kill}
- [x] The day's record (`day.run`): the day reconciled at its end, a mismatch named and its
      profit withheld; else the profit after every cost line, to one rounding policy, beside
      what holding the market earned; the same days replayed to the same records. Scene 6's days
      moved onto the fourteen months, its book checked against the broker's every day - **scenes
      6 and 7 pass** {id: money-record; files: desk/day.py, desk/book.py, desk/orders.py,
      tests/unit/test_day*.py, tests/unit/test_book*.py, tests/unit/test_orders*.py,
      tests/scenes/test_scenes.py, docs/PLAN.md; after: money-costs}
- [x] SimCity, small: one command runs the whole desk's day over all fourteen months of
      rehearsal data against the pretend broker with its faults, every night, and writes one
      record; a census names every part of the money path and turns red when one has no scenario.
      Done in #134; its first night is RED (six lines held against five). Remains: a nightly
      run on his PC with its records kept (the runner's owner); code and data version in the record
      {id: money-simcity; files: desk/simcity.py, tests/unit/test_simcity*.py,
      tests/scenes/test_scenes.py, manifest.toml; after: money-kill, money-record}
- [ ] **First, from SimCity's red night:** the send path counts orders still working, so a desk
      that died mid-send never holds more than five lines; any broker says which of the desk's
      own orders are still working; SimCity's night turns green and its pin (`SIX_HELD`) goes
      {id: money-working; files: desk/book.py, desk/broker.py, desk/orders.py, desk/kill.py,
      desk/simcity.py, tests/unit/test_book*.py, tests/unit/test_broker*.py,
      tests/unit/test_orders*.py, tests/unit/test_kill*.py, tests/unit/test_simcity*.py;
      after: money-simcity}
- [ ] A holding whose stop was cancelled by hand gets it back the same day, or he is told at
      once (found by SimCity: 98 sessions held with no stop)
      {id: money-restop; files: desk/day.py, desk/book.py, tests/unit/test_day*.py,
      tests/unit/test_book*.py; after: money-working}
- [x] Emergencies in numbers: an emergency, a crash and a black swan each defined by measured
      falls, each with its action (EMG-01) {id: money-emergencies; files: desk/emergency.py,
      tests/unit/test_emergency*.py, manifest.toml}
- [ ] (Every box adding a public function to strategy, orders, broker, book, day or kill also
      needs `desk/simcity.py, tests/unit/test_simcity*.py` in its files, one session at a time;
      a function no scenario runs turns the check red: halts and limits among them.)
- [ ] Halts: a halt is a typed record; while one is in force the desk buys nothing and says so
      every day until it is lifted, and the day's verdict reads it; each morning one list of
      every blocker and every signal it blocked (FIL-08, NS-06, FIL-04, TRD-01)
      {id: money-halts; files: desk/halt.py, desk/day.py, desk/book.py,
      tests/unit/test_halt*.py, tests/unit/test_day*.py, tests/unit/test_book*.py,
      manifest.toml; after: money-kill, money-record}
- [ ] The gate's other limits from canon B1: a day's and a week's loss and an order rate,
      refused at the gate (EMG-04 when live) {id: money-limits; files: desk/orders.py,
      desk/book.py, desk/day.py, tests/unit/test_orders*.py, tests/unit/test_book*.py,
      tests/unit/test_day*.py, tests/scenes/test_scenes.py; after: money-record}
- [x] Each strategy's declaration typed: its bar, holding period, test universe and data; a
      short sale cannot be built at all (STR-03, STR-06); remains: a sale made only from the
      book's holding (orders, day, broker) {id: money-declared;
      files: desk/strategy.py, tests/unit/test_strategy*.py}
- [x] The money invariants property-tested, seeded: positions equal the sum of fills, equity
      equals cash plus market value, profit equals realised plus unrealised less costs, orders
      move only through valid states, sending is idempotent (TST-04, canon B4). Done in #132,
      25 seeded worlds; remains: a fault that can reach a sale or fill in two executions
      {id: money-invariants; files: tests/unit/test_book*.py, tests/unit/test_orders*.py,
      tests/unit/test_broker*.py; after: money-record}
- [ ] **The crash watch, on the five-minute data:** every five minutes in trading hours it
      reads the newest bars of every held and watched line and the market's own; a fall that
      crosses the emergency thresholds halts all buying at once, alerts him immediately at
      any hour, and records why; the protective sell across every position (STP-07) acts on
      it once built (EMG-01, EMG-03)
      {id: money-watch; files: desk/watch.py, desk/halt.py, tests/unit/test_watch*.py,
      tests/unit/test_halt*.py, manifest.toml; after: money-halts}
- [ ] A position the desk did not make is named and then sold on paper (TRD-06); no signal
      is left half-processed at the day's end (TST-08)
      {id: money-stranger; files: desk/day.py, desk/book.py, desk/orders.py,
      tests/unit/test_day*.py, tests/unit/test_book*.py, tests/unit/test_orders*.py;
      after: money-halts}
- [ ] SimCity widened: a hundred seeded worlds with faults and drills, not one rehearsal
      world (TST-05, TST-22)
      {id: money-worlds; files: desk/simcity.py, tests/unit/test_simcity*.py;
      after: money-simcity}
- [ ] Small and illiquid trades: a trade whose expected gain is under twice its round-trip
      cost is flagged, and no position is above 1% of its line's twenty-day traded value
      (SIZ-10, TRD-10)
      {id: money-small; files: desk/orders.py, desk/day.py, tests/unit/test_orders*.py,
      tests/unit/test_day*.py; after: money-limits}
- [ ] Time and gaps: a time stop after the strategy's declared holding period; a gap that
      jumps the stop held against the loss limit; a hold limit and gap sizing for the
      leveraged lines (STP-11, STP-10, SIZ-09)
      {id: money-time-gaps; files: desk/day.py, desk/orders.py, desk/strategy.py,
      tests/unit/test_day*.py, tests/unit/test_orders*.py, tests/unit/test_strategy*.py;
      after: money-limits}
- [ ] Fills realistic: spread and slippage in every fill, from the one cost model (TRD-09)
      {id: money-fills; files: desk/broker.py, desk/orders.py, desk/book.py,
      tests/unit/test_broker*.py, tests/unit/test_orders*.py, tests/unit/test_book*.py,
      tests/unit/test_day*.py, tests/scenes/test_scenes.py; after: money-invariants}
- [ ] The golden reference run committed; a change to a size, a stop or a threshold is
      replayed on it before it lands (TST-21, GOV-09, canon B5)
      {id: money-golden; files: *; after: money-fills, money-limits, money-halts}
- [ ] Every trade's whole story: signal, intent, risk decision, order, fill and the bar it
      read, linked by ids; profit attributed by strategy, line, holding time and cost
      (TRD-11, TRD-12, DQ-08)
      {id: money-story; files: desk/story.py, desk/book.py, desk/day.py,
      tests/unit/test_story*.py, tests/unit/test_book*.py, tests/unit/test_day*.py, manifest.toml;
      after: money-fills, money-limits}
- [ ] Money honestly counted: interest on idle cash, with the risk-free rate in every
      Sharpe; currency gains and losses on dollar holdings reported apart from trading
      profit; a fall from the book's highest point alerted on paper (BIC-03, BIC-04, BIC-05)
      {id: money-honest; files: desk/day.py, desk/book.py, tests/unit/test_day*.py,
      tests/unit/test_book*.py; after: money-fills}

## Phase 3 — the money path, on paper

Begun alongside phase 2 by his ruling of 13 November: "Five lanes, phase 3 now".

- [ ] **FIRST-LIGHT: ten consecutive clean trading days**
- [ ] **FIRST-LIGHT's first day is Monday 16 November, 08:00 London** (his ruling: the date
      holds; blockers get workarounds, never a later date). It starts on every one of the
      twenty lines that is clean that morning; a line that joins later (an ISA swap still in
      hand, a line parked) joins without restarting the count. Each blocker has a workaround
      that keeps every safety rule: until the working-orders count is built, the send refuses
      any line with an open order at the broker (the paper account is read before every
      round); until the supervisor is built, the runner itself runs the desk's day on
      schedule; the twenty lines' daily bars come from the store, refreshed from the archive
      each morning, with the broker's bars as the fallback. Sunday 18:00: a dry rehearsal of
      the whole day, and one go/no-go line to him naming any blocker still open and its
      workaround (NS-10, TRD-01)
- [ ] **One pre-flight each trading morning, before the open:** the whole check green on main;
      one SimCity world lived; each rung's known-answer cases (a planted edge passes, noise
      fails); the paper Gateway's handshake; every line's data fresh and its checksums whole;
      a canary bar compared across two sources; the messenger's delivery proven; a halt in
      force named. One record, one go/no-go line; a no-go halts buying for the day, never
      silently (OPS-04, GOV-13, TST-21)
- [ ] **One deep run each night after the US close, and a full one each weekend:** the hundred
      SimCity worlds with faults and drills, the stress scenarios, the rungs' null and power
      calibration, a synthetic round trip of every order type through the pretend broker,
      every trade's lifecycle traced end to end; the weekend run adds the deliberate breaks
      of the money path. One record each, folded into the morning line (TST-05, TST-22,
      TST-20, TRD-11)

### The paper lane's book

**Lane objective:** the real paper-broker adapter behind the same interface as
`broker.Pretend`, through the one door (`desk/paper.py`) with the standard library alone,
built from what it reads towards what it sends. The account and each of the twenty lines as
the broker lists it are read (`desk/listing.py`). Next, first a short step: the account
check moved onto the money lane's one comparison (`book.differences`, R-PAPER-1, done in
#52), so "is the book the broker's?" has one home. Then the fills and orders the broker
reports, read-only, each fill's price turned from the broker's unit (pence on six London
lines) back into the line's currency, and the desk's own orders told from anyone else's;
then placing. It sends no order until that day's read-only check (`clearance.check`) has
come back clean, and the check has been taught the desk's own resting stops. The account is
the old desk's (his ruling, 13 November), reached through IB Gateway's paper port 4002 on
his PC with the desk's own client id (222), never 4001.

- [x] The read-only check of the paper account's positions and open orders against the
      desk's book, every mismatch named (`desk/paper.py`); run on the real account on 13
      November: quiet, no shares held and no order resting
- [x] Each of the twenty lines as the broker lists it, read-only: its number there, its
      exchange, pence or pounds, and its price steps, with a price put down onto the
      broker's step in the broker's unit (`desk/listing.py`); run on the real gateway on 13
      November: twenty of twenty listed, six London lines priced in pence
- [x] The fills and the orders the broker reports, read-only: each fill under the broker's
      id with its price back in the line's currency, and the desk's own orders and stops
      told from anyone else's (`desk/reports.py`, #86; real gateway 13 November: 21 fills,
      none the desk's, no order open; before real fills are written, the broker's later
      corrections of a fill, R-PAPER-5; the true shape of an open order is seen on the first
      real one) {id: paper-reports; files: desk/reports.py, desk/paper.py,
      tests/unit/test_reports.py, tests/unit/test_paper.py, manifest.toml}
- [x] The Gateway known before any order: its daily restart and the weekly re-login handled
      unattended. A re-login that needs his phone or password is his: a reminder line at the
      right time, never a workaround. The old desk's gateway alarms are a quarry only. (Done in #100; remains:
      the messenger sends his lines, the adapter asks `gateway.known`, Sunday 15 Nov seen live.) (The
      runner already watches port 4002 and the account, read-only, and tells him when it stops
      answering.) {id: paper-gateway; files: desk/gateway.py, tests/unit/test_gateway.py,
      manifest.toml}
- [x] The check run every day and before any order: the adapter refuses to send until
      that day's check is clean, and tells the desk's own resting stops from anyone else's (`desk/clearance.py`, #104; remains: the
      adapter's send asks `clearance.require`, done in #113; a daily run and a message when unclean)
      {id: paper-check; files: desk/clearance.py, desk/paper.py,
      tests/unit/test_clearance.py, tests/unit/test_paper.py, manifest.toml;
      after: paper-reports}
- [x] The real paper-broker adapter behind the same interface as `broker.Pretend`, speaking
      to IB Gateway with the standard library alone (`desk/` imports nothing else). All six
      answers done (#110, #113, #123); remains: nothing to build, each "unproven at the real
      Gateway" item is for paper-conformance
      {id: paper-adapter; files: desk/placing.py, desk/paper.py, desk/reports.py,
      tests/unit/test_placing.py, tests/unit/test_paper.py, tests/unit/test_reports.py,
      manifest.toml; after: paper-reports, paper-check}
- [x] Stops resting at the broker, each rounded down to its line's price step (done in #123)
      {id: paper-stops; files: desk/placing.py, desk/listing.py,
      tests/unit/test_placing.py, tests/unit/test_listing.py; after: paper-adapter}
- [x] No paper order before the kill switch is drilled, held by the code (done in #113; remains: the
      drill run at each desk start): the adapter's
      send refuses unless a drill record of the kill switch from the last 31 days exists,
      and a contract test proves the refusal (owed: name the money lane's kill-switch box in
      `after` once it has an id) {id: paper-drill; files: desk/placing.py,
      tests/unit/test_placing.py; after: paper-adapter, paper-stops}
- [x] Morning and evening messages, and an alarm on silence
      Built (#142), nothing calls it. Remains: paper-running calls it (done in #152), something outside the desk runs
      `messenger.watch` every few minutes, his bot key in the desk's environment (his alone), a real message seen on his phone
      {id: paper-messages; files: desk/messenger.py, tests/unit/test_messenger.py,
      manifest.toml}
- [x] Unattended running, and recovery from a restart
      Built (#152, R-MONEY-8). Remains: the two doors a step is given (price store; day's rates from DATA), the process that asks (paper-supervised)
      {id: paper-running; files: desk/running.py, desk/placing.py,
      tests/unit/test_running.py, tests/unit/test_placing.py, manifest.toml;
      after: paper-adapter, paper-stops, paper-messages}
- [x] **No paper order until the money lane's kill switch has been drilled** (EMG-02)
      Built (#155): the step drills once each day before its check, orders and record
      {id: paper-kill-drilled; files: desk/running.py, tests/unit/test_running.py;
      after: money-kill, paper-drill, paper-running}
- [ ] Conformance trades, on paper, one London and one US line, each in its market's hours:
      a market buy at the open; the resting stop placed, triggered, and cancelled on a sale;
      a partial fill if the paper broker gives one; a rejection. Each real result recorded
      beside the pretend broker's, and the pretend broker fixed where they differ.
      Remains: the in-hours half (#135 did the dry orders, 59 cancelled): fills, triggered stop, sale, part fill, SPY
      {id: paper-conformance; files: *; after: paper-gateway, paper-check, paper-stops,
      paper-drill}
- [ ] The desk's own process supervised: one supervisor, restarts proven by killing it,
      health judged from outside by dated receipts, surviving a reboot, a dropped network
      and a broker disconnect; a ledger of operator actions proving seven days without one,
      bar the ruled Gateway re-login (OPS-01, OPS-02, OPS-04, OPS-10, NS-01)
      {id: paper-supervised; files: desk/supervisor.py, tests/unit/test_supervisor.py,
      manifest.toml; after: paper-running}
- [ ] The running process always on main's latest code, and a money-path change reaching
      it only at a safe point, never mid-send (OPS-05, OPS-16)
      {id: paper-on-main; files: desk/supervisor.py, tests/unit/test_supervisor.py;
      after: paper-supervised}
- [ ] The messages: a start-of-day card by 05:40; an end-of-day summary with the profit,
      the streak and the verdict; a line on every change of state and "the desk is not
      trading" by 09:30 UK; urgency levels without storms; one messenger with a delivery
      record, the merge line and the runner's alerts behind the same door (MSG-02, MSG-03,
      MSG-04, MSG-09, MSG-11) {id: paper-cards; files: desk/messenger.py,
      tests/unit/test_messenger.py; after: paper-messages, paper-running}
- [ ] The day's extras: missed winners, blocked signals, and the running cost set against
      net profit each week (MSG-13, NS-14) (boxes from here down are not yet noted)
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

**Lane objective:** auto-tune, so a pass can never take the PC down; then the cell's key, the
first pass and the rest. (A cell names its line and venue, R-DATA-1: done in #73.) Order:
grid-tune and grid-key side by side; then grid-pass, grid-week, grid-declared, grid-weekend.

- [x] The unit of work, keyed by code and data version (`lab/cell.py`)
- [x] A batch service that survives a bad cell and a restart (`lab/batch.py`)
- [x] Results kept, keyed by code and data version; only what changed is re-run (`lab/batch.py`)
- [x] The fast grid engine, its parity with the desk's engine proven on the golden data
      (`lab/grid.py`: the same position after every bar, or a refusal, never a guess)
- [x] The unit of work on the grid, the desk's engine deciding what the grid refuses
- [x] A cell names its ticker's venue: a `Line` of the research list, its bars read from
      its venue's folder (R-DATA-1). Remains: a cell can still be made from a symbol alone,
      only for the rungs lane's files (R-GRID-2) {id: grid-venue; files: lab/cell.py, lab/batch.py,
      tests/unit/test_lab_cell.py, tests/unit/test_lab_batch.py}
- [x] Auto-tune, so a pass can never take the PC down: a hard memory ceiling held by
      Windows itself (a Job Object on the workers, about 60% of the 64 GB); workers sized
      to free cores, two of the eight threads left free while markets are open (UK 08:00 to
      21:00 on trading days) and one overnight and at weekends; batches sized from measured
      memory per cell, bars read per ticker, never the whole universe; backing off under
      about 25% free memory or above about 85% CPU and stepping back up with room; peak
      memory and CPU logged for each pass. Proven: a deliberately memory-hungry cell is
      killed by the ceiling, the PC stays responsive and the batch carries on
      {id: grid-tune; files: lab/tune.py, tests/unit/test_lab_tune.py, manifest.toml}
- [x] The cell's key carries the cost model's version and the rung's code, so a change to
      either re-runs what it touches (BT-04). Remains: nothing stamps a verdict with the new key yet (R-GRID-3) {id: grid-key; files: lab/cell.py,
      tests/unit/test_lab_cell.py; after: grid-venue}
- [x] The grid's first pass over the research universe: every strategy at every setting on
      every ticker, each cell kept by code and data version. Remains: a command the runner can start, a lock, a journal per worker (grid-week) {id: grid-pass; files:
      lab/sweep.py, lab/batch.py, lab/tune.py, tests/unit/test_lab_sweep.py,
      tests/unit/test_lab_batch.py, tests/unit/test_lab_tune.py, manifest.toml; after:
      grid-venue, grid-tune, grid-key}
- [ ] Runs seven days without stopping. Remains: the seven days themselves; the run began 13 Nov 23:29 UK (moved onto the fix 14 Nov 00:41 UTC, pid in `C:	mp\kestrel2_week\pid.txt`); on or after 20 Nov 23:45 UK read `sweep.unbroken` and tick if 7 days {id: grid-week; files: lab/batch.py, lab/sweep.py,
      lab/tune.py, tests/unit/test_lab_batch.py, tests/unit/test_lab_sweep.py,
      tests/unit/test_lab_tune.py; after: grid-pass}
- [ ] Each strategy judged on its own declared universe; the everything-on-everything grid
      kept as a transfer study, never a verdict; sweeps on the declared universe (LAD-01,
      LAD-13) {id: grid-declared; files: lab/sweep.py, tests/unit/test_lab_sweep.py; after:
      grid-week}
- [ ] A full sweep within a weekend, its time measured (LAD-10) {id: grid-weekend; files: *;
      after: grid-declared}

### The rungs lane's book

**Lane objective:** in-sample and out-of-sample folds: a strategy's history cut into folds,
each judged after costs, the two shown side by side, and the verdict given on the worst
fold; every fold is a trial the luck rung counts (canon B6, AG-01).

- [x] The first rung proven: it catches a planted edge and rejects a planted non-edge, after
      the broker's costs and the desk's own stop (`lab/rung.py`)
- [x] Luck correction counting every trial: a verdict's chance multiplied by the number of
      trials it was picked from, one combined 5% test across the set, the count kept on
      every corrected verdict (`lab/luck.py`)
- [x] In-sample and out-of-sample folds, side by side after costs, the worst fold reported
      and judged on
      {id: rungs-folds; files: lab/folds.py, tests/unit/test_lab_folds.py, manifest.toml}
- [x] The count kept from batch to batch: one register of every trial ever tried on a
      question, a dropped candidate included, so no later batch can start the count again
      {id: rungs-trials; files: lab/trials.py, tests/unit/test_lab_trials.py, manifest.toml}
- [x] The luck test fixed before any result: a deflated Sharpe with bands of 0.90 and 0.50,
      one combined 5% test across the set, a daily Sharpe above 2 flagged, and one verdict
      rule over the named rungs (LAD-03, LAD-08, LAD-09)
      {id: rungs-deflated; files: lab/deflated.py, tests/unit/test_lab_deflated.py, manifest.toml}
- [x] Plateaus over peaks: the centre of a plateau promoted, never a lone peak. Remains: nothing
      calls it; the rules carry no settings yet
      {id: rungs-plateau; files: lab/plateau.py, tests/unit/test_lab_plateau.py, manifest.toml}
- [x] Periods and regimes: replays across periods and regimes; a strategy never failed for
      working in only one; out-of-regime trades tagged on paper (LAD-05, REG-03, STR-20).
      Remains: the weather (REG-01) and handing home regimes to the desk (before paper)
      {id: rungs-regimes; files: lab/regime.py, tests/unit/test_lab_regime.py, manifest.toml; after: rungs-folds}
- [x] Failing fairly: too few effective trades is "not enough evidence", never a fail; a
      check that the code is the published rule; no trades at all is a fault in the test
      (LAD-06, STR-12). Remains: plateau and regime rungs read only pass or not
      {id: rungs-fair; files: *; after: rungs-folds, rungs-trials, rungs-deflated, rungs-plateau, rungs-regimes}
- [x] Its costs whole: spread, slippage and the sale's own fees, from the desk's one cost
      model; and a rate of exchange for each day. Remains: real daily rates (R-RUNGS-3)
- [x] The edge judged against the market risk it took (its beta, or a leverage-matched
      benchmark), and the book's concentration measured as its number of independent bets,
      with the A-GATE profit split by correlated cluster (BIC-01, BIC-02). Built: BIC-01,
      `lab/market.py` (#131); BIC-02, `lab/bets.py` (#136). Remains: wiring (the caller with
      the book's pounds and profit; the market rung named among those the verdict rule reads;
      real daily rates R-RUNGS-3; the operator's ruling on concentration in the A-GATE)
      {id: rungs-beta; files: lab/beta.py, tests/unit/test_lab_beta.py, manifest.toml}
- [ ] Reproduces a published strategy's own published result. Built: `lab/reproduce.py`
      (#120). Remains: Connors' RSI-2 figure from the book, SPY from 1993 (R-RUNGS-5), the first
      real run. Built: the first rung waits for a figure on file (#139); the Double 7's
      figure written down (#141). Remains also: `folds`/`regime` passing reproductions on
      {id: rungs-reproduce; files: lab/reproduce.py, lab/rung.py,
      tests/unit/test_lab_reproduce.py, tests/unit/test_lab_rung.py}
- [x] Stress scenarios: the 2020 crash, flash crashes, a leveraged product's gap (2008 lies
      before the history) (TST-06). Built: `lab/stress.py` (#140). Remains: nothing calls it;
      judged by the loss limit when MONEY sets it (R-RUNGS-11); first run on real bars
      {id: rungs-stress; files: lab/stress.py, tests/unit/test_lab_stress.py, manifest.toml}
- [ ] **The eleven rungs made trustworthy before any verdict counts**, the old desk's
      biggest failure (its rung audit of 20 October is the quarry): sample size by effective
      trades; costs charged; a confidence interval; excess over the benchmark after the
      market risk taken, judged by its size and not merely measured; at least two regime
      windows; benchmark-relative excess judged by a confidence interval, not a sign; the
      deflated Sharpe with the number of trials and their spread taken from one clustered
      set; combinatorial purged cross-validation (or the probability of overfitting across
      the whole roster); a placebo on blocks of days; walk-forward folds; a block bootstrap
      that duplicates no other rung. Each rung proven alone: a planted edge passes it,
      five hundred cells of pure noise pass it at about its stated rate and no more, a power
      curve at three effect sizes, a broken copy of the rung caught, and each defect the old
      audit found kept as a case that must fail (LAD-09, LAD-03, LAD-08)
      {id: rungs-trustworthy; files: *; after: rungs-beta}
- [ ] Each indicator known-answer tested against a published reference series (STR-14).
      Built: moving average, Bollinger deviation, Wilder smoothing held to four published tables
      (#145). Remains: the RSI, true range, bands, carried band, channel (R-RUNGS-6); room for more tables
      {id: rungs-indicators; files: lab/published.py, tests/unit/test_lab_published.py}
- [ ] Before paper: a kill condition declared for each strategy; promotion only after at
      least thirty effective paper trades, net positive (STR-17, LAD-11). Built:
      `lab/promotion.py` (#127). Remains: the desk reads it (R-RUNGS-7); each candidate's kill numbers
      {id: rungs-promotion; files: lab/promotion.py, tests/unit/test_lab_promotion.py;
      after: rungs-trustworthy}
- [ ] At least three ladder-passed strategies and a feasibility number before A-GATE paper
      (NS-04)
      {id: rungs-feasibility; files: lab/feasibility.py, tests/unit/test_lab_feasibility.py,
      manifest.toml; after: rungs-trustworthy}
- [ ] **The eponymous strategies through the ladder first**, before any grid exploration:
      the twenty-one published rules the old desk listed, ported one at a time as rules under
      the one template, each with its author's source, instrument, period and published
      figure written down, so that reproduction can run (the old desk's never did, for want
      of the figures); each reproduced on its author's own market first, and only then judged
      on ours. The bar for twenty-one trials is high and most are expected to fail: that is
      the information (BT-15, STR-14)
- [ ] **Published figures without buying books** (his ruling, 14 November): where an
      author's own table is not to be had free, the best published replication found on the
      internet stands in, labelled secondary, with its source, date, rules and period
      written down; where sources disagree, the range is written down and reproduction must
      land inside it. RSI-2 goes first this way; variants of each rule are tested later on
      the ladder, never chosen by eye (BT-15)
- [ ] **The ladder in sets, each published as it finishes:** set 1, the eponymous strategies;
      set 2, the grid's transfer study over the research universe; then sets of variants
      around any plateau found, each family named before it runs. After each set, one
      Telegram summary and a results file: every strategy, every rung's verdict with its
      reason, the trial count it was judged against, and what goes forward (LAD-09, LAD-03)
- [ ] **Graduation to paper:** a strategy passes all eleven rungs and the luck test at the
      set's full trial count (and its reproduction, if published); it is named in this plan,
      with its kill condition, before its first paper day; it then trades paper side by side
      with up to nine others under the A-GATE terms. Nothing reaches real money without his
      signature (STR-17, LAD-11, MIG-07)
      {id: rungs-eponymous; files: *; after: rungs-trustworthy, rungs-indicators}
- [ ] His paramount case: long and inverse leveraged-ETP trend strategies through the ladder
      (STR-18)
      {id: rungs-leveraged; files: *; after: rungs-trustworthy}

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
      trades, the best three days under a third of the profit. By his ruling of 13
      November evening, a candidate's paper days count from the first clean FIRST-LIGHT
      day, or from the day it passed the ladder if that is later; and up to ten candidates
      run side by side, each named here before its first paper day, the luck test counting
      every one of them as a trial, a candidate dropped still counted.
- [ ] Side-by-side candidates on one paper account: each with its own capital number and
      its own book in the ledger, the gate applied per candidate, and the broker's account
      reconciled against the sum of their books every day

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
- [ ] **Off the single PC:** the desk packaged and moved to a cloud server with a cloud
      database, so his desktop is no longer a single point of failure; the runner's
      Windows-only parts (scheduled tasks, the memory ceiling) kept behind one door so they
      can be swapped; IB Gateway and the secrets on the server; the move drilled before any
      real money (OPS-15)
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
