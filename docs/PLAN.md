# The plan

**Current objective:** phase 2's first step — one strategy template and the five frozen
daily strategies, so that scene 2 passes on the clean lines.

Scenes passing: **2 of 7**. Phase: **2-money-sim**.

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

## Phase 2 — the money path, in simulation

- [ ] One strategy template; the five frozen daily strategies
- [ ] Sizing from one capital number; stops set at entry; a leveraged line sized by what
      it controls (his ruling, 13 November)
- [ ] The pretend broker, with faults: rejects, partial fills, disconnection, crashes
- [ ] The book, the ledger, reconciliation, the day record
- [ ] **Scenes 2 to 7 pass in simulation**

## Phase 3 — the money path, on paper

- [ ] The real paper-broker adapter behind the same interface
- [ ] Stops resting at the broker
- [ ] Unattended running, and recovery from a restart
- [ ] Morning and evening messages, and an alarm on silence
- [ ] **FIRST-LIGHT: ten consecutive clean trading days**

## Phase 4 — the ladder

Starts as a second track as soon as phases 1 and 2 give it data and a strategy template.

- [ ] A batch service that survives a bad cell and a restart
- [ ] Results kept, keyed by code and data version; only what changed is re-run
- [ ] Each rung proven: it catches a planted edge and rejects a planted non-edge
- [ ] Reproduces a published strategy's own published result
- [ ] Runs seven days without stopping

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

A batch is one session, one objective, one merge. A batch that adds net lines must name
the scene it advances. No new capability until every scene passes.

Estimates are from size, not measurement, and are re-made after phase 0 and after the
first three sessions of phase 2. Actual against estimate is reported every week.
