# The plan

**Current objective:** the money lane's — reconciliation: the desk's book against the
broker's, a mismatch named and the day's profit withheld, so scene 6 passes.

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

**Lane objective:** the research universe, by his ruling of 13 November: about 1,500
tickers (the S&P 500, the Nasdaq 100, the FTSE 350 and about 200 of the most-traded ETFs),
daily since 2010, from the free archive, through the one store's checks, kept apart from
the twenty trading lines. The grid lane needs it.

- [x] The rehearsal data in a file of its own (`tests/scenes/rehearsal.py`)
- [x] The rehearsal data lengthened to about fourteen months, the five rules buying and
      selling in it on every clean line, its UK and US holidays respected; the spoilt line's
      faults kept within the last sixty sessions (`docs/DECISIONS.md`, the data lane's)
- [ ] The scenes moved onto the whole fourteen months (`SCENES_FROM` back to `FIRST`), once
      the money lane's scene 2 counts each line's own sessions; until then they see its
      last six weeks
- [x] One line the archive refuses is parked, not the whole fetch stopped (`archive.gather`, `store.Refused`)
- [ ] The research list: about 1,500 tickers with their venue and currency, kept apart from
      the instrument master's twenty trading lines; nothing on it is traded
- [ ] The research list's daily bars since 2010, fetched and kept through the one store's
      checks, a bad ticker parked with its reason. The research store lives outside the
      repository and every worktree, in the folder `KESTREL2_DATA` names. Fetching is slow and
      resumable, with backoff, and each raw answer is cached there, so the archive is never
      hammered. While the archive refuses, the fetcher writes `{"refusing_since": <time>}` to
      `KESTREL2_DATA/archive.json` (null once it answers); the runner tells the operator after
      six hours, and the lane does other work rather than retry
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

## Phase 2 — the money path, in simulation

- [x] One strategy template; the five frozen daily strategies (his choice: five textbook
      rules, 13 November) - **scene 2 passes**
- [x] Sizing from one capital number; stops set at entry; a leveraged line sized by what
      it controls (his rulings, 13 November: a fifth each, a stop where the market has
      fallen 10%) - **scene 3 passes**
- [ ] **Scenes 2 to 7 pass in simulation**, by the money lane's book below; the data
      lane's lengthened rehearsal data (phase 1) comes first

### The money lane's book — scenes 4 to 7, in order

**Lane objective:** reconciliation (`day.run`), so scene 6 passes: after the day's trading,
the desk's book against the broker's positions line by line; a line that differs is named,
the day's profit is withheld (never a plain number), and the desk buys nothing while they
disagree. The pretend broker, the send path, the book and the day's trading are built.

- [x] The pretend broker: fills at the day's prices, rejects, partial fills, disconnection,
      a crash, resting stops, positions, and a position injected behind the desk's back
- [x] The send path: every order through the one gate, sent once however often the desk
      restarts, its fills recorded under the broker's ids - **scene 4 passes**
- [x] The book built from the broker: what is held and what is left, so the gate enforces
      at most five holdings and two buys of one line share one fifth
- [x] The day run: decisions dated that day only, a rule's position read from the book,
      round trips with commission and conversion - **scene 5 passes** (on the fourteen
      months; spread, slippage and UK tax come with the day record)
- [ ] Reconciliation: the desk's book against the broker's, a mismatch named and the day's
      profit withheld - **scene 6 passes**
- [ ] The day record: every cost line (spread, slippage and UK tax added to round trips),
      one rounding policy for pounds, what holding the market earned, and the same days
      replayed to the same records - **scene 7 passes**
- [ ] SimCity, small: one command runs the whole desk's day over all fourteen months of
      rehearsal data against the pretend broker with its faults, every night, and writes one
      record; a census names every part of the money path and turns red when one has no
      scenario

## Phase 3 — the money path, on paper

Begun alongside phase 2 by his ruling of 13 November: "Five lanes, phase 3 now".

- [ ] **FIRST-LIGHT: ten consecutive clean trading days**

### The paper lane's book

**Lane objective:** the paper account proved quiet before any order. The account is the old
desk's (his ruling, 13 November), reached through IB Gateway's paper port 4002 on his PC
with the desk's own client id, never 4001. Every day a read-only check sets the account's
positions and open orders against the desk's own book, and a mismatch is flagged (scene
6). No order is sent until this exists and has run clean.

- [ ] The Gateway known, read-only, before any order: port 4002 answers as a paper
      account, with the desk's own client id; its daily restart and the weekly re-login
      handled unattended. A re-login that needs his phone or password is his: a reminder line
      at the right time, never a workaround. The old desk's gateway alarms are a quarry only
- [ ] The paper account proved quiet: the daily read-only check of positions and open
      orders against the desk's book, a mismatch flagged
- [ ] The real paper-broker adapter behind the same interface as `broker.Pretend`, speaking
      to IB Gateway with the standard library alone (`desk/` imports nothing else)
- [ ] Stops resting at the broker, each rounded down to its line's price step
- [ ] Conformance trades, on paper, one London and one US line, each in its market's hours:
      a market buy at the open; the resting stop placed, triggered, and cancelled on a sale;
      a partial fill if the paper broker gives one; a rejection. Each real result recorded
      beside the pretend broker's, and the pretend broker fixed where they differ
- [ ] Unattended running, and recovery from a restart
- [ ] Morning and evening messages, and an alarm on silence

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

## Phase 5 — the edge

- [ ] Candidates through the ladder, leveraged index lines included
- [ ] The operator's hand tickers judged honestly, with their own rules
- [ ] Small-size paper trading as out-of-sample proof
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

## Phase 7 — going live

- [ ] The go-live requirements, and his one signature

---

## Rules of the plan

A batch is one session, one lane, one objective, one merge. A batch that adds net lines must name
the scene it advances. No new capability until every scene passes.

Estimates are from size, not measurement, and are re-made after phase 0 and after the
first three sessions of phase 2. Actual against estimate is reported every week.
