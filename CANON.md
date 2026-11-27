# The canon
Rules that keep this desk converging instead of doom looping, for every session: lanes
(Parts A, B) and seats (Part C). Facts live in `CLAUDE.md`; recurring failures and their
checks in `docs/FAILURE_PATTERNS.md`. **Limit: 200 lines, held by a guard** (`BUDGET.json`):
a new rule replaces or merges one, or becomes a check. The first desk forgot 56 lessons.

# Part A — engineering
## A1. Prime directives
1. **North star first.** Every change traces to a requirement id or an item in
   `docs/PLAN.md`. Everything else waits.
2. **Build the machinery, not patches.** Correct results come from the design — one
   model, one engine, one source of truth — not from checks bolted on afterwards.
3. **Less code is progress.** Deleting dead code, scaffolding and duplicates is
   high-value work. Never grow the codebase to work around a problem, nor work around one
   whose real fix is known: make the fix, or say that it is out of scope.
4. **Always green.** The whole check passes on GitHub before every merge, and a passing
   scene never regresses.
5. **Evidence over assumption.** Read the code, reproduce it, run the check. No claim
   without proof from this session.
6. **Small, reversible steps.** One concern per commit.
7. **The machine is the product.** The runner and every tool that builds the desk obey
   these same ceilings, caps, tests and rules. A process problem is fixed by deleting or
   tightening, never by growing process code (the predecessors' tools outgrew the desk).

## A2. Fix the machine, not the symptom
- Before editing, write down the hypothesis and the evidence: the failing test, the
  traceback, the log. No guess-fixes.
- Fix where the wrong value is produced, not where it is noticed.
- Search for the same pattern elsewhere. If it recurs, repair the mechanism once, then
  remove the patches it makes redundant, in a separate commit.
- If a change touches code that a fix changed in the last ten commits, treat it as a
  recurring problem: find the mechanism and record it in `docs/FAILURE_PATTERNS.md`.
- **Not acceptable as fixes:** special cases for particular inputs, symbols or dates;
  code that corrects bad output afterwards; validation buried deep inside; retries or
  sleeps that hide timing problems; catching and ignoring errors; defaults that mask
  missing data; defensive checks instead of correct types; a second code path for a job
  that already has one.
- Validate only at system boundaries — files, vendors, the broker, the operator — once,
  on entry, into typed models. Trust them inside.
- Make invalid states impossible: types, enums, constructors that enforce invariants,
  immutable data, explicit state machines.

## A3. Tests — few, strong, about the product
- One check command runs everything. The hook, GitHub, the demo and the scoreboard all
  use it. There is no other way of verifying.
- **One gate per principle, all inside that one check, on every change:** PEP-8, strict
  types, docstrings, KISS (size, complexity), DRY (no duplicate bodies, one home per
  number), SOLID (module walls, one contract test per interface). Only slow, deep tests
  run nightly, and a red one is a fault. A principle with no gate is a wish.
- The test suite is the only verification code. No scaffolding in the tree: no verify,
  check, smoke, debug or harness scripts, no tests of test helpers. Scaffolding runs from
  outside the repository, and its OUTPUT is the evidence.
- **Levels.** Scenes end to end in business language; contract tests per component;
  golden files for generated numbers; property tests for invariants. A bug extends the
  contract test of the component it broke — no test-per-bug piles.
- Fast and deterministic: no network, no real external systems, a fixed clock and seeds,
  tiny committed synthetic fixtures. Fakes only at adapter boundaries.
- A flaky test is a bug. Fix its root cause before other work. Never rerun until green.
- **Never** delete, skip, weaken or loosen a test to get green; never change tool
  configuration, a threshold or an ignore list to pass; never hardcode a result or
  special-case a test input. Merging redundant tests is its own commit, coverage kept.

## A4. Structure
- `manifest.toml` says what each package may import; `manifest/<lane>.toml` lists each
  lane's modules and the one thing each owns. Register a module before creating it. Guarded.
- **One owner per concept:** one model, one config loader, one client per external
  system, one home per business rule, one source of truth for names, symbols, ids,
  thresholds, calendars and configuration. Search before you create; merge duplicates.
- **Pure core, side effects at the edges.** Logic is data in, data out. Network, files,
  the broker and the clock sit behind thin adapters.
- **Fail loudly.** No broad or empty exception handlers, no silent fallbacks, no
  suppression without a reason on the same line. Errors say what failed, with which ids.
- Type annotations everywhere. Typed models instead of loose dictionaries.
- Small units: functions under 50 lines, files under 800 (his ruling, 21 Nov). Both guarded.
- Scripts only call into the package; no business logic lives in them.
- Optimise only when a benchmark tied to a requirement shows the need.
- One dependency list, `requirements.txt`, pinned; a new one only when it replaces code we
  would otherwise maintain, its reason in `docs/DECISIONS.md`.
- No dead code, commented-out code, versioned copies or backups. Git is the archive.
- No secrets in code, logs or the repository. This repository is public.

## A5. Forbidden
- **Fake implementations:** placeholder logic, hardcoded or random results, or fakes in
  product code presented as working. Unfinished parts raise `NotImplementedError` and are
  listed in `docs/STATUS.md`.
- A new version of a file (`_v2`, `_new`, `_fixed`, a copy) instead of editing the
  original; commented-out code or tests; summary, notes or report files outside the fixed
  document set; editing many files to fix one bug before finding the mechanism.

## A6. Workflow
**Ready** means: a requirement id, acceptance criteria in business terms, the exact
files, and the failing test that will prove it; at most ten minutes of work.
1. **Understand.** Read the relevant code and tests. Restate the goal in plain English.
2. **Plan.** Files to change, the mechanism, everything downstream, tests to add.
3. **Test first.** Write the scene or contract test and watch it fail for the right
   reason. For pure restructuring, confirm the tests already cover the behaviour.
4. **Change.** The smallest change, at the source.
5. **Verify.** The inner loop is the fast check plus the card's tests; then push and read
   GitHub's whole check. Run the whole check on the PC only to chase a red.
6. **Review.** An independent reviewer that never saw the reasoning, for every money-path
   and ladder change. Fix every blocking finding.
7. **Commit** one logical change, prefixed `feat`, `fix`, `refactor`, `test`, `docs` or
   `chore`, saying what and why; **record** STATUS, PLAN, DECISIONS or FAILURE_PATTERNS.
**Done** means: the whole check green on GitHub and its output read, tests seen failing
first, the outcome seen where it lands (a job's real result, never its exit code), the
box ticked, and a plain-English report. Never declare done without both.

## A7. Prove the guard, never trust it
A guard nobody has seen fail is a guard nobody has tested. **Every guard is driven
against a deliberate violation before it is called a guard**, and the evidence — the
mistake, the test that caught it — is recorded in `docs/DECISIONS.md`. **A whole-file
escape hatch is not a guard** (failure pattern 1).

## A8. Stop rules, and scope
- **Two failed attempts at one problem: stop**, and never retry a failing command
  unchanged. Record what was learned, propose a different approach or ask.
- **A passing scene fails: stop everything else and restore it.** If one attempt does not
  fix it, revert the commit that broke it. Never repair forward on a broken tree.
- The change grows beyond the plan — more files, more special cases, the size cap
  exceeded: stop and re-plan.
- Ambiguous requirements are decided by rule and his rulings, recorded with the options;
  only his hard lines (`CLAUDE.md`) wait for him.
- You cannot explain why something works or fails: do not edit. Investigate.
- One objective per session. Do only what the task asks; log anything else under "found,
  not fixed" in `docs/STATUS.md`. Never mix a behaviour change and restructuring.

# Part B — the trading desk
## B1. Safety
- The desk works in backtest and paper only. It never enables live mode, places a real
  order, connects to a real account or reads live credentials.
- Live mode is off by default, needs explicit configuration and a human confirmation, and
  credentials live outside the repository.
- Every order passes one pre-trade risk gate: position, notional, loss and order-rate
  limits. Nothing bypasses it. A kill switch stops all trading, and the drill is run.

## B2. One engine
- Backtest, paper and live share one engine and identical strategy code. Only the
  adapters differ: the data feed, the broker, the clock.
- Strategies see only the strategy interface — point-in-time data, the portfolio, order
  intents. They never call a vendor, the broker or the clock directly.
- Any second implementation, such as a fast backtester, must match the engine on the
  golden dataset in a parity test, or be removed.

## B3. Time and data
- The engine serves only data available at the simulated moment. A future-blind test
  proves decisions up to time T are identical with and without data after T.
- Timestamps are timezone-aware UTC inside. One calendar source. One documented
  bar-timestamp convention. A UK holiday is not a US holiday.
- Raw data is immutable and versioned. Cleaning — gaps, duplicates, outliers, units,
  splits — happens once, on entry, at the one writer. Every price is read through one
  door. Derived data is reproducible from raw data plus the code version.
- One instrument master. Facts about a ticker come from reference data, never its name.

## B4. Numbers and accounting
- Money uses exact decimals or integer ticks with one rounding policy. Amounts carry
  their currency, and conversion happens in one place.
- **Invariants, property-tested:** positions equal the sum of fills; equity equals cash
  plus market value; total profit equals realised plus unrealised minus costs; orders
  move only through valid state transitions; sending an order is idempotent.
- Costs — commission, spread, slippage, financing, and UK transaction taxes by instrument
  type — are always modelled. No result is reported without them, and every verdict names
  the broker whose schedule priced it.

## B5. Reproducibility
- The same data, configuration, seed and code version give identical results. Every run
  records its id, configuration, data version and commit.
- A golden reference run on fixture data is committed. A golden number changes only with
  a plain-English reason in `docs/DECISIONS.md`, approved by the desk (his ruling, 22 Nov).
- Every order is traceable end to end: signal → intent → risk decision → order → fill.

## B6. Research discipline
- Parameters are chosen in-sample only. Results show in-sample and out-of-sample side by
  side, after costs, with the worst fold reported and judged on.
- Every winner is corrected for luck, and records how many trials it was picked from.
- Promote only through the engine (contract tests, golden run): a plateau's centre, never a lone
  peak; a daily Sharpe over 2 is a red flag. Unjudged rules trade only as a paper MACHINERY TEST
  (one share, one switch, off by default): never evidence, promoted or near live (his 22 Nov).

# Part C — seats, cards and memory (his rulings, 22 Nov)
Every rule names its check. One marked OWED is built before any new work.
- **Memory is code.** Seats change hourly and prose dies with them: an order lives only as a
  line of the open-orders list, never only in a message; an agreement is done only when a test,
  guard, drive or runner gate fails on its breach, and the register names it (OWED: a test).
- **Rules arrive by load.** The start-up hook ticks CLAUDE.md and CANON.md against main and
  prints the agreements; a hard line is a hook that denies, never a word. Check: the hook,
  driven stale and current; the deny hook is OWED.
- **One outcome number** (`CLAUDE.md`), read from one function by the Telegram, STATUS and
  SCOREBOARD. Check: the runner's hourly table; the shared function is OWED.
- **Work in progress is capped.** No new card in a lane whose open boxes rose and none
  closed in 24 h; a card ending twice without a tick is parked with its cause; a fault fixed
  a third time stops its lane until its failure pattern has a check. Ready cards match the
  slots, never a quota. Check: runner gates, OWED (empty sessions: done, runner 2947b46).
- **Subtract first.** The runner, notes, drives and seats only shrink unless he rules; a
  review ends in deletions and failing checks, never in new cards. Check: RUNNER_BUDGET
  only down; the notes OWED.
- **Every mistake becomes a check** (Cherny): the session that errs builds the check, and
  writes a line here only when no line covers it. Short leash (Karpathy): small steps, each
  verified before the next; a seat hands over at 70% by writing, then ends.
