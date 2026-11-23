# The plan

**Current objective:** the money lane's — the kill switch and its drill (his ruling: first
of its own book); then the costs whole, then the day's record, with which scenes 6 and 7
pass together.

Scenes passing: **8 of 8**. Phase: **3-money-paper**.

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
section of `docs/STATUS.md`, its book here, its table in `docs/SCOREBOARD.md` and its own
decisions in `docs/lanes/<lane>.md`, which only it may change. Each lane's book sits inside
the phase it belongs to: DATA in
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
(`check.py`, the guards, `BUDGET.json`, `CLAUDE.md`, `CANON.md`,
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
Retiring `desk/eponymous_*.py` (R-RUNNER-127) waits until all the rules are spec rows in
`lab/catalogue.toml` (6 of about 25 on 15 Nov); deleting earlier would delete rules, not copies.
R-RUNGS-6 and R-RUNGS-12 (the public `strategy.rsi` and `strategy.lower_band`) were done in #185 and
are pinned by `tests/unit/test_strategy.py`; the open lines in STATUS are stale (the scribe ticks them from the Ticks line of #497 and its successor).
Checked again 15 Nov late: still 6 rows of 19 files, so R-RUNNER-127 stays held (it needs spec-epon first).
Checked 16 Nov: 6 catalogue rows of 21 eponymous rules (15 unexpressed: bollinger_squeeze, connors_*, dan_zanger_breakout, darvas_box, demark_sequential, dual_momentum, faber_tactical, kell_breakout, keltner_channel_trend, mansfield_rs_momentum, minervini_breakout, raschke_swing, weinstein_stage, zweig_breadth_thrust); lab/ladder, rulebook, published, blocks and 8 tests still import the files. Waits: spec-epon.
Checked again 16 Nov (MONEY session): still 15 unexpressed; R-RUNGS-6 and R-RUNGS-12 re-verified done on main (`tests/unit/test_strategy.py` green).

Checked 16 Nov (MONEY, third session): R-RUNGS-8 (`orders.strategy_of` refuses an unreadable id, pinned in `tests/unit/test_orders.py`) and R-RUNGS-11 (`orders.GAP_LOSS`, one named number) are already on main; no blocking request is open.

Checked 16 Nov (MONEY, later session): R-RUNNER-127 still held (15 rules unexpressed, 19 files); R-RUNGS-6 and R-RUNGS-12 ticked (public `strategy.rsi`, `strategy.lower_band`, `tests/unit/test_strategy.py` green).
Checked 16 Nov (MONEY, third session): unchanged; the scribe has not yet folded the ticks for R-RUNGS-6 and R-RUNGS-12 (done in #185); R-RUNNER-127 waits on spec-epon.

Checked 16 Nov (MONEY, fourth session): R-RUNGS-6 and R-RUNGS-12 re-verified on main (`tests/unit/test_strategy.py` green); R-RUNNER-127 is the coordinator's own branch now (ops note 19:3x), declined here.
Checked 17 Nov (MONEY, s2): no blocking request to MONEY is open and every unticked box in the book carries an id (other sessions') or waits (money-connors7: operator); nothing built.

Checked 17 Nov (MONEY): R-RUNGS-12 re-verified on main (`strategy.rsi`, `strategy.lower_band` public since #185; `tests/unit/test_strategy.py` green); no code change.

Fold request (DATA, 22 Nov, Coordinator 33's ruling: a lane may not delete its own module or manifest line; runner ops folds on a non-lane branch, test first): `desk/store_scope.py` (41 lines) folds into `desk/coverage.py`: `window_start` and `judge` move over, `keeper.py` imports `coverage.judge`, `tests/unit/test_store_scope.py` moves into `tests/unit/test_coverage.py`, and the `desk/store_scope.py` manifest line goes. Its behaviour is already pinned by that test.
Checked 17 Nov (MONEY, s6): R-DATA-53 is on main (`desk/command.py:387` passes `home=root.parent`, #798) and R-PAPER-29 is on main (`book.conformance_cost`, #763); no blocking request is open; nothing built.
Checked 20 Nov (MONEY, s2): R-PAPER-35's field is on main (#1102) and set in day, kill, simcity, orders; what is left is PAPER's files (`desk/goflat.py`, `desk/conformance_parts.py`, `desk/placing.py` `_cleared`), outside MONEY's claim; nothing built.
Checked 20 Nov (MONEY, s7): no blocking request is open; R-PAPER-30 (size the 0.05% half-spread, `orders_parts.HALF_SPREAD`/`SLIPPAGE` from one real VUAG buy 0.09 and sale 0.14 below the pretend close) needs a day of fills and moves golden numbers (B5), so it waits for more conformance tapes; nothing built.
Checked 20 Nov (MONEY, s8): no blocking request is open. R-RUNGS-7's desk half is on main (`day.run(killed=...)` refuses a killed strategy's buys); what is left is reading `promotion.standing` into that set, which `desk/` may not import (lab wall) and whose caller `desk/running.py` is PAPER's; nothing built.

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
- [x] **Hot every five minutes, paramount (his ruling, 13 November evening):** during each
      venue's trading hours the keeper fetches every clean line's newest five-minute bar
      every five minutes, checks it on entry, and updates every indicator the rules and the
      crash watch read; a line whose bar is late, missing or out of line is parked at once
      and not traded, and the other lines carry on; a line that comes clean comes back by
      itself. The source's delay is measured and shown, never hidden (DQ-12, DAT-07, DAT-11)
      {id: data-keeper; files: desk/keeper.py, tests/unit/test_keeper*.py, desk/bars.py, tests/unit/test_bars*.py, manifest.toml; after: data-five-minute, data-hours}
- [x] The research list's parked fifth: 201 tickers' large one-day moves confirmed, or a
      rule for research that needs no confirmation (rule built in `universe.read`, #80; remains:
      the grid reads through it (R-DATA-7) and the rungs count the named moves (R-DATA-8); the
      2.5 times re-measured on the full universe; WWH, SHC and three windfalls settled by a
      second source; a home for the research store)
      {id: data-parked-fifth; files: lab/universe.py, tests/unit/test_lab_universe_parked.py}
- [x] **ONE DOOR FOR PRICES, bars** (his 22 Nov ~10:00, "paramount": every price is read from market_history.db or market_live.db alone): `lab/universe_parts.read` reads `bars.daily` of the history database,
      keeping its rescale cut, never the `grid/store` CSV files (`store.read`, line 63), so the grid, sweep, batch,
      transfer, montecarlo and the research refresh read the database; wire: the research refresh and the grid
      job; gate: a contract test where a bar present only in a CSV is never read
      Built (#1653, then one non-lane PR, 22 Nov): `universe_parts.read(path, line)` is the one reader (CSV `read` deleted, a line the database lacks raises LookupError); batch.stored, sweep (the grid job reads DATA/market_live.db's history beside it), transfer, montecarlo's grid jobs and breadth read it. store.read stays only in the CSV writer, its importer and headstart: data-door-writer deletes them.
      {id: data-door-bars; files: lab/universe_parts.py, tests/unit/test_lab_universe*.py; waits: 2026-11-24}
- [ ] One door, one writer: `universe.nightly` and the Stooq files write into the history database through
      `bars.writing`, never the CSV store; `store.read`, `faults`, `shelve` and the CSV half of `prepare` are
      deleted with their tests; wire: the research refresh job; gate: the deleted names import nowhere.
      Built (#1767): the research refresh writes the history database through `bars.writing`, no CSV; `universe_history.enter` deleted. Also built (#1798, #1827): headstart judges through `store.judge` (no scratch CSV store); `store.shelve`, `faults`, `HISTORY` deleted, seven store tests rewritten onto judge. Remains: delete `store.prepare`, `read`, `_bar`, `_FAULT` and `_write`'s CSV use; their MONEY and GRID callers are split to their owners (runner ops 112, 23 Nov: money-door-writer, grid-door-writer); once both land, the deletions and the gate that the deleted names import nowhere
      {id: data-door-writer; files: lab/universe.py, lab/universe_parts.py, lab/universe_history.py, lab/headstart.py, lab/headstart_days.py, desk/store.py, desk/store_scope.py,
      tests/unit/test_lab_universe*.py, tests/unit/test_store*.py, tests/unit/test_lab_headstart*.py, tests/unit/test_keeper.py; after: data-door-bars, money-door-slippage, money-door-writer, grid-door-writer}
- [ ] THE STORE'S CSV HALF UNUSED BY MONEY: `desk/halt.py` writes its file without `store._write`, and the
      scenes read their prices through the history database (`bars.writing`, `universe_parts.read` or `store.judge`),
      never `store.prepare` or `store.read`; gate: neither file names those three
      (split from data-door-writer by runner ops 112, 23 Nov: these are MONEY's files)
      {id: money-door-writer; files: desk/halt.py, tests/unit/test_halt*.py, tests/scenes/test_scenes.py}
- [ ] THE STORE'S CSV HALF UNUSED BY THE GRID: the `.faults` filter in `lab/sweep.py` deleted; the batch
      and sweep tests set their prices through the history database, never `store.prepare` or `store.read`;
      gate: none of the three files names them
      (split from data-door-writer by runner ops 112, 23 Nov: these are GRID's files)
      {id: grid-door-writer; files: lab/sweep.py, tests/unit/test_lab_sweep.py, tests/unit/test_lab_batch.py}
- [x] **The old desk's stores as a head start, now** (his ask, 14 November): its daily and
      five-minute bars (Stooq and IBKR stores, and its per-ticker matrices) read in through
      the one store's checks, every bar re-checked, each kept with its source; where a fresh
      bar from the archive or the broker differs, the fresh one wins and the difference is
      counted. Its stored indicators are not copied: indicators are recomputed from bars, and
      the old values serve only as a cross-check of the recomputation (DAT-03, DAT-01).
      Remains after #175 (five-minute bars built, not yet run on the real store): run it once
      R-RUNNER-10 has landed; daily bars (calendar before 2010, adjusted against as-traded);
      the parquet stores; the old indicators as a cross-check
      Built: `python -m lab.headstart` (#190, resumable, 245,593 old five-minute bars tried in
      on the real stores); `--daily 3LGO` (#209, 2,816 clean bars); four Sources (#203).
      Built since: the parquet and raw-zip readers (#236, #238, #591), the old database's daily rows (#245, #254),
      adjusted against as-traded closes recognised and never written over raw (#286), daily rows from Stooq,
      ibkr_store and mark_the_trend (#527-#545). Remains: the catalog_v2 tag in the data register (outside the
      repository); a matching rule for adjusted against as-traded closes, a new module not on its list (headstart.py
      is at 400 lines); the research list's bars
      Settled (coordinator 54, 22 Nov: not his: the catalog_v2 tag is runner-side notes work; the matching rule is a new lab module registered in manifest.toml inside the lab/ ceiling; the research list's bars come from the keeper)
      Met (runner ops 106, 23 Nov, coordinator 103's D1): catalog_v2 retagged CROSS-CHECK in the data register (names and venues, no bars); the adjusted-close rule is `lab/headstart_days.py` (adjusted days refused whole); the research list's bars are in market_history.db (2000-2009 daily for 820 of 1,084 lines, below)
      {id: data-headstart; files: lab/headstart.py, tests/unit/test_lab_headstart.py, desk/bars.py, tests/unit/test_bars*.py, manifest.toml; waits: 2026-11-24}
- [x] The archive spared: fetching slow and resumable, with backoff, each raw answer cached
      in the folder `KESTREL2_DATA` names (outside the repository and every worktree); while
      the archive refuses, `{"refusing_since": <time>}` written to `KESTREL2_DATA/archive.json`
      (null once it answers), so the runner tells the operator after six hours, and other work
      done meanwhile rather than retrying
      {id: data-archive-spared; files: desk/archive.py, tests/unit/test_archive*.py}
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
- [ ] The lists' members year by year, so a study of the past is not the survivors' alone
      (S&P 500 and Nasdaq 100 built in #96, `lab/members.py`; remains: the FTSE 350 and the funds,
      joining the lists' records up, a second source for 2010 to 2014)
      Remains (#638): the FTSE 350's changes, the funds' records and a 2010-2014 second source.
      Re-carded to a free route (his ruling 22 Nov ~10:05: no paid data until the desk earns consistently):
      the FTSE 100 and 250 changes from FTSE Russell's published quarterly-review announcements, joined to
      the revision history of Wikipedia's FTSE 100 and FTSE 250 pages read through the MediaWiki API; a change
      the two disagree on is a named fault, never a guess; the funds and the 2010-2014 second source by the same
      rule, or the box says which free source is missing and why
      wire: the nightly research refresh reads the lists' members by date; gate: a contract test on a committed
      fixture of one review's announcement and the page revision either side finds the joiners and leavers, and a
      planted disagreement is a named fault
      Built (#1651): `lab/members.reconcile` joins one FTSE review's announced changes to the page revisions either side; disagreement is a named `Disagreement`; feeds not wired. Also (#1715): `Members.survived` measures the share of a day's members still listed (279 of 500 on 1 Jan 2010). Remains: the fetcher module (FTSE Russell announcements, MediaWiki API; a request to RUNNER in STATUS), the nightly refresh reading members by date; no free source exists for the funds' past members or a second 2010-2014 record, so they stay unmeasured (#1841, #1858).
      Re-carded (runner ops 106, 23 Nov, coordinator 103's D1: the remainder was a new file outside the claim): the fetcher is `lab/members_feed.py`, registered in manifest.toml, its test `tests/unit/test_lab_members_feed.py` on committed fixtures, no network; count lab/ room against BUDGET first
      {id: data-members; files: lab/members.py, lab/members_feed.py, tests/unit/test_lab_members*.py, manifest.toml}
- [x] Kept hot, always: the runner runs the store's keeper after the US close and before the
      London open on every trading day, a dated receipt each time; a line staler than one
      session raises an alert, and a keeper that misses its slot raises one too (DQ-12,
      DAT-07)
      {id: data-kept-hot; files: desk/keeper.py, tests/unit/test_keeper*.py; after: data-keeper}
- [x] Polite fetching: the archive's limits measured, slow and resumable requests, backing
      off on refusals, raw responses cached, an alert after six hours refused (DAT-08)
      {id: data-polite; files: desk/archive.py, tests/unit/test_archive*.py; after: data-archive-spared}
- [x] The store's keeper: its cadence, a dated receipt for each run, a restart drill; each
      bar's source and arrival time kept (DQ-12, DQ-10)
      Built (#820): desk/keeper_receipt.py; each receipt line names the newest bars that arrived, with moment and source; restart drill pinned.
      {id: data-keeper-receipts; files: desk/keeper.py, tests/unit/test_keeper*.py, desk/bars.py, tests/unit/test_bars*.py, desk/keeper_receipt.py; after: data-kept-hot}
- [ ] **First, by his ruling of 13 November:** SPY, QQQ and GLD leave the twenty for their
      UK-listed twins an ISA can hold: VUAG (S&P 500), EQQQ (Nasdaq 100) and IDTL (US
      Treasuries 20+ years), each on the London venue; every line carries an ISA and
      retail-buyable flag; the "simply holding the market" yardstick re-pointed (UNI-09)
      (built in #85: the three twins, both flags, yardstick VUAG, GLD out; remains: SPY and QQQ
      leave the master once GRID's and RUNGS's tests stop naming them (the requests to GRID and RUNGS);
      IB1T is not ISA-holdable, for the operator)
      Remains (#640): SPY and QQQ leave LINES only when the callers outside the claim read `lines.REFERENCE`
      (the requests to GRID, RUNGS and MONEY) and the tests name lines that stay; they are kept as price references (#455, #543)
      Settled (coordinator 54, 22 Nov: not his: his 13 November ruling is that SPY and QQQ leave the twenty traded lines; kept only as price references in `lines.REFERENCE`, never traded, they honour it; remains: the callers outside the claim read `lines.REFERENCE` and the tests name lines that stay)
      Waits for the three requests to GRID, RUNGS and MONEY (STATUS) to read `lines.REFERENCE`; their ids are two-digit, which the requirements guard refuses in a box, so the wait is dated and the next scribe moves it to the request when it lands. Not the operator's (coordinator 54, 22 Nov).
      {id: data-isa-twins; files: desk/lines.py, tests/unit/test_lines.py, tests/unit/test_lab_universe.py; waits: 2026-11-24}
- [x] A home for the research store on his PC, refreshed nightly, a ticker that left a list
      cleared out, and the day and list it reflects written beside it
      {id: data-research-home; files: lab/universe.py, tests/unit/test_lab_universe*.py; after: data-parked-fifth}
- [x] The hot bars' first source is the broker: he already pays for IBKR's market data, so
      the five-minute keeper reads live bars through IB Gateway's paper port, read-only, and
      the free archive is the second source and the check on it; first prove, read-only,
      that the paper account sees his live data and not the delayed kind, and if it does
      not, say which setting he must turn on (DAT-02, DAT-07)
      Built: the broker's daily bars first at the one writer (#517, #521), the keeper asks it for lines the
      archive lacks (#701), one-minute bars from IBKR (#629). Remains: a bar's own source label (a request to MONEY)
      Proved 19 Nov (#903): the paper Gateway serves live, not delayed, bars. Remains: a bar's own source label (MONEY's, #844).
      {id: data-broker-bars; files: desk/keeper.py, tests/unit/test_keeper*.py; after: data-keeper-receipts; waits: R-DATA-9}
- [x] **An ingest that cannot pile up, by construction:** one slot per ticker per minute, so a
      round never holds more than its tickers; a late round is replaced by the next, and its
      gap goes to a bounded backfill list; writes are upserts on ticker, bar size and time, so
      a retry never duplicates; each round's lag, size and refusals recorded and alerted on.
      Finished months of intraday history are sealed into compressed files for the lab to
      read, when a benchmark shows SQLite slowing (DAT-07, DQ-12)
      Verified on main (#915): slots, upserts, parked list, receipts. Remains: sealing into compressed files, only if the benchmark ever reds.
      {id: data-ingest; files: desk/keeper.py, tests/unit/test_keeper*.py, desk/bars.py, tests/unit/test_bars*.py; after: data-keeper-receipts}
- [ ] **Two databases, both owned by the one store** (his ruling, 14 November), in the desk's
      data folder, never in this public repository: `market_history.db`, long-term, every timeframe
      from an hour up plus all imported intraday history; and `market_live.db`, live 1-minute
      bars for the twenty lines and a watchlist of up to 100 within his IBKR line allowance.
      The hot keeper runs every minute in each venue's hours, IBKR first, with the free
      archive as a check; each night the day's live bars roll into `market_history.db`. Every useful
      store on C: (`kestrel2_notes\data_register.md`, tagged IMPORT) is consolidated into
      `market_history.db`, each source marked verified there. One consistent snapshot of both
      databases and the ledger is written each night for his own backup to carry (DAT-11,
      DQ-12, DQ-05)
      Built: the two databases (#442, #510), the keeper and reference series on them (#486, #524), the
      imports of Stooq, ibkr_store and mark_the_trend daily, hourly and 15/30-minute rows (#527-#566), the
      history pull and its writer (#636, #674), pages back and keeps the line's currency (#710, #725). Remains: the rest of R-RUNNER-10 (5-minute parquet, market.db,
      bars.db, per-source counts), paging back (R-RUNNER-216; #739: pull asks only 1m-30m and 1d; remains rollup of 1h, 4h, 1wk (#1243 15m/30m from 5m; #1301, #1305 2m/5m/10m from 1m; remains the monitor's filler writing them)
      into the history database as rollup:<from>; #780: a rolled bar differing from a held one is a FAULT line on stderr; #797: `python -m desk.quality` audits, backfills and re-audits the daily timeframe; remains the other timeframes, market_live.db, local Stooq and rollup sources, the runner job; #930: backfill.fill takes one ordered source list, the rollup step needs Source.ROLLUP_5M in desk/bars_schema.py, outside the box's claim; #935: the audit counts a closed session of today), the long database for daily and up
      Re-carded (coordinator 54, 22 Nov: claim scope, not his: the claim now holds desk/bars_schema.py, which the rollup step's Source.ROLLUP_5M needs; inside the desk/ ceiling)
      Remainder (runner ops 106, 23 Nov, coordinator 103's D1: the rollups and both audits are on main, #1832; the runner reads the alarm every 5 min since runner c2dd0be): the five-minute parquet, market.db and bars.db imported with per-source counts, in `lab/headstart.py`, now claimed
      {id: data-two-stores; files: desk/coverage.py, desk/history_write.py, desk/quality.py, tests/unit/test_coverage.py, tests/unit/test_history_write.py, tests/unit/test_quality.py, desk/bars.py, tests/unit/test_bars*.py, desk/keeper.py, tests/unit/test_keeper*.py, desk/bars_schema.py, lab/headstart.py, tests/unit/test_lab_headstart.py; after: data-ingest; waits: 2026-11-24}
- [ ] **THE DATA MONITOR, FIRST (his priority, 22 Nov: "data quality needs to be top priority"; "the data monitor
      should always be running"):** measured 22 Nov 09:4x, both databases: daily 1,083 of 1,084 lines fresh and
      five-minute 43 of 44, but every other span stale: 1h 0 of 1,074 (newest 23 Oct), 4h 0 of 546 (29 Jul), 1wk
      none, live 15m/30m/1m 4 of 2,097. `desk.quality` audits the daily span alone, once a night, weekdays.
      It becomes the one monitor: every database x span (5m, 15m, 30m, 1h, 4h, 1d, 1wk) x line judged against the
      venue calendar's last ended session, each gap filled (IBKR, then Yahoo named, then rollup), audited again, and
      one line printed: `data quality: <fresh>% fresh, <faults> faults, <gaps> gaps, worst <db/span/line>`
      Named HOVER (a kestrel hovers over the field watching). His 22 Nov 09:5x terms: HOVER checks every 5
      minutes, 7 days, as plain code that spends no tokens; green means no action. Only red wakes a model,
      cheapest first: Haiku reads the fault and names its kind, Sonnet fixes a kind already seen, Opus only a
      new kind. Every hour a Telegram table: both databases x every span (1m to 1wk), % fresh, faults, gaps.
      And an alarm that tells only of change (his 22 Nov ~10:00): the first red check sends one Telegram
      naming the database, span, line and why; while red, one reminder every 30 minutes; the first green
      check after it sends one "back to green, red for <minutes>" and the alarm falls silent
      The golden lines are always green or the table says why: SPY and QQQ, with VUAG (LSE) standing in for SPY
      and IITU (LSE) for QQQ, in both databases at every span (measured 09:5x: all four present, daily and
      five-minute fresh, other spans stale like the rest; VUAG has no 15m, 30m, 1m or 4h). Daily bars are read
      from ONE store: the ladder's daily files miss SPY 2022-09-28 that market_history.db holds
      wire: a runner job every 5 minutes, 7 days, and the hourly Telegram table; gate: a contract test where a
      planted stale span, missing day and stale golden line each turn the line red, and the alarm sends red once and green once
      Built (#1654): `desk.quality.hover` (freshness line, exit 0/1) and `alarm` (red once, 30-minute reminder, one green). Also built (#1658, #1689): the monitor reads the archive's six-hour outage alarm; `hover` keeps its alarm state in hover_alarm.json and prints `SEND: <message>` (the runner's line, via `announce`) when it speaks (#1736, #1769, #1782), and `table` gives the per-span line for the hourly report; #1699 adds `register` (a report, not a red); #1809 reds a missing day inside a golden line's history (golden lines only); #1832 judges both databases (market_history.db and market_live.db), the worst cell naming its database, a missing database fails loudly (history reads red on stale spans until gap filling exists). Also #1850: `table` covers both databases (one table, db-prefixed rows, each database's register); #1860: the worst cell names a golden line's fault first. Remains: the 5-minute runner job posting SEND lines and the hourly table to Telegram (runner; see STATUS), the Haiku/Sonnet/Opus escalation, gap filling for 15m-1wk, the two-store daily read.
      {id: data-monitor; files: desk/quality.py, tests/unit/test_quality.py}
- [ ] Derived spans rolled, never fetched: 15m, 30m, 1h and 4h rolled from five-minute bars and 1wk from daily,
      into the history database as `rollup:<from>` on every keeper round, so they are as fresh as their base;
      a rolled bar that differs from a held one is a FAULT, never a silent overwrite (canon B3)
      wire: every keeper round; gate: a rolled hour equals its twelve five-minute bars, and a differing held bar is a FAULT
      {id: data-rollup-hot; files: desk/rollup.py, tests/unit/test_rollup.py; after: data-monitor}
- [ ] No missing trading day: a line's gap on a day its venue traded (SPY 2022-09-28, ISF 2012-05-28 among
      6,788 market FAULTs in the ladder) is filled from IBKR, then Yahoo, or the one calendar names it a
      holiday; a line's audit lists no unnamed gap
      wire: HOVER's filler; gate: SPY's 2022-09-28 planted missing is filled, and a named holiday stays empty
      {id: data-no-missing-day; files: desk/backfill.py, desk/venues.py, tests/unit/test_backfill.py, tests/unit/test_venues*.py; after: data-monitor}
- [ ] One pounds-per-dollar history back to the earliest bar held, so no fold reads FAULT for a missing rate
      (about 5,300 in the ladder); conversion stays in its one place
      Source (his ruling 22 Nov ~10:05, free data only): FRED's DEXUSUK daily series (US dollars to one pound),
      fetched with the FRED key handed to the job by the runner's session environment alone, stored in
      market_history.db as a reference series beside the bars, through the one writer and its checks
      wire: the nightly research refresh and HOVER's filler; gate: a fold whose rate was missing reads it
      from the stored series, and a planted missing day is a named gap, never a FAULT
      Built (#1774, #1790): the nightly refresh fetches FRED's DEXUSUK (keyless) through the one writer (Source.FED_NOON) and names the pound's sessions with no rate. Remains: HOVER's filler (desk/backfill.py) filling the gaps; the ladder's half is RUNGS's own box, rungs-pound-gap
      {id: data-pound-history; files: desk/keeper.py, tests/unit/test_keeper*.py, desk/bars.py, tests/unit/test_bars*.py, lab/universe.py, tests/unit/test_lab_universe*.py, desk/backfill.py, tests/unit/test_backfill.py}
- [ ] **Data in tiers, for 4,000+ tickers** (research of 14 November, kept in the notes
      folder as `data_stack_2026-11-14.md`). Tier A: held, signalled and watched names, live
      1-minute from IBKR within his line allowance (100 now). Tier B: US breadth at 1 minute
      from one vendor feed, bought only when a strategy needs it, after the A-GATE. Tier C:
      every ticker daily. Each tier's source sits behind one adapter, so a vendor can change
      without touching a strategy. London breadth beyond IBKR's lines runs at 5 or 15
      minutes. A name moves between tiers as it gains or loses a signal or position (DAT-01,
      DAT-05)
      {id: data-tiers; files: desk/tiers.py, tests/unit/test_tiers.py, manifest.toml; after: data-two-stores}
- [x] The calendars carried past 2027, before 2027 ends
      {id: data-calendar-years; files: desk/venues.py, tests/unit/test_venues*.py}
- [x] Deep history: daily bars back to 2000 wherever the archive has them, the calendars
      carried back first; the old desk's Stooq store used only as a head start, every bar
      re-checked on entry (DAT-03, BT-09)
      Built: the calendar reaches 1993 (#594), the archive is spared (#637, #665, #668, #685). Remains: the
      bars before 2010 through the head start, once its remains (data-headstart) are met
      Built (#691): `archive.SINCE` is 1 January 2000, so the keeper's next daily round asks 2000-2009.
      Checked on main (#1101): venues.SESSION_YEARS 1993-2029, archive.SINCE 2000-01-01; nothing left to build.
      Built (#841): venues.KNOWN split into HOURS_YEARS and SESSION_YEARS, the store keeps bars from 2000, five real moves recorded. Remains: the first keeper round to fill 2000-2009 for all twenty lines and read any park. (coordinator 54, 22 Nov: not his: the keeper round is a runner job)
      Earlier (#819, #821, #822): the old Stooq store holds nothing before the archive's first bar, so no head start is left to write. `desk/store.py:152` and `desk/bars_parts.py:24` read `venues.KNOWN` (hours years, 2010-2029) as the sessions years (`venues.SESSION_YEARS`, 1993-2029), so every bar before 2010 is dropped; the US calendar's 2000-2009 sessions are pinned (#819). One session claiming desk/venues.py, store.py, bars_parts.py, lines.py and their tests: split KNOWN, point store at the sessions years, record five real moves in `real_moves` (AAPL 2000-09-29; NVDA 2000-04-05, 2004-08-06; AMD 2008-09-29, -30; confirm each on the archive's bars), then `python -m lab.headstart_days` and the keeper fill 2000-2009
      Met (runner ops 106, 23 Nov, read on market_history.db): the keeper's rounds hold 2000-2009 daily bars for 820 of 1,084 lines (559 US, 261 LSE): AAPL, NVDA, AMD, SPY, QQQ 2,515 bars each from 3 Jan 2000; lines listed later (ISF 2009, VUSA, 3LGO) start at their listing
      {id: data-deep-history; files: desk/bars_parts.py, desk/store.py, tests/unit/test_bars*.py, tests/unit/test_store*.py, desk/venues.py, tests/unit/test_venues*.py, lab/headstart.py, tests/unit/test_lab_headstart.py, desk/archive.py, tests/unit/test_archive*.py; after: data-calendar-years, data-polite; waits: 2026-11-24}
- [x] A frozen feed: a week of one bar repeated is dropped and parks a recent line
- [x] A suspension recorded on its line is no gap
- [x] A one-day crash is kept and parks until recorded; only a hundredfold bar is a wrong unit
- [ ] The old stores consolidated, never lost: once the one store holds their bars, verified by
      counts and checksums per ticker and timeframe and by one restore drill, the originals
      are deleted from C: with his explicit yes, asked then (never copied to E:, his backup
      drive). His mark_the_trend programs are retired (his word, 14 November), so
      `C:\mtt_cache` is treated like the other stores (DQ-05, OPS-07)
      {id: data-consolidated; files: lab/headstart.py, tests/unit/test_lab_headstart.py; after: data-deep-history, data-two-stores}
- [x] 2MU's five real moves recorded from a second source, or its reason confirmed
      {id: data-2mu; files: desk/lines.py, tests/unit/test_lines.py, desk/store.py, tests/unit/test_store.py}
- [x] 5QQQ's consolidation of 22 August 2024 handled, or its reason confirmed
      {id: data-5qqq; files: desk/lines.py, tests/unit/test_lines.py, desk/store.py, tests/unit/test_store.py; after: data-2mu}
- [x] SGLN's garbled weeks of 2011 handled, or its reason confirmed
      {id: data-sgln; files: desk/lines.py, tests/unit/test_lines.py, desk/store.py, tests/unit/test_store.py; after: data-5qqq}
- [x] 3LGO's missing history, and a rule for when enough has gathered
      {id: data-3lgo; files: desk/lines.py, tests/unit/test_lines.py, desk/store.py, tests/unit/test_store.py; after: data-sgln}
- [x] A stretched bar's changes recorded beside it
      {id: data-stretched; files: desk/store.py, tests/unit/test_store.py; after: data-3lgo}
- [x] A line's bars and its fault record written together, so a crash cannot part them
      Built (#832, #1210): one CSV per line, fault rows in a `fault` column, swapped in with one replace. Older stores keep an orphan `*.faults.csv` until the next nightly prepare. (coordinator 54, 22 Nov: not his: nothing here needs money, a credential, spend, a guard loosened or his machine's settings)
      {id: data-written-together; files: desk/store.py, tests/unit/test_store.py; after: data-stretched}
- [x] A pence history the archive calls pounds caught
      Built (#630, #725): every pull reaches the store through `history_write.keeper`, which turns pence to pounds once on entry; `history.run` and `pull` hand out the broker's unit by design (#1065)
      {id: data-pence; files: desk/store.py, tests/unit/test_store.py; after: data-written-together}
- [ ] The full research universe, 5,000 and more, once the grid's first pass works
      Built (#1788): 1,066 lines after the S&P 400 and 600 (docstring corrected, #1814). Remains: the Russell 1000/2000 lists from a published source, added in lab/universe.py once the grid's first pass runs clean (grid-week showed 2,810 cells failing an hour on 22 Nov); no ticker is written from memory.
      {id: data-full-universe; files: lab/universe.py, tests/unit/test_lab_universe*.py; after: data-research-home; waits: 2026-11-29}
- [x] Each line's UK tax a fact on the line, from one table of two rates: nil for a fund or
      an exchange-traded product, stamp duty for a UK share; the twenty lines each state nil,
      and one London line of the rehearsal data pays it (R-MONEY-1)
- [ ] The window before mid-April 2010 prepared
      {id: data-pre-2010; files: lab/headstart.py, tests/unit/test_lab_headstart.py; after: data-deep-history}
- [ ] Coverage and quality measured: history at least twice the longest lookback for every
      line, five years by the A-GATE; a quality score per line and desk-wide, and a cap on
      the share of lines parked (DAT-03, DQ-01)
      Built (#795): `desk/coverage.py`, pure and tested. Built (#1037): `quality.monitor` feeds it the store's real counts and the parked list, prints "coverage 0.xx", and goes red past 10% of lines parked. Built (#1059): `coverage.LOOKBACK` reads the grid's longest setting from SWEEPS (a line needs 500 sessions). Remains: the second-source part
      {id: data-coverage-second; files: desk/coverage.py, tests/unit/test_coverage*.py; after: data-second-source}
- [ ] A second source: a gap filled and a failing feed replaced from a ranked second
      source, with a staleness alarm and a register of sources; the twenty lines' bars
      checked against the broker's price of record each day once PAPER connects (DQ-03,
      DAT-07, DAT-01, DAT-02)
      Built (#1658, #1699): the staleness alarm is read by the monitor; `quality.register` names each line's newest-bar source (a report, not a red). Built (#1826): `quality.against_record(path, line, record)` reds a close more than store.AGREE (2%) from the broker's, or a missing day; `quality.check_records` and `python -m desk.quality record` ask the broker for each line's last ended session and judge it (#1834; kept in quality.py, not the monitor, to dial the broker once). Remains: the runner scheduling `record` daily after the close, PAPER answering with broker bars for the twenty lines (a request to PAPER in STATUS), a ranked second source beyond the three.
      {id: data-second-source; files: desk/archive.py, tests/unit/test_archive*.py, desk/quality.py, tests/unit/test_quality*.py; after: data-polite; waits: 2026-11-24}
- [ ] Dividends and corporate actions: total-return history for the ladder, the paper
      profit and the hold-the-market yardstick (UNI-07)
      DATA's part landed (#1659): `desk.bars.total_return(path, line)` returns a reference series' dividend-adjusted twin, any other line as held (the archive's twin, no new schema). Remains: the ladder, paper profit and yardstick call it (RUNGS, PAPER, MONEY files; requests not yet filed, the date is a placeholder hold); dividend events and a split table only if wanted.
      {id: data-dividends; files: desk/bars.py, tests/unit/test_bars*.py; waits: 2026-11-24}
- [ ] Survivorship: the research list taken as it stood on each past date, with the names
      that left it, or the bias measured and stated on every verdict (BT-09)
      Built (#1715, #1750): `Members.survived` and `members.bias(name, day)` give the stated line; not wired into verdicts (a request to RUNGS in STATUS). #1839: `members.bias` answers for every list (FTSE350 and ETFS state "past members not recorded, bias unmeasured", never raise). Remains: FTSE 350 and funds' past members. Waits for RUNGS printing the bias on verdicts (request in STATUS); a box may not name a two-digit id, so no `waits:` note.
      {id: data-survivorship; files: lab/members.py, tests/unit/test_lab_members*.py}
- [ ] UK stamp duty and taxes confirmed line by line, in one table by instrument type
      (NS-05): the table is built and the five London funds confirmed; still owed, the five
      London products seen on a contract note, the research list's London shares name by
      name, Ireland's 1%, and the default removed (R-DATA-4, R-DATA-5)
      {id: data-stamp-duty; files: desk/lines.py, tests/unit/test_lines.py; after: data-isa-twins}
- [ ] Leveraged-product lifecycle watched: an issuer's closure, a compulsory redemption or
      an ISA eligibility change on any line held or researched raises an alert (BIC-11)
      {id: data-lifecycle; files: desk/lifecycle.py, tests/unit/test_lifecycle.py, manifest.toml; after: data-isa-twins}
- [ ] Disk watched; old research files roll off by rule (OPS-07)
      Built (#1098, #1107): `python -m desk.quality` goes red under 10% free on the store's drive (`quality.disk`, called from `monitor`). Remains: the roll-off rule for old research files (needs his yes before deleting); the runner job reading the red; other monitor tests read the real drive's free space.
      {id: data-disk-rolloff; files: desk/quality.py, tests/unit/test_quality*.py; waits: operator}
- [ ] **IBKR's capacity, no new spend, 10% kept spare** (research of 14 November,
      `free_data_2026-11-14.md` in the notes folder): 90 tickers streamed live, 1-minute bars
      built from quotes; polled 1-minute bars for 27 tickers every 5 minutes, 81 every 15 and
      324 hourly as the guaranteed floor, rising toward 270, 810 and 3,240 only as far as a
      measured ramp on the paper port allows (every request counted with its error codes;
      any pacing refusal halves the rate); daily bars for every ticker (DAT-01, DAT-05)
      (runner ops 112, 23 Nov: claim adds desk/keeper_live.py, where the polled rounds must use keeper.pace and count each request, and desk/lines.py with its test, for the lines beyond today's twenty; two runs stopped on it, real_loop)
      {id: data-ibkr-capacity; files: desk/keeper.py, tests/unit/test_keeper*.py, desk/keeper_live.py, desk/lines.py, tests/unit/test_lines.py; after: data-broker-bars; waits: 2026-11-23}
- [ ] **A free collector, started now, before anything uses it:** once a day, about 300 calls
      across the free tiers he already has, each response kept raw and timestamped: a US
      second opinion on every bar (Massive's whole-market daily), a third (Tiingo), a rotating
      London audit sample (Alpha Vantage and EODHD), US macro series and release dates (FRED,
      BLS, BEA, EIA), earnings calendars (Finnhub and Alpha Vantage, cross-checked), and news
      with timestamps (Finnhub, Marketaux, GNews). NewsAPI is not used: its free terms forbid
      it. History that free tiers do not keep cannot be bought back later (BIC-06, DAT-01)
      Built (#1663, #1712, #1728, #1752): EODHD, Alpha Vantage London sample, BLS, EIA, BEA (11 sources). Remains: Alpha Vantage earnings CSV (own reader; cross-check of Finnhub dates).
      {id: data-collector; files: desk/collector.py, tests/unit/test_collector.py, manifest.toml; after: data-polite}
- [ ] **Market weather recorded before it acts:** realised-volatility sizing researched first,
      the one effect with strong published evidence; index trend and breadth from the desk's
      own bars next; VIX term structure, credit spreads and the yield curve recorded each day
      but acting only once each passes REG-07; news for event awareness, never a signal until
      proven (REG-01, REG-07, STR-20)
      {id: data-weather; files: desk/weather.py, tests/unit/test_weather.py, manifest.toml; after: data-tiers}

## Phase 2 — the money path, in simulation

- [x] One strategy template; the five frozen daily strategies (his choice: five textbook
      rules, 13 November) - **scene 2 passes**
- [x] Sizing from one capital number; stops set at entry; a leveraged line sized by what
      it controls (his rulings, 13 November: a fifth each, a stop where the market has
      fallen 10%) - **scene 3 passes**
- [ ] **Scenes 2 to 7 pass in simulation**, by the money lane's book below; the data
      lane's lengthened rehearsal data (phase 1) comes first

### The money lane's book — scenes 4 to 7, in order

> R-MONEY-54 half done (#1405): `halt.stop` takes `his`; `watch.look` takes an optional broker
> door and cancels working buys through `halt.stop` on a crash halt. Remains: PAPER passes the
> door in `desk/running.py` (R-MONEY-61). `book.py` and `desk/goflat.py` already call `halt.stop`.

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

- [ ] Connors' Double 7's as a desk rule (R-RUNGS-10): `desk/eponymous_connors_double_7.py` is a
      MONEY file, but the ladder finds every `desk/eponymous_*.py` and `lab/published_epon.py` (RUNGS)
      must name it and `test_lab_published_epon.py` count 21, so neither lane's pull request is green
      alone. Needs one session claiming both lanes' files (the runner's to grant; coordinator 54, 22 Nov: not his)
      {id: money-connors7; waits: R-RUNGS-10; files: desk/eponymous_connors.py, tests/unit/test_eponymous_connors.py, desk/eponymous_connors_double_7.py, tests/unit/test_eponymous_connors_double_7.py, lab/published_epon.py, tests/unit/test_lab_published_epon.py, manifest.toml}
      (desk/ holds 100 of its 100 allowed files and the box adds a new desk file; lab/published_epon.py and its test are RUNGS files that the lane-ownership guard refuses on a MONEY branch. Re-card it in the RUNGS book with Double 7's folded into desk/eponymous_connors.py (131 lines, already holds %B and RSI-2), reusing commit 35158bb6, and drop R-MONEY-67 rather than raise the ceiling.) (Its files span MONEY (desk/eponymous_connors_double_7.py) and RUNGS (lab/published_epon.py and its test); the lane-ownership guard refuses that on a MONEY branch. It needs the coordinator to move the box to the RUNGS lane's book, with the rule file registered under RUNGS in manifest.toml. That loosens no guard. PR 588's branch holds working code to reuse.)
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
- [x] **First, from SimCity's red night:** the send path counts orders still working, so a desk
      that died mid-send never holds more than five lines; any broker says which of the desk's
      own orders are still working; a sale left working by a dead desk with its stop resting under
      it sells twice (the desk ends short): cover that too; SimCity's night turns green and its pin (`SIX_HELD`) goes.
      Done in #163 (a note before each send; after a death the broker cancels what is working;
      night green); remains: a desk not restarted before the next open can still end short (the
      pretend broker should lapse a working order at the day's end, SimCity gain an overnight death);
      the send path's cancels are told only by the leftover order's answer; simcity.py is 399 of 400 lines
      {id: money-working; files: desk/book.py, desk/broker.py, desk/orders.py, desk/kill.py,
      desk/simcity.py, tests/unit/test_book*.py, tests/unit/test_broker*.py,
      tests/unit/test_orders*.py, tests/unit/test_kill*.py, tests/unit/test_simcity*.py;
      after: money-simcity}
- [ ] A holding whose stop was cancelled by hand gets it back the same day, or he is told at
      once (found by SimCity: 98 sessions held with no stop). First step done in #191 (the desk keeps
      every stop's level; a lost stop is on the day's list with stop, shares, level); remains: the
      put-back itself (a way to rest a stop at a level in `desk/broker.py`; `running.recover` on paper),
      the list reaching him (R-MONEY-18); the SimCity census is split (#590). The put-back on paper is on main (#657, running.recover) and the day's list names each bare line (#191); remains: nothing of MONEY's (the Pretend put-back door, `put_stop_back`, is on main; the list reaching him was re-homed to PAPER as R-RUNNER-291 and landed there, #805, the evening message naming each lost stop)
      {id: money-restop; files: desk/day.py, desk/book.py, tests/unit/test_day*.py,
      tests/unit/test_book*.py, desk/simcity*.py, tests/unit/test_simcity*.py, manifest.toml,
      desk/broker.py, tests/unit/test_broker*.py;
      after: money-working; waits: R-MONEY-53}
- [x] Emergencies in numbers: an emergency, a crash and a black swan each defined by measured
      falls, each with its action (EMG-01) {id: money-emergencies; files: desk/emergency.py,
      tests/unit/test_emergency*.py, manifest.toml}
- [x] Halts: a halt is a typed record; while one is in force the desk buys nothing and says so
      every day until it is lifted, and the day's verdict reads it; each morning one list of
      every blocker and every signal it blocked (FIL-08, NS-06, FIL-04, TRD-01). Done in #148;
      remains: a halt cancels no working buy (money-watch), SimCity lives no halted day, NS-10 reads `Record.counts`
      {id: money-halts; files: desk/halt.py, desk/day.py, desk/book.py,
      tests/unit/test_halt*.py, tests/unit/test_day*.py, tests/unit/test_book*.py,
      manifest.toml; after: money-kill, money-record}
- [x] The gate's other limits from canon B1: a day's and a week's loss and an order rate,
      refused at the gate (EMG-04 when live). Built (#467, #564, #478): loss and new-line limits, underlying cap, correlation and volatility sizing in `desk/risk.py`; Standing, per-underlying exposure and the drawdown alert reach the gate on the send path (#632, #661); correlation cap 0.90 reaches the send path (#698); remains: volatility sizing into `orders.size` with its risk-per-trade setting, after the weather box and the golden run {id: money-limits; files: desk/orders.py,
      desk/book.py, desk/day.py, tests/unit/test_orders*.py, tests/unit/test_book*.py,
      tests/unit/test_day*.py, tests/scenes/test_scenes.py,
      desk/simcity*.py, tests/unit/test_simcity*.py, manifest.toml; after: money-record, money-working}
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
- [x] **The crash watch, on the five-minute data (done in #172, `desk/watch.py`; nothing calls it yet; remains: his word against the market, the sale of every position STP-07, parking one line, a halt cancelling working buys):** every five minutes in trading hours it
      reads the newest bars of every held and watched line and the market's own; a fall that
      crosses the emergency thresholds halts all buying at once, alerts him immediately at
      any hour, and records why; the protective sell across every position (STP-07) acts on
      it once built (EMG-01, EMG-03)
      {id: money-watch; files: desk/watch.py, desk/halt.py, tests/unit/test_watch*.py,
      tests/unit/test_halt*.py, manifest.toml; after: money-halts}
- [x] A position the desk did not make is named and then sold on paper (TRD-06); no signal
      is left half-processed at the day's end (TST-08). Done in #683; open: Pretend takes a stranger sale's shares off the line's stop (R-MONEY-50)
      {id: money-stranger; files: desk/day.py, desk/book.py, desk/orders.py,
      tests/unit/test_day*.py, tests/unit/test_book*.py, tests/unit/test_orders*.py,
      desk/simcity*.py, tests/unit/test_simcity*.py, manifest.toml; after: money-halts, money-working}
- [x] SimCity widened: a hundred seeded worlds with faults and drills, not one rehearsal
      world (TST-05, TST-22). Done in #150; remains: a nightly run on his PC with its records, worlds
      that deal every line's months alike, which worlds and code/data versions in the record
      {id: money-worlds; files: desk/simcity.py, tests/unit/test_simcity*.py;
      after: money-simcity}
- [ ] Small and illiquid trades: a trade whose expected gain is under twice its round-trip
      cost is flagged, and no position is above 1% of its line's twenty-day traded value
      (SIZ-10, TRD-10). On main: the 1% cap in `orders.size` (`orders.traded_value`, `LIQUIDITY`, #1690) and in `orders.gate`, which takes `traded` (#1796), fed by nothing yet. Remains: `day._buy` feeding it (restore 3bf88fa2's day.py change; fixtures volume 10**7 in test_restop, test_running, test_running_tell, which needs a card claiming them); the expected-gain flag (TRD-10)
      (runner ops 108, 23 Nov, stall watch 01:0x: claim adds tests/unit/test_restop.py; the two running tests' fixtures are PAPER's, set first by paper-small-volume)
      {id: money-small; files: desk/orders.py, desk/day.py, tests/unit/test_orders*.py,
      tests/unit/test_day*.py, desk/simcity*.py, tests/unit/test_simcity*.py, manifest.toml,
      tests/unit/test_restop.py; after: money-limits, paper-small-volume}
      (coordinator 54, 22 Nov: not his: SIZ-10 and TRD-10 fix the numbers, a flag under twice the round-trip cost and a cap at 1% of the twenty-day traded value)
- [ ] Time and gaps: a time stop after the strategy's declared holding period; a gap that
      jumps the stop held against the loss limit; a hold limit and gap sizing for the
      leveraged lines (STP-11, STP-10, SIZ-09). Step 1 on main (#845): time stop in `strategy._run`, `orders.gap_loss`/`gapped`. Step 2 on main (#1449): the time stop ages from the book's fill date. Step 3 on main (#1504): a gapped stop halts buying (`day._stand_down`). Remains: each rule's hold limit from its own sell logic (his ruling Sat 21 Nov 21:33; moves golden days, strategy files outside this claim, B5), then `orders.gapped` at `book.collect`.
      {id: money-time-gaps; waits: 2026-11-24; files: desk/day.py, desk/orders.py, desk/strategy.py,
      tests/unit/test_day*.py, tests/unit/test_orders*.py, tests/unit/test_strategy*.py,
      desk/simcity*.py, tests/unit/test_simcity*.py, manifest.toml, desk/book.py, tests/unit/test_book*.py,
      desk/eponymous_*.py, tests/unit/test_eponymous*.py, desk/grimes.py, tests/unit/test_grimes*.py, tests/scenes/test_scenes.py; after: money-limits}
      (runner ops 106, 23 Nov, coordinator 103's D1: claim widened to the files its Remains name, the rules' sell logic and book.collect; the golden days move on his recorded yes)
      (coordinator 54, 22 Nov: settled: his yes to the golden days moving is recorded in STATUS, R-MONEY-62)
- [x] Fills realistic: spread and slippage in every fill, from the one cost model (TRD-09)
      {id: money-fills; files: desk/broker.py, desk/orders.py, desk/book.py,
      tests/unit/test_broker*.py, tests/unit/test_orders*.py, tests/unit/test_book*.py,
      tests/unit/test_day*.py, tests/scenes/test_scenes.py,
      desk/simcity*.py, tests/unit/test_simcity*.py, manifest.toml; after: money-invariants, money-working}
- [x] The golden reference run committed; a change to a size, a stop or a threshold is
      replayed on it before it lands (TST-21, GOV-09, canon B5)
      {id: money-golden; files: *; after: money-fills, money-limits, money-halts}
- [x] Every trade's whole story: signal, intent, risk decision, order, fill and the bar it
      read, linked by ids; profit attributed by strategy, line, holding time and cost
      (TRD-11, TRD-12, DQ-08) On main: `book.story`/`attributed` (#1468); `book.told` trade stories with strategy, bar read and days held, run in SimCity (#1486); `book.chain` decision-time id chain in story.csv (#1509). Step 1 on main (#1716): chain kept before the send (`book.intend`), strangers chained. Step 2 on main (#1777): the sized shares as `Link.asked` beside `filled`. Step 3 on main (#1805): SimCity's trips scenario attributes profit by strategy, line, holding time and cost (`book.attributed`).
      {id: money-story; files: desk/story.py, desk/book.py, desk/day.py,
      tests/unit/test_story*.py, tests/unit/test_book*.py, tests/unit/test_day*.py,
      desk/simcity*.py, tests/unit/test_simcity*.py, manifest.toml; after: money-fills, money-limits}
      (coordinator 54, 22 Nov: settled: its Remains were rewritten to name the real jobs, #1573)
- [ ] Money honestly counted: interest on idle cash, with the risk-free rate in every
      Sharpe; currency gains and losses on dollar holdings reported apart from trading
      profit; a fall from the book's highest point alerted on paper (BIC-03, BIC-04, BIC-05). BIC-05 on main (#1516); BIC-04 on main for closed trades (#1542, #1569) and open holdings (#1596); BIC-03 interest told daily at `RISK_FREE` beside profit (#1560, #1584). Remains: `RISK_FREE` in every Sharpe (lab, R-MONEY-65), then drop "interest inside the day's profit" from the box: interest stays beside profit as its own column and daily line, since profit must equal the ledger (#1861, decided). `RISK_FREE` in every Sharpe is RUNGS's request R-MONEY-65; the saved record is money-saved-fx, done
      {id: money-honest; waits: R-MONEY-65; files: desk/day.py, desk/book.py, tests/unit/test_day*.py,
      tests/unit/test_book*.py, tests/scenes/test_scenes.py, desk/simcity*.py, tests/unit/test_simcity*.py, manifest.toml;
      after: money-fills}
- [x] Currency and interest kept in the day's saved record, beside profit, so a later day
      reads them back unchanged; no golden day's numbers move (R-MONEY-66, split from
      money-honest by runner ops Sun 22 Nov 08:5x: that box's claim lacked these files and
      ended red twice; its other remains wait on the operator's golden ruling and on lab/).
      {id: money-saved-fx; files: desk/day.py, desk/day_parts.py, desk/day_money.py,
      tests/unit/test_day*.py, desk/simcity*.py, tests/unit/test_simcity*.py, manifest.toml;
      after: money-fills}
- [ ] (Every box adding a public function to strategy, orders, broker, book, day or kill also
      needs `desk/simcity.py, tests/unit/test_simcity*.py` in its files, one session at a time;
      a function no scenario runs turns the check red: halts and limits among them.)
      {id: money-census; files: desk/simcity*.py, tests/unit/test_simcity*.py, manifest.toml;
      after: money-watch, money-stranger,
      money-golden, money-story}

- [x] **ONE DOOR FOR PRICES, slippage** (his 22 Nov ~10:00, "paramount": every price is read from market_history.db or market_live.db alone): `lab/slippage.py:104` reads `bars.daily(home / keeper.HOT, line)`,
      not the `daily/*.csv` files nothing writes any more; wire: its study; gate: its contract test on a database fixture
      {id: money-door-slippage; files: lab/slippage.py, tests/unit/test_lab_slippage*.py}
- [ ] One door, the desk's pound: the day, its money, the book and SimCity take the rate from `keeper.pound`
      (desk/day.py:201, 241, 274; day_money.py:23; book.py:318; simcitycmd.py:176; simcity_fills.py:111);
      `rates.csv` stays an audit record and is never read as a source; wire: the trading day and SimCity;
      gate: a test where `rates.csv` disagrees with the database and the database wins
      (runner ops 108, 23 Nov, stall watch 01:31: claim adds desk/book_parts.py, where the rates record is read, and desk/simcity.py, which reads it through `book.pounds_per`; two sessions stopped at that wall)
      {id: money-door-pound; files: desk/day.py, desk/day_money.py, desk/book.py, desk/simcitycmd.py, desk/simcity_fills.py, tests/unit/test_day*.py, tests/unit/test_book*.py, tests/unit/test_simcity*.py, desk/book_parts.py, desk/simcity.py; waits: 2026-11-24}
- [ ] A round never sends more orders than its step's time allows (coordinator 93's 20:5x ruling, option 2):
      each market order waits `paper.FILL_SECONDS` (120 s) and the runner ends the desk step at 900 s, so a zoo
      round of many one-share orders died mid-send (20 Nov, failure pattern 24). The step's time moves from
      `desk/simcity_incidents.py:76` (STEP_SECONDS) to `desk/paper.py` beside FILL_SECONDS, one home, never a copy;
      a round sends at most (STEP_SECONDS - margin) // FILL_SECONDS orders, the desk's own first, and the rest are
      not sent, each kept in the day's record as carried to the next step. Opus, A6 blind review (money path).
      Rejected: zoo orders that do not wait (a second send path), a longer timeout. The zoo goes back on only
      after this lands and a zoo-on rehearsal says GO; gate: a test, written first, where a planted round of 20
      one-share orders sends only the cap and names the rest carried
      (runner ops 106, 23 Nov, coordinator 103's D1: desk/paper.py is PAPER's; its constants come from paper-step-time, then this box points simcity_incidents at them and drops its own)
      (money-time-gaps waits to 2026-11-24: 5 sessions in a row landed no change, the doctor asks why; money-honest waits on R-MONEY-65, said in #1861; money-door-pound parked a day, MONEY-s10, canon A8)
      (#1823: cap built, MAX_ORDERS = 7, the rest carried; constants sit in desk/day.py. Remains: move STEP_SECONDS, STEP_MARGIN, MAX_ORDERS to desk/paper.py (R-MONEY-69); Blocker.CARRIED in desk/halt.py; blind review (A6); zoo-on rehearsal GO before the zoo returns)
      {id: money-round-cap; files: desk/day.py, desk/simcity_incidents.py, tests/unit/test_day*.py,
      tests/unit/test_simcity*.py; after: paper-step-time}
- [x] **Fault, the deep run (A3: a red deep test is a fault):** (#1813: ledger opened once per change, 50,412 -> 228 opens on the fixture night) deep SimCity on 067062cd ended 22 Nov 22:37
      "stuck in the worlds: no end in 7200 s" at `desk/book_parts2.py:48` (`_ledger`). The ledger file is read and
      parsed whole on every `book.fills` and `book.found` call, and the day and the book call them about twenty
      times a simulated day (desk/day.py:94-491, desk/book.py:145-441, desk/day_money.py:36, 79), so a world's
      fourteen months re-read a growing file thousands of times: the twin of #1755 and #1704 (failure pattern 26).
      Fix at the source: the ledger is read once per change of the file, never once per call; no retry, no longer
      timeout, no second reader. Gate: a test, written first, where a planted ledger of 2,000 fills is opened at
      most once across a simulated day's calls with no fill written, and once more after `_record` adds one
      {id: money-ledger-once; files: desk/book_parts2.py, desk/book.py, desk/day.py, desk/day_money.py,
      tests/unit/test_book*.py, tests/unit/test_day*.py, tests/unit/test_simcity*.py}

- [x] **Grimes's ten in the zoo (coordinator 103 G1 ruling, 22 Nov 23:5x; G27):** (met by #1696: `desk/intraday.py` imports `GRIMES` and `test_intraday_zoo.py` names all ten; found by #1900's run, test run on main by runner ops 112, 23 Nov) `manifest.toml:107` says the zoo
      holds "Grimes's ten among the daily", but `desk/intraday.py` imports nothing of `desk/grimes.py`, so that line is
      false and #1783's guard (every desk rule reached by the rulebook or the zoo) is red on main. Wire the zoo in
      `desk/intraday.py` to reach `desk/grimes.py`'s ten setups (the AG catalogue) as daily rules; the zoo stays OFF
      (ZOO_ON off by default; Z2 and a zoo-on rehearsal GO unchanged), one share, a paper MACHINERY TEST, never
      evidence (CANON B6). No exemption in the guard (a loosening). Gate: a test, written first, red on main, where
      the zoo's listing names all ten setups. Opus, A6 blind review (money path). #1783 relabels after this lands
      desk/grimes.py is at 799 lines: what moves out goes to desk/grimes_parts.py, registered in the manifest first
      {id: money-grimes-zoo; files: desk/intraday.py, desk/grimes.py, desk/grimes_parts.py, manifest.toml, tests/unit/test_intraday*.py,
      tests/unit/test_grimes*.py}
- [ ] **SimCity's gaps on lines before their first bar** (coordinator 107 E1, deep 23 Nov 00:44, SIMCITY RED):
      the night's gap scenarios pick 2MU, 5QQQ, IB1T, SMGB, SPCX and VHYG on days before their first bar ("no bar
      before the gap day, its gap is unrunnable", 8-9 of 20 worlds, first world 1), and its conformance scenario
      stops on a line with no bar the session before ("the desk stops on no day", 20 of 20 worlds, world 0 day 56:
      SMGB has no bar of 2019-08-02). Hypothesis: the scenarios choose lines unlike the trading day, which leaves a
      line out until its first bar; the trading day itself is not affected. Also judge here "a gap down to the low
      leaves a stop's loss inside the gap limit" (3 worlds, first world 1) and say whether "0 round trips, five rules
      never held a line" is these halts or a fault of its own. Fix where the line is chosen, never a special case per
      line; if the fix needs a file outside this claim, stop and say so. Gate: a test, written first, red on main,
      replaying world 0 to day 56 and world 1's gap scenario on a fixture with a late-starting line
      {id: money-simcity-firstbar; files: desk/simcity*.py, tests/unit/test_simcity*.py}
- [ ] **Shares under a broker stop, taken in and sold** (coordinator 107 E1, deep 23 Nov 00:44): "shares the book
      lacks, under a stop at the broker, are taken into the book and sold" in 6 of 20 worlds, first world 4: the
      stranger path adopts shares that already sit under a working stop and sells them, which can sell twice. Find
      where the adoption reads the broker's stops; a stranger under a stop is booked with that stop, never sold on
      top of it. Opus, A6 blind review (money path). Gate: a test, written first, red on main, replaying world 4
      {id: money-stranger-stopped; files: desk/book.py, desk/book_parts2.py, tests/unit/test_book*.py,
      desk/simcity*.py, tests/unit/test_simcity*.py}
- [ ] **Scenarios for four book parts** (coordinator 107 E1, deep 23 Nov 00:44 census: 67 parts, 4 with no
      scenario): `book.attributed`, `book.chains`, `book.conformance_cost` and `book.told` are run by no SimCity
      scenario; give each one in the night's census, no change to the parts themselves. Gate: the census test
      names zero parts without a scenario
      {id: money-census-book; files: desk/simcity*.py, tests/unit/test_simcity*.py}

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
- [x] Morning and evening messages, and an alarm on silence (#142; remains: paper-running calls it, something outside the desk runs `messenger.watch`, his bot key in the desk's environment)
      {id: paper-messages; files: desk/messenger.py, tests/unit/test_messenger.py,
      manifest.toml}
- [x] Unattended running, and recovery from a restart (#152; remains: the process that asks for a step, the price store's door, DATA's rates)
      {id: paper-running; files: desk/running.py, desk/placing.py,
      tests/unit/test_running.py, tests/unit/test_placing.py, manifest.toml;
      after: paper-adapter, paper-stops, paper-messages}
- [x] **No paper order until the money lane's kill switch has been drilled** (EMG-02) (#155: drilled once each day at the step's first work)
      {id: paper-kill-drilled; files: desk/running.py, tests/unit/test_running.py;
      after: money-kill, paper-drill, paper-running}
- [x] Conformance trades, on paper, one London and one US line, each in its market's hours:
      a market buy at the open; the resting stop placed, triggered, and cancelled on a sale;
      a partial fill if the paper broker gives one; a rejection. Each real result recorded
      beside the pretend broker's, and the pretend broker fixed where they differ.
      (Waits for 2026-11-16: the trial trades need London and US markets open, and weekend markets are shut.)
      Done: Monday 16 Nov's London and US files compared; ids, the stop step, the gate's refusal, the broker's reasons and the soak command landed (#433, #452, #488, #512, #565, #572, #610, #686). The stop step is judged on fills and holdings (#779). Remains: a part fill is unseen (the paper broker gave none at 1, 16 or 18 shares); the next live US run to confirm 6 of 6
      {id: paper-conformance; files: *; after: paper-gateway, paper-check, paper-stops,
      paper-drill; waits: 2026-11-16}
- [ ] The desk's own process supervised: one supervisor, restarts proven by killing it,
      health judged from outside by dated receipts, surviving a reboot, a dropped network
      and a broker disconnect; a ledger of operator actions proving seven days without one,
      bar the ruled Gateway re-login (OPS-01, OPS-02, OPS-04, OPS-10, NS-01)
      Remains: the step is the first registered job (#490) and `python -m desk.supervisor tell` sends what health finds (#499). The hours (05:30-22:00 UTC) and the 03:00 restart window are done (#1631, #1639). Still to do: the kill drill on the real step, seven days counted (time, not code). Windows starting the supervisor is its own box below, which waits on him (coordinator 54, 22 Nov: a new Windows task is persistent config on his machine; the rest is not his)
      {id: paper-supervised; files: desk/supervisor.py, tests/unit/test_supervisor.py,
      manifest.toml; after: paper-running; waits: 2026-11-29}
- [ ] Windows starts the supervisor and `tell` at boot: a new Windows task on his PC (his yes in chat, Sun 22 Nov 09:5x: "Yes, add it")
      {id: paper-supervisor-windows; files: desk/supervisor.py, tests/unit/test_supervisor.py;
      after: paper-supervised}
- [x] The running process always on main's latest code, and a money-path change reaching
      it only at a safe point, never mid-send (OPS-05, OPS-16) (#752: the supervisor pulls main fast-forward only between runs with every job's lock held; a failed pull is a receipt and the old code runs on; remains: Windows starting the supervisor)
      {id: paper-on-main; files: desk/supervisor.py, tests/unit/test_supervisor.py}
- [ ] The messages: a start-of-day card by 05:40; an end-of-day summary with the profit,
      the streak and the verdict; a line on every change of state and "the desk is not
      trading" by 09:30 UK; urgency levels without storms; one messenger with a delivery
      record, the merge line and the runner's alerts behind the same door (MSG-02, MSG-03,
      MSG-04, MSG-09, MSG-11)
      Remains: hourly P&L (#471, #492), the kill and halt line (#502) and the email fallback (#484, wired into the step in #1309; the runner must hand SMTP_*, a preflight line is owed) landed; desk/messenger.py is at its 400-line limit and desk/ has 92 of 10,500 lines left, so the new messages are a fold inside the desk/ ceiling: shrink or merge messenger code first, as split-desk-keeper did, never a ceiling raise (coordinator 54, 22 Nov: re-carded so it is not blocked; a raise would be his). The daily messages end the last-day lines with the verdict and streak (#1636, MSG-03); the 05:40 start-of-day card (#1864; only the card moved, notes and reminders stay at his 08:00) and the 09:30 "not trading" line (#1852 wired `messenger.idle` into `running._say`; #1880 proves it through the step) landed; still owed: the SMTP preflight line in desk/command.py (claim must add it; the runner must hand SMTP_*) (the streak shows as N of 10, #1665; the streak-above-0 test landed, #1675; messenger.py shrunk to 395 lines, #1698). The evening message now names each lost stop (#805); messenger split to 349 lines (#782)
      (runner ops 112, 23 Nov: claim adds desk/command.py for the SMTP preflight line, the one item left; the 2026-11-24 wait was that missing file, so it is lifted)
      {id: paper-cards; files: desk/running.py, tests/unit/test_running*.py, tests/unit/test_command.py, desk/messenger.py, desk/messenger_parts.py, manifest.toml,
      tests/unit/test_messenger.py, tests/unit/test_messenger_parts.py, desk/command.py; after: paper-messages, paper-running}
- [x] FIRST-LIGHT counted by the desk itself: ten consecutive clean days, and a day that
      sent nothing cannot be green (NS-10) (#511: `desk/streak.py`; remains: showing the streak in the day's message and the pre-flight line)
      {id: paper-first-light; files: desk/streak.py, tests/unit/test_streak.py,
      manifest.toml; after: paper-running}
- [ ] An independent watcher of the supervisor, which is restarted weekly (OPS-03)
      {id: paper-watcher; files: desk/watcher.py, tests/unit/test_watcher.py,
      manifest.toml; after: paper-supervised}
- [x] Backups: the fill ledger and the day records copied twice, one copy off the PC, and a
      restore drilled every quarter (DQ-05, DQ-09) (#515: `desk/records_kept.py`; remains: the runner calling it nightly, runner-side work, coordinator 54, 22 Nov: not his)
      {id: paper-backups; files: desk/backup.py, tests/unit/test_backup.py, manifest.toml}
- [ ] The day's extras: missed winners, blocked signals, and the running cost set against
      net profit each week (MSG-13, NS-14) (coordinator 54, 22 Nov: it comes after paper-cards and edits the same messenger file; not his)
      {id: paper-extras; files: desk/messenger.py, tests/unit/test_messenger.py;
      after: paper-cards}

- [x] **ONE DOOR FOR PRICES, the command's pound** (his 22 Nov ~10:00, "paramount": every price is read from market_history.db or market_live.db alone): `command_parts.rates` asks `keeper.pound`, never
      `rates.csv` first nor IBKR or the archive directly (desk/command_parts.py:36-64); conformance never falls back
      to `archive.fetch` (conformance_parts.py:70); wire: running and the command; gate: a test with the broker and
      archive stubbed to fail, the rate still read from the database (#1674; remains: `desk/command.py` still passes `broker=` to `rates` as an ignored parameter and its preflight text says "kept before"; a later card removes both and `pound.log`)
      {id: paper-door-pound; files: desk/command_parts.py, desk/conformance_parts.py, tests/unit/test_command*.py, tests/unit/test_conformance*.py}
- [x] The desk step's time beside the fill wait (#1868) (split from money-round-cap by runner ops 106, 23 Nov: the lane wall bars
      MONEY from desk/paper.py): `STEP_SECONDS, STEP_MARGIN = 900, 60` in desk/paper.py beside `FILL_SECONDS`, the one home
      money-round-cap then reads; gate: a test that (STEP_SECONDS - STEP_MARGIN) // FILL_SECONDS is 7
      {id: paper-step-time; files: desk/paper.py, tests/unit/test_paper*.py}
- [ ] Running fixtures carry a traded volume (split from money-small by runner ops 108, 23 Nov: the lane wall bars
      MONEY from these tests): the fixtures of tests/unit/test_running.py and tests/unit/test_running_tell.py give
      each line a volume of 10**7 shares a day, so the 1% liquidity cap money-small feeds from the trading day
      never shrinks their orders; no behaviour changes today; gate: both files green on main with the volume set
      {id: paper-small-volume; files: tests/unit/test_running.py, tests/unit/test_running_tell.py}

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
- [ ] Runs seven days without stopping. Remains: the week's clone runs pre-#1210 code against the new-format store (2,810 cells fail each hour since 21 Nov 03:21 UTC: #1370, and stale `.faults` notes swept as phantom tickers, filter restored in #1612), so the seven days restart unbroken once the runner brings it to current main and restarts the job; read `sweep.unbroken` on or after 28 Nov and tick if 7 days. A pass that raises is now logged and the week carries on (#1562); each pass line names its commonest failure causes (`why`, #1563; the log line carries them, #1748); the 15 Nov stop's trigger is unproven {id: grid-week; waits: 2026-11-28; files: lab/batch.py, lab/sweep.py,
      lab/tune.py, tests/unit/test_lab_batch.py, tests/unit/test_lab_sweep.py,
      tests/unit/test_lab_tune.py}
- [x] Each strategy judged on its own declared universe; the everything-on-everything grid
      kept as a transfer study, never a verdict; sweeps on the declared universe (LAD-01,
      LAD-13) {id: grid-declared; files: lab/sweep.py, tests/unit/test_lab_sweep.py}
- [x] A full sweep within a weekend, its time measured (LAD-10). Remains: nothing; a cold transfer study took 17 min, the declared pass about 8 min, against 48 h {id: grid-weekend; files: *}

- [x] **ONE DOOR FOR PRICES, the transfer study's pound** (his 22 Nov ~10:00, "paramount": every price is read from market_history.db or market_live.db alone): `lab/transfer.py:170` passes
      `history_bars.pounds(home)` to `ladder.rates`, never the archive; wire: the grid-transfer job; gate: its test
      with the archive stubbed to fail
      Remains: nothing (#1683: `lab/transfer.py` takes the pound from `history_bars.pounds`) {id: grid-door-pound; files: lab/transfer.py, tests/unit/test_lab_transfer*.py; after: rungs-door-pound}

### The rungs lane's book

**Lane objective:** in-sample and out-of-sample folds: a strategy's history cut into folds,
each judged after costs, the two shown side by side, and the verdict given on the worst
fold; every fold is a trial the luck rung counts (canon B6, AG-01).

- [x] **ONE DOOR FOR PRICES, the ladder's pound** (his 22 Nov ~10:00, "paramount": every price is read from market_history.db or market_live.db alone): `ladder.rates` loses its `archive.fetch` default and the
      `ladder/pound.jsonl` table (`rung.kept_closes`), so every caller passes `history_bars.pounds`; montecarlo's
      pound and bars come from the database; wire: the ladder sets and montecarlo; gate: `ladder.rates()` with no
      source fails loudly
      {id: rungs-door-pound; files: lab/ladder.py, lab/rung.py, lab/montecarlo.py, tests/unit/test_lab_ladder*.py, tests/unit/test_lab_rung*.py, tests/unit/test_lab_montecarlo*.py}
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
      Remains: the weather (REG-01) and handing home regimes to the desk (before paper). Built: `weather.edges` per fold (#866) and `weather.against_trend` (#875), wired into no verdict; `weather.contest` and `weather.write` (#907: calm/shallow/broad layers, worst fold beside trend's, 3 trials, an unscorable layer "cannot score") are built; remains (R-RUNNER-205): run the contest as a plain-code job on the real store, run volatility, drawdown and breadth through them on the real store with trial count and worst fold, wire the winners into the regime rung, then macro series from the data-collector
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
      (#120). Built: the first rung waits for a figure on file (#139); the Double 7's
      figure written down (#141); dry run on real SPY 2011-19 ran all five rules (#143).
      A replication may stand in for an author's figure, labelled second hand; best free figures
      written down, none on file (#169, #186). BLOCKED (do not hand out): waits on SPY and
      sessions from 1993 (R-RUNGS-5, 9), the Double 7's rule (R-RUNGS-10), RSI-2 buying under 10
      (R-RUNGS-14), the index from 1983 (R-RUNGS-13), all five still open (#195). Remains also: `folds`/`regime`/`stress` passing reproductions on
      {id: rungs-reproduce; files: lab/reproduce.py, lab/rung.py,
      tests/unit/test_lab_reproduce.py, tests/unit/test_lab_rung.py;
      waits: R-RUNGS-5, R-RUNGS-9, R-RUNGS-10, R-RUNGS-13, R-RUNGS-14}
- [x] Stress scenarios: the 2020 crash, flash crashes, a leveraged product's gap (2008 lies
      before the history) (TST-06). Built: `lab/stress.py` (#140). Remains: nothing calls it;
      judged by the loss limit when MONEY sets it (R-RUNGS-11); first run on real bars
      {id: rungs-stress; files: lab/stress.py, tests/unit/test_lab_stress.py, manifest.toml}
- [x] **The eleven rungs made trustworthy before any verdict counts**, the old desk's
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
      audit found kept as a case that must fail (LAD-09, LAD-03, LAD-08). Built: all eleven
      modules, each proven alone (#343-#365, #412). Remains: the Sharpe a trade has one home (#746); the ladder judges by three of them
      (costs #438, ci #440, cpcv #445 declare a RUNG; "rungs built" counts 4 of 12 (the map names twelve, each row marked built or `no RUNG`, #1625); regimes #1165 now declares one too; rungs 7, 10, 11, 12 still undeclared or gate-less); wiring the rest, the clustered
      trials (#379 built) into the verdict, the gap-through loss (R-RUNNER-187 declined, #409). Also remains (R-RUNNER-191): market.fit, rung_dsr.chance vs deflated._deflated, rung_regimes/rung_bootstrap bands (rung_ci keeps its own, open at both ends, #815; rung_benchmark reads rung.mean_and_error, #827; one home for a mean and its interval, rung.interval, #838; rung_dsr's wrapper of the paper's formula gone, #848); Fold/Walked out of rung_folds.py (R-RUNNER-191 part b, blocked on R-RUNGS-29; part a, the golden ladder verdict test, #919); ease-switch-on done (R-RUNGS-30 #942; EASED = True, golden verdicts re-pinned, #993); the ladder pool yields memory (#1082); EASED tests pinned per test, registry strict again (#1124); the key carries the capital (#1201); rung 5 regimes declares its RUNG (#1165); `Candidate` refuses any unrun rung (#1256); the scorecard rule is named constants in lab/verdict.py, not yet wired into judge() (#1411); the results file is compacted by `Kept.compact()` in `door` (#1420); rung 4's judge `banded` lives in lab/market.py, lab/rung_beta.py is an empty docstring awaiting deletion by the coordinator, the map counts rungs built at 5 (#1425). Built since: a cell's key carries its own rule's code, so an edit re-judges only that rule (#912); the retail rung stands in a basket row behind EASED (#927, map row 12; remains: `ladder_sets.baskets()` passing `against=` to `basket.row`, R-RUNGS-30)
      {id: rungs-trustworthy; files: *; after: rungs-beta}
- [ ] **LADDER READY, the cards (his ruling, 15 November: "done properly and to elite desk
      specifications", then the ladder runs 24x7).** Ranked; each card one test and one change:
  - [x] L1 TAPE-CACHE: a rule on a line simulated once into a kept tape (trades, daily
        returns), keyed by the rule, the engine, the bars and the rates; each rung's result
        keyed by the tape and that rung's own code. Changing a rung re-simulates nothing.
        Built: one tape per (rule, line) cut by date (#337, #378), compressed (#555), rates priced after it (#398)
        {id: rungs-tape-cache; files: lab/tape.py, tests/unit/test_lab_tape.py}
  - [x] L2 THE RUNG MAP: each of the eleven rungs above named to its module and test, built
        or not, in `lab/ladder.py`'s docstring; the later cards follow it
        {id: rungs-rung-map; files: lab/ladder.py, tests/unit/test_lab_ladder_map.py; after: rungs-tape-cache}
  - [ ] L3-L13 ONE CARD PER RUNG, built or proven to one standard, one module each so they
        run in parallel: a planted edge passes; five hundred noise cells pass at about the
        stated rate; a power curve at three effect sizes; a broken copy caught; each defect
        of the old desk's rung audit kept as a case that must fail
        Decision e: no dead rungs; dsr merges into deflated, placebo into shuffle, bootstrap into ci, sample into rung
        1's trade minimum, benchmark into market; wire: each on verdict.judge's path; gate: a ladder test fails when
        any lab/rung_*.py is off that path (rungs_built equals the map)
        Gate done (#1676): the registry test pins the rung modules off the path, now seven after empty rung_beta.py was folded away (#1740) (benchmark, bootstrap, dsr, placebo, retail, sample, stops); it may only fall.
        Remains: wire or merge each (each needs lab/ladder.py, manifest.toml and its target in the claim; merges need R-RUNGS-29), then pin 'waiting is empty'. Step 1 built (#1844): rung_bootstrap folded into rung_ci (off-path modules 7 to 6, FOLDED pin until it is wired); next: benchmark, dsr, placebo, sample, retail, stops, each needing its target in the claim; rung_stops is the stop-rule study, rename it out of rung_ (e.g. lab/stop_rules.py). Registry test reads the real rungs from `rung.found()` (#1768)
        {id: rungs-each-rung; files: lab/ladder.py, tests/unit/test_lab_ladder.py, lab/rung_*.py, tests/unit/test_lab_rung_*.py, lab/stop_rules.py, tests/unit/test_lab_stop_rules.py, manifest.toml; after: rungs-rung-map; waits: R-RUNGS-29}
  - [x] L14 one clustered set of trials for the deflated Sharpe, its spread measured
        {id: rungs-clustered-trials; files: lab/trials.py, lab/rung_dsr.py, tests/unit/test_lab_trials_clustered.py; after: rungs-rung-map}
  - [ ] L15 the blind review of the whole ladder (R-RUNNER-40), every blocking finding fixed
        {id: rungs-blind-review; files: lab/ladder*.py, tests/unit/test_lab_ladder*.py; after: rungs-each-rung, rungs-clustered-trials}
  - [ ] L16 the gate: the runner runs the catalogue 24x7, each change re-running only its
        own specs, each set's table published with "rungs built: n of 12"
        {id: rungs-gate; files: lab/ladder_sets.py, lab/ladder_pool.py, tests/unit/test_lab_ladder_pool.py; after: rungs-blind-review}
  - [ ] L17 A PASS CAN EXIST: `verdict.UNRUN` names plateau on every cell and `goes()` needs no rung unrun, so
        no cell could ever go forward (blind review 22 Nov 09:2x). Plateau judged on each rule's B5 variants
        (the centre of a plateau, canon B6), so a cell with a real edge can pass; a planted edge goes forward
        A rule with no settings is declared NOT APPLICABLE for plateau, reviewed, never UNRUN by default (decision a);
        wire: verdict.judge on every cell; gate: a planted edge goes forward and a no-settings rule is not blocked
        Step 1 landed (#1660): plateau.Surface and plateau.judged, verdict.judge(surface=); no surface stays UNRUN. Built: `plateau.Fixed` (#1702) and `plateau.of(rule, book, firsts)` builds a cell's Surface or FIXED (#1742).
        Remains: wire it: lab/ladder.py and lab/ladder_sets.py pass `surface=plateau.of(c.strategy, rulebook.specs(), firsts)` into verdict.judge (changes test_lab_ladder.py and test_lab_ladder_epon.py; the claim must name those four files)
        {id: rungs-plateau-wired; files: lab/plateau.py, lab/verdict.py, lab/ladder.py, lab/ladder_sets.py, tests/unit/test_lab_plateau.py, tests/unit/test_lab_verdict.py, tests/unit/test_lab_ladder.py, tests/unit/test_lab_ladder_epon.py; after: rungs-faults-not-answers; waits: operator}
  - [ ] L18 TRIALS COUNTED HONESTLY: `trials.family` counts every line ever entered and never shrinks (3,435 per
        rule against ~1,017 judged), luck then needs t>=4.6 and no line reaches it (highest 4.36). The family is
        the set's own lines, clustered (L14) and passed into `deflated.read`; a known-answer case pins both bars
        Step 1 landed (#1714): the luck rung is report-only (`deflated.OWN`), the deflated Sharpe the gate; `verdict.every` no longer counts the luck rung (#1792); step 2 (#1771): `trials.daily` and `deflated.judge_lines` judge a rule on its own clustered lines, known answer pinned. Remains: wire `judge_lines` in place of `deflated.judge(..., family - 1)` in lab/verdict.py, lab/ladder_sets.py, lab/ladder.py, lab/ladder_pool.py, lab/basket.py (tests: test_lab_verdict.py, test_lab_ladder_sets.py, test_lab_ladder_pool.py), then delete `trials.family`; book the planted loss in `trials.daily` on the window's last day
        One correction, not two (decision b): the deflated Sharpe on clustered effective trials is the gate, the
        Bonferroni luck rung is report-only, and a rule is also judged on its pooled basket of lines;
        wire: verdict.judge and the set runner; gate: a known-answer case pins the effective trial count and both bars
        Step 3 built (#1845): `verdict.Pool.among(cell)` judges a rule's lines once as one clustered set and `verdict.judge(..., among=)` takes it for the luck and deflated rungs. Remains: `ladder._one`, ladder_sets and ladder_pool pass `among=pool.among(c)`, then `family`, `trials.family` and `_charged`'s family path go (claim: verdict, ladder, ladder_sets, ladder_pool and their tests); cover a set-level `judge_lines` failure (remember it as `Pool.fold` does) and align each line's daily returns to one window first.
        {id: rungs-trials-live; files: lab/verdict.py, tests/unit/test_lab_verdict.py, lab/trials.py, lab/deflated.py, tests/unit/test_lab_trials.py, tests/unit/test_lab_deflated.py, lab/ladder.py, lab/ladder_sets.py, lab/ladder_pool.py, lab/basket.py, tests/unit/test_lab_ladder.py, tests/unit/test_lab_ladder_sets.py, tests/unit/test_lab_ladder_pool.py, tests/unit/test_lab_basket.py, tests/unit/test_lab_variants.py; after: rungs-clustered-trials}
  - [ ] THE POUND'S MISSING DAY A NAMED GAP: a fold whose pound-per-dollar rate is missing reads it from the stored
        DEXUSUK series (data-pound-history); a planted missing day is a named gap in the cell's reason, never FAULT
        (split from data-pound-history by runner ops 111, 23 Nov: the ladder is RUNGS's file)
        {id: rungs-pound-gap; files: lab/ladder.py, tests/unit/test_lab_ladder.py, lab/history_bars.py, tests/unit/test_lab_history_bars*.py; after: data-pound-history}
  - [ ] L19 ONE VERDICT RULE: the eased scorecard (`verdict.scorecard`, MAX_WEAK) is built but never called, so one
        WEAK kills a cell; it is wired as the one answer or deleted, and regime's 30 trades in each half is
        proven fair by a power case (a t=3 edge over 60 trades)
        Hard gates pre-registered before a run (costs, deflated Sharpe, out-of-sample folds, shuffle) must PASS; regime,
        market and stress are scored with MAX_WEAK; "lowest of NAMED" is deleted (decision c); wire: verdict.judge;
        gate: one WEAK soft rung no longer kills a cell, one failed hard gate always does
        Built (#1803): `verdict.judge` answers by one rule (`one_answer`): hard gates must PASS, soft rungs through the scorecard (MAX_WEAK 2), a soft FAULT gives FAULT; the weather regime rung grades three bands. Remains: delete `deflated.rule` and its test; wire `promotion.Candidate` to `verdict.one_answer`; `ladder_parts` (line 112) leaves soft-graded rungs out of `every`.
        {id: rungs-scorecard; files: lab/verdict.py, lab/rung_regimes.py, tests/unit/test_lab_verdict.py, tests/unit/test_lab_rung_regimes.py}
  - [ ] L20 FAULTS ARE NOT ANSWERS: 6,788 lines read FAULT at market (SPY has no bar on a day, e.g. 2022-09-28) and
        ~5,300 at folds (no pounds-per-USD rate): each rung reads its missing day from the one store's calendar and
        the rate table, and a fault count over 1% of a set stops its table being published
        Faults are fixed at entry, never in a rung (decision d, the data cards and one door for prices); wire: the
        set runner's pre-flight; gate: a set whose inputs have gaps refuses to start.
        Step 1 built (#1680): `market.gaps`, `folds.gaps`. Step 2 built (#1706, #1786): `ladder.run` runs `folds.preflight` before anything is written and its door refuses (NOT PUBLISHED) over 1% FAULT cells (`folds.published(faults, cells)`). Remains: the pooled runner `ladder_pool.run` skips the pre-flight (add `folds.preflight(ladder.inputs(todo, make_bars()), pounds)` before `ladder.begun`; claim widens to lab/ladder_pool.py and tests/unit/test_lab_ladder_pool.py), `ladder_sets.epon` writes its table before the fault count (lab/ladder_sets.py), then rerun EPON; the gaps themselves are DATA's; claim widened to them (runner ops 92, 22 Nov)
        Step 3 built (#1865): the pooled runner behind EPON, LEV and `first` runs the same pre-flight and refuses a set with input gaps; tables end `## NOT PUBLISHED` over 1% FAULT. Remains: DATA mends 77,870 input gaps (R-RUNGS-40), then rerun EPON and tick.
        {id: rungs-faults-not-answers; files: lab/ladder_sets.py, tests/unit/test_lab_ladder_sets.py, lab/ladder.py, lab/ladder_parts.py, lab/market.py, lab/folds.py, tests/unit/test_lab_ladder.py, tests/unit/test_lab_market.py, tests/unit/test_lab_folds.py; after: rungs-rung-map; waits: R-RUNGS-40}
- [ ] **STRATEGIES AS DATA (his goal: 1,000+ strategies over 1,000+ tickers):**
  - [ ] B1 building blocks written once, each known-answer tested: indicators, entries,
        exits, stops, filters (regime filters among them), sizing. Built: every block has its
        known answer (#396). Built: the sizing block `VolatilitySize(n)`, by the desk's own `desk.risk.volatility` (#1637), now on the one `Block` interface (#1711). Remains: register it (a SIZE kind in lab/block_base.py, `volatility_size` in `BLOCKS`, the spec and simulator reading it; the claim must widen to those files; manifest line for lab/blocks.py to name sizing). Was: sizing blocks, once the volatility-sizing research settles their form
        (coordinator 54, 22 Nov: a research wait, not his: the volatility-sizing contest table is written, R-RUNNER-205, #1481; the session reads it to settle the sizing blocks' form)
        {id: rungs-blocks; files: lab/block_base.py, lab/blocks.py, tests/unit/test_lab_blocks.py; waits: operator}
  - [ ] B2 a typed Spec, validated on entry: an unknown block or a bad setting is refused
        Remains (R-MONEY-45, #809, #823, #1382): 21 of 21 rules are rows (mansfield_rs_momentum #873, zweig breadth_thrust #1382, both run on ratio bars the caller builds); remains: a caller building Zweig's ratio bars from `lab.universe.breadth` (R-MONEY-35 wiring)
      {id: rungs-spec; files: lab/spec.py, tests/unit/test_lab_spec.py; waits: R-MONEY-35}
  - [x] B3 the catalogue, one TOML row per strategy with its source and known-answer case;
        a guard: unique names, known blocks only, a source and a case on every row.
        Built: `lab/catalogue.toml` 24 rows, `Spec.parse` refuses any without (#1078, verified)
  - [ ] B4 the nineteen eponymous rules as rows, identical trades on the fixture proven,
        then their Python files deleted. Built: 20 of 21 in the catalogue (#873); Zweig waits on breadth data
        {id: rungs-rows-as-rules; files: lab/catalogue.toml, desk/eponymous_*.py, tests/unit/test_eponymous_*.py, tests/unit/test_lab_catalogue*.py; after: rungs-spec}
  - [ ] B5 variants generated from a row's setting ranges, every one counted as a trial. Built: `lab/variants.py` (#364) makes every combination and counts trials; one home after #1307/#1315; a repeated value in a range is refused (#1321). Rows with ranges: Donchian 3x4 (#1459), RSI-2 3x3 (#1469), Williams %R 3x3 (#1473), Keltner 3x3 (#1489), Connors three-day 3x3 (#1496), Connors %b 3x3x3 (#1503; first row ranging two settings in one place), Turtle Soup 3x3 (#1521), Jegadeesh 3x3 (#1529), Zanger (#1527), Bollinger squeeze 3x3 (#1538), Kell 3x3 (#1543), Donchian fade 3x3 (#1546), Minervini 3x3 (#1551), Clenow 3x3 (#1564), Weinstein ago 3x1 (#1570), Mansfield 3x3 (#1578), Faber and dual momentum 3x3 each (#1587, joined key `entry+exit` in #1574), Zweig's hold 115/230/345 (#1595), Darvas's box sessions 2/3/4 (#1604), DeMark's setup length 7/9/11 (#1615); a row's name may not carry `[` (#1591); set VAR enters all 84 variants as trials before any run (#1535); a rule's variants count in its trials family (#1507), validated on entry by `Spec.parse`; a test holds each to the plateau's rules with the published setting at the centre. `lab/variants.py` reads `lab.spec` alone (#1620), so R-RUNGS-33 is unblocked for GRID. Remains: judging the variants through the grid chain (GC; needs R-RUNGS-33, `lab/rulebook.rule` resolving a variant's name; settle one trial name per judged variant); entering the new rows' variants in the register from a caller; every row with a setting is ranged (Weinstein's shared 150-day lookback is deliberately not ranged); fast and desk engines disagree on `clenow_momentum[entry.n=60,exit.n=50]` (bar 830), so hold every variant to parity, quicker than 80 s, before judging through the fast grid
        {id: rungs-b5; files: lab/spec.py, lab/variants.py, lab/catalogue.toml, tests/unit/test_lab_variants.py; waits: R-RUNGS-33}
  - [ ] B6 the old desk's families listed and entered as sets of rows marked QUARRY, their
        cases derived by hand, never from the old desk's numbers
        {id: rungs-quarry-rows; files: lab/catalogue.toml, tests/unit/test_lab_catalogue*.py; after: rungs-rows-as-rules}
  - [ ] P1 a fast engine for rows, vectorised in `lab/`, matching the desk's engine on the
        golden fixture (canon B2) or removed; indicators computed once per ticker and shared
        {id: rungs-fast-engine; files: lab/fast.py, tests/unit/test_lab_fast.py, manifest.toml; after: rungs-blocks; waits: operator}
  - [ ] GC the grid chained onto each set: rows swept over their ranges and the research
        universe, through the same tapes and rungs, the plateau's centre reported (canon B6)
        {id: rungs-grid-chain; files: lab/ladder_sets.py, lab/ladder_pool.py, tests/unit/test_lab_ladder_pool.py; after: rungs-gate, rungs-b5}
- [x] Each indicator known-answer tested against a published reference series (STR-14).
      Built: moving average, Bollinger deviation, Wilder smoothing (#145); true range, RSI gains
      and losses, channel (#154): five tables, 250 printed numbers; the tables now in lab/published_tables.py and the RSI held to cs-rsi.xls's 19 printed rows (#1640). Built: the band line held to StockCharts' printed Lower Band, 23 rows (#1707); every table also run while a rule is holding (#1749). Retired (coordinator 100, 22 Nov 23:0x): Supertrend's carried band and a fresh-low table, for which no free printed worked example was found; no paid data before profit (his 22 Nov), not a hard line. Supertrend stays held to its reference script's carried bands (lab/published.py, supertrend_10_3)
      {id: rungs-indicators; files: lab/published.py, lab/published_tables.py, manifest.toml,
      tests/unit/test_lab_published*.py; waits: operator}
- [ ] Before paper: a kill condition declared for each strategy; promotion only after at
      least thirty effective paper trades, net positive (STR-17, LAD-11). Built:
      `lab/promotion.py` (#127). Remains: the desk reads it (R-RUNGS-7, MONEY's, open); each candidate's
      kill numbers need a ladder-passed candidate (#413)
      {id: rungs-promotion; files: lab/promotion.py, tests/unit/test_lab_promotion.py;
      waits: R-RUNGS-7}
- [ ] At least three ladder-passed strategies and a feasibility number before A-GATE paper
      (NS-04). Built: `lab/feasibility.py` (#415); ticking needs three real rules through the ladder (#416),
      which comes from rungs-eponymous (coordinator 54, 22 Nov: its wait was a placeholder; 'after: rungs-eponymous' holds it)
      {id: rungs-feasibility; files: lab/feasibility.py, tests/unit/test_lab_feasibility.py,
      manifest.toml; after: rungs-trustworthy, rungs-eponymous}
- [ ] **The eponymous strategies through the ladder first**, before any grid exploration:
      the twenty-one published rules the old desk listed, ported one at a time as rules under
      the one template, each with its author's source, instrument, period and published
      figure written down, so that reproduction can run (the old desk's never did, for want
      of the figures); each reproduced on its author's own market first, and only then judged
      on ours. The bar for twenty-one trials is high and most are expected to fail: that is
      the information (BT-15, STR-14). Step 1 built (#1721): each rule's published test written down in `published_epon.TESTED` (only Faber has an author's own test); Step 2 built (#1804, #1829): Faber's printed figures word for word (compounded 10.18%, drawdown 42.24%, ~70% invested), and `lab/reproduce.py` takes an eponymous rule and measures CAGR, drawdown, time invested (R-RUNGS-37). Remains: Faber's figure on file in `reproduce.FIGURES` (tolerances, fixed before a run: CAGR within 0.5 points, drawdown 3, invested 5), which needs the S&P 500 total-return monthly series from 1901 held through the one writer (R-RUNGS-38, 39, DATA) and a monthly line with its own calendar (the desk's Faber rule judges a month-end on the next bar; desk files, outside this claim)
      {id: rungs-epon-first; files: lab/reproduce.py, tests/unit/test_lab_reproduce.py, lab/ladder_sets.py, lab/published_epon.py, tests/unit/test_lab_published_epon.py; after: rungs-trustworthy; waits: R-RUNGS-38, R-RUNGS-39}
- [ ] **Published figures without buying books** (his ruling, 14 November): where an
      author's own table is not to be had free, the best published replication found on the
      internet stands in, labelled secondary, with its source, date, rules and period
      written down; where sources disagree, the range is written down and reproduction must
      land inside it. RSI-2 goes first this way; variants of each rule are tested later on
      the ladder, never chosen by eye (BT-15)
      {id: rungs-secondary-figures; files: lab/published_epon.py, tests/unit/test_lab_published_epon.py; after: rungs-epon-first}
- [ ] **The ladder in sets, each published as it finishes:** set 1, the eponymous strategies;
      set 2, the grid's transfer study over the research universe; then sets of variants
      around any plateau found, each family named before it runs. After each set, one
      Telegram summary and a results file: every strategy, every rung's verdict with its
      reason, the trial count it was judged against, and what goes forward (LAD-09, LAD-03)
      {id: rungs-sets; files: lab/ladder_sets.py, tests/unit/test_lab_ladder_sets*.py; after: rungs-epon-first}
- [ ] **Graduation to paper:** a strategy passes all eleven rungs and the luck test at the
      set's full trial count (and its reproduction, if published); it is named in this plan,
      with its kill condition, before its first paper day; it then trades paper side by side
      with up to nine others under the A-GATE terms. Nothing reaches real money without his
      signature (STR-17, LAD-11, MIG-07)
      {id: rungs-eponymous; files: *; after: rungs-trustworthy, rungs-indicators}
- [ ] His paramount case: long and inverse leveraged-ETP trend strategies through the ladder
      (STR-18). Built: set LEV, six trend rules on the leveraged lines (#423). Remains: inverse
      leveraged lines, once a Line may state an inverse fund (R-RUNGS-21, R-RUNGS-22); a real run of LEV
      {id: rungs-leveraged; files: *; after: rungs-trustworthy; waits: R-RUNGS-21}

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

## The machine, then the desk — his mandate of 15 November

"Do not make the same mistakes as the previous kestrel repo and mark_the_trend repo."
Reviews of both found the same mechanisms: tools outgrowing the product, activity counted
as progress, status committed as history, suppressions in bulk, documents breeding. From
Tuesday 17 November, STOP THE LINE: no feature card starts until the first block below is
green on main. Designs, pre-mortems and planted breaks: the runner's notes,
`tuesday-designs.md`. Each box is done only when its planted break is seen failing on main.

**Stop the line (first, in this order)**
- [ ] R2 outcome contract: a night job's real result, never its exit code; DONE only when proven
- [ ] R3 the night jobs in the check, on committed real-shaped fixtures, under 60 s together
- [ ] R5 the READY gate on dependencies: a card starts only when what it needs is on main
- [ ] R7 a Stop hook with nested goals, one lane first, then every lane and every card
- [ ] G1 health rules blocking: duplicate bodies, a number with two homes, lines per box
- [ ] G2 suppressions: never rising from 80, each with its reason; no skip or xfail
- [ ] G3 the repository root holds only its fixed set
- [ ] G4 no status-only commits; state lives outside git
- [ ] G5 the runner into this repository as `ops/`, under its own ceiling (7,668, only down)
- [ ] G6 strategy scope: the desk trades its five; research rules in one rule book, capped
- [ ] F4 every pull request title carries its type, so the fix share is honest
- [ ] F6 a session runs its claim's tests and the fast check; the merge train runs all
- [ ] F7 a lane writes its own section and one scoreboard line; the shared head generated
- [ ] F8 a new module names its own concept, never an owner's name plus a suffix
- [ ] F9 every runner request names the box or scene it serves, or it is not READY
- [ ] Option C: phases 2 and 3 open, their needs offered, three sessions a lane, no auto-open
- [ ] CONSOLIDATE: the eponymous files into one template under `lab/`, duplicates and
  two-homed numbers removed, desk under 8,500 lines, results identical before and after

**Design gates (inside the one check, every change)**
- [ ] D1 DRY: unique function bodies; numbers in named constants (ratchet)
- [ ] D2 one contract test per Protocol, run against every implementation
- [ ] D3 the desk holds only what trades; each module owns one thing, said without "and"
- [ ] D4 docstrings by convention, ratcheted to none missing
- [ ] D5 dead code and test-only modules never rise
- [ ] D7 churn by the same lines changed again, not by titles
- [ ] D8 nightly deep tier: mutation tests on the money path, long property runs, SimCity

**Keeping it honest, every week**
- [ ] Every Sunday the runner opens a card to review every document in the fixed set
  against main (stale facts, lengths, rules with no check); a missed week is a fault
- [ ] Card time: median under 10 minutes and the slowest tenth under 25, measured in the
  hourly report; a week above it is a fault with its causes named

**The best small desk (after FIRST-LIGHT, each traced to a scene)**
- [ ] Q1 each paper day's expected result against the real one, the gap tracked
- [ ] Q2 trading costs measured from real paper fills against the model
- [ ] Q3 survivorship: each list as it stood on each past date
- [ ] Q4 desk-wide risk: a drawdown limit, correlation between lines, sizing by volatility
- [ ] Q6 each strategy beside simply holding its market
- [ ] Q7 a one-page runbook: if this happens, do that
- [ ] Q8 market events in the calendar: no new entry into a known event

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
Checked 20 Nov (MONEY, s4): R-PAPER-35's remainder is still PAPER's files (`desk/goflat.py`, `desk/conformance_parts.py`, `desk/placing.py:248`); R-RUNNER-401 has no R-RUNNER-397 "park one line" file on main to reuse and `desk/book.py` (382 of 400 lines) has no room, so it needs a design card; nothing built.
Checked 21 Nov (MONEY, scribe): R-RUNNER-407 part is on main (#1255, the gate refuses a buy at or under its stop); remains the live price into Order.market and the first stop from the fill (PAPER, R-MONEY-60), then the SimCity scene 'a gap down past the stop'. R-RUNNER-317, 319, 409 built (#1022, #1245, #1279); R-RUNNER-414 book side built (#1272), the prefix at order-id creation and the MSTR rows 6-7 remain.
