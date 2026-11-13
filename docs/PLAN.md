# The plan

**Current objective:** the money lane's — the book built from the broker: what is held and
what is left, so the gate enforces at most five holdings and two buys of one line share
one fifth.

Scenes passing: **4 of 7**. Phase: **2-money-sim**.

The two lines above belong to the money lane: it alone moves the scenes count. The data
and ladder lanes' objectives are in their own books below. The operator's Telegram line
reads the ticked boxes under each `## Phase N` heading, so each lane's book sits inside its
phase.

---

## The three lanes

Three chains of sessions run side by side on the operator's PC, day and night, each
session starting when the one before it ends (his rulings, 13 November 2026,
`docs/DECISIONS.md`). A lane's session works on its lane's objective only, edits only the
files its lane owns, and writes only in its lane's parts of the shared documents: its
section of `docs/STATUS.md`, its book here, its table in `docs/SCOREBOARD.md` and its part
at the end of `docs/DECISIONS.md`. Each lane's book sits inside the phase it belongs to:
DATA in phase 1, MONEY in phase 2, LADDER in phase 4. So two lanes' pull requests never
touch the same lines, and GitHub merges neither until it holds the other.

| lane | owns |
|---|---|
| MONEY | `desk/strategy.py`, `orders.py`, `broker.py`, `book.py`, `day.py`; `tests/scenes/test_scenes.py`; their unit tests |
| DATA | `desk/lines.py`, `venues.py`, `archive.py`, `store.py`; `tests/scenes/rehearsal.py`; their unit tests |
| LADDER | `lab/`; `tests/unit/test_lab_*.py` |

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

### The data lane's book — rehearsal data first, then the parked lines and the store's findings

**Lane objective:** the scenes' rehearsal data lengthened to about fourteen months, so
the five rules trade in it (his ruling, 13 November), before the money lane reaches
scene 5. Scenes 1 to 3 keep passing on it.

- [x] The rehearsal data in a file of its own (`tests/scenes/rehearsal.py`)
- [x] The rehearsal data lengthened to about fourteen months, the five rules buying and
      selling in it on every clean line, its UK and US holidays respected; the spoilt line's
      faults kept within the last sixty sessions (`docs/DECISIONS.md`, the data lane's)
- [ ] The scenes moved onto the whole fourteen months (`SCENES_FROM` back to `FIRST`), once
      the money lane's scene 2 counts each line's own sessions; until then they see its
      last six weeks
- [ ] One line the archive refuses is parked, not the whole fetch stopped
- [ ] The four parked lines brought back, or each one's reason confirmed: 2MU's five real
      moves recorded from a second source; 5QQQ's consolidation of 22 August 2024; SGLN's
      garbled weeks of 2011; 3LGO's missing history, and when enough has gathered
- [ ] The store's open findings in `docs/STATUS.md` (the data lane's section): a frozen
      feed; a suspension gap; a one-day crash dropped as a wrong unit; a stretched bar's
      changes unrecorded; bars and fault record swapped one after the other; the window
      before mid-April 2010; a pence history the archive calls pounds
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

**Lane objective:** the book built from the broker (`book.positions`): what is held and what
is left, every fill the broker made written in the ledger (a stop's overnight sale
included), so the gate enforces at most five holdings and two buys of one line share one
fifth. The pretend broker and the send path are built; scene 4 passes.

- [x] The pretend broker: fills at the day's prices, rejects, partial fills, disconnection,
      a crash, resting stops, positions, and a position injected behind the desk's back
- [x] The send path: every order through the one gate, sent once however often the desk
      restarts, its fills recorded under the broker's ids - **scene 4 passes**
- [ ] The book built from the broker: what is held and what is left, so the gate enforces
      at most five holdings and two buys of one line share one fifth
- [ ] The day run: decisions dated that day only, a rule's position read from the book,
      round trips with their costs - **scene 5 passes** (needs the data lane's fourteen
      months first)
- [ ] Reconciliation: the desk's book against the broker's, a mismatch named and the day's
      profit withheld - **scene 6 passes**
- [ ] The day record: every cost line, what holding the market earned, and the same days
      replayed to the same records - **scene 7 passes**

## Phase 3 — the money path, on paper

- [ ] The real paper-broker adapter behind the same interface
- [ ] Stops resting at the broker
- [ ] Unattended running, and recovery from a restart
- [ ] Morning and evening messages, and an alarm on silence
- [ ] **FIRST-LIGHT: ten consecutive clean trading days**

## Phase 4 — the ladder

Runs now as a second track, the ladder lane, since phases 1 and 2 gave it data and a
strategy template.

### The ladder lane's book

**Lane objective:** a batch service that runs many cells (`lab/cell.py`), one bad cell
recorded and the rest carried on, and a restart taking up where it stopped - proven by its
own contract test.

- [x] The unit of work, keyed by code and data version (`lab/cell.py`)
- [ ] A batch service that survives a bad cell and a restart
- [ ] Results kept, keyed by code and data version; only what changed is re-run
- [ ] Each rung proven: it catches a planted edge and rejects a planted non-edge
- [ ] Reproduces a published strategy's own published result
- [ ] Runs seven days without stopping

The ladder lives in `lab/`, which phase 2's ceiling holds to 1,500 lines (`BUDGET.json`).
Raising it is the operator's decision: the lane asks in its STATUS section when it nears
the ceiling, and works inside it until he answers.

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
