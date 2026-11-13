# The canon

Rules that keep this codebase converging instead of doom looping. They apply to every
task in every session. Project facts live in `CLAUDE.md`; recurring failures and their
guards live in `docs/FAILURE_PATTERNS.md`.

**Limit: 200 lines, held by a guard.** A new rule must replace or merge an existing one,
or become an automated check. A rule that lives only in prose is a rule that will be
forgotten — the first desk proved that with 56 lessons and 64 deny rules.

---

# Part A — engineering

## A1. Prime directives

1. **North star first.** Every change traces to a requirement id or an item in
   `docs/PLAN.md`. Everything else waits.
2. **Build the machinery, not patches.** Correct results come from the design — one
   model, one engine, one source of truth — not from checks bolted on afterwards.
3. **Less code is progress.** Deleting dead code, scaffolding and duplicates is
   high-value work. Never grow the codebase to work around a problem.
4. **Always green.** The check passes before every commit, and a passing scene never
   regresses.
5. **Evidence over assumption.** Read the code, reproduce it, run the check. No claim
   without proof from this session.
6. **Small, reversible steps.** One concern per commit.
7. **Stop instead of spiralling.** Two failed attempts at one problem means stop and
   rethink.

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
- The test suite is the only verification code. No scaffolding: no verify, check, smoke,
  debug or harness scripts in the tree, no tests of test helpers, no code that exists
  only to exercise other code. Scaffolding runs from outside the repository, and its
  OUTPUT is the evidence.
- **Levels.** Scenes end to end in business language; contract tests per component for
  inputs, outputs and invariants; golden-file tests for generated numbers; property
  tests for invariants. A bug extends the contract test of the component it broke — no
  test-per-bug piles.
- Fast and deterministic: no network, no real external systems, a fixed clock and seeds,
  tiny committed synthetic fixtures.
- A flaky test is a bug. Fix its root cause before other work. Never rerun until green.
- Fakes only at adapter boundaries, never for the code under test.
- **Never** delete, skip, weaken or loosen a test to get green; never change tool
  configuration, a threshold or an ignore list to pass; never hardcode a result or
  special-case a test input.
- Consolidating redundant tests happens in its own commit, with equal or better
  coverage, and is reported.

## A4. Structure

- `manifest.toml` lists every module, the one thing it owns and what it may import.
  Register a module before creating it. A guard enforces it.
- **One owner per concept:** one model, one config loader, one client per external
  system, one home per business rule. Search before you create; merge duplicates on
  sight.
- One source of truth for names, symbols, ids, thresholds, calendars and configuration.
- **Pure core, side effects at the edges.** Logic is data in, data out. Network, files,
  the broker and the clock sit behind thin adapters.
- **Fail loudly.** No broad or empty exception handlers, no silent fallbacks, no
  suppression without a reason on the same line. Errors say what failed and with which
  ids.
- Type annotations everywhere. Typed models instead of loose dictionaries.
- Small units: functions under 50 lines, files under 400. Both are guarded.
- Scripts only call into the package; no business logic lives in them.
- Optimise only when a benchmark tied to a requirement shows the need.
- Pin dependencies in `requirements.txt`, the one declared list. Add one only when it
  replaces code we would otherwise write and maintain, and record why in
  `docs/DECISIONS.md`.
- No dead code, commented-out code, versioned copies or backups. Git is the archive.
- No secrets in code, logs or the repository. This repository is public.

## A5. Forbidden

- Creating a new version of a file (`_v2`, `_new`, `_fixed`, a copy) instead of editing
  the original.
- **Fake implementations:** placeholder logic, hardcoded or random results, or fakes in
  product code presented as working. Unfinished parts raise `NotImplementedError` and are
  listed in `docs/STATUS.md`.
- Writing summary, notes or report files outside the fixed document set.
- Adding a script to prove something works.
- Commenting out failing code or tests.
- Editing many files to fix one bug before finding the mechanism.
- Starting a second objective in one session.
- Declaring done without the check's output.

## A6. Workflow

**Ready** means: a requirement id, acceptance criteria in business terms, the modules
affected, and the test that will prove it.

1. **Understand.** Read the relevant code and tests. Restate the goal in plain English.
2. **Plan.** Files to change, the mechanism, everything downstream, tests to add.
3. **Test first.** Write the scene or contract test and watch it fail for the right
   reason. For pure restructuring, confirm the tests already cover the behaviour.
4. **Change.** The smallest change, at the source.
5. **Verify.** Run the whole check and read the output.
6. **Review.** An independent reviewer that never saw the reasoning. Fix every blocking
   finding.
7. **Commit.** One logical change, prefixed `feat`, `fix`, `refactor`, `test`, `docs` or
   `chore`, saying what and why.
8. **Record.** `docs/STATUS.md`, `docs/PLAN.md`, and `docs/DECISIONS.md` or
   `docs/FAILURE_PATTERNS.md` where relevant.

**Done** means: the check green locally and on GitHub, tests seen failing first,
reviewer passed, documents updated, committed, and a plain-English report given.

## A7. Prove the guard, never trust it

A guard nobody has seen fail is a guard nobody has tested. **Every guard is driven
against a deliberate violation before it is called a guard**, and the evidence — the
mistake, the test that caught it — is recorded in `docs/DECISIONS.md`.

This is not theory. On the first day, eleven of twelve guards caught their violation.
The twelfth was the one that stops this desk reaching live money: it excused any file
containing the word "never" anywhere, and the core package said it in ordinary prose. It
had been passing green while doing nothing. **A whole-file escape hatch is not a guard.**

## A8. Stop rules

- **Two failed attempts at one problem: stop.** Record what was learned, propose a
  different approach or ask.
- **A passing scene fails: stop everything else and restore it.** If one attempt does not
  fix it, revert the commit that broke it. Never repair forward on a broken tree.
- The change grows beyond the plan — more files, more special cases, the size cap
  exceeded: stop and re-plan.
- Requirements are ambiguous, or behaviour the operator can see would change beyond the
  task: ask, with options and a recommendation.
- You cannot explain why something works or fails: do not edit. Investigate or ask.
- Never retry a failing command unchanged.

## A9. Scope

- One objective per session, taken from `docs/PLAN.md`.
- Do only what the task asks. No drive-by refactors, renames or extras; log anything else
  under "found, not fixed" in `docs/STATUS.md`.
- Never mix a behaviour change and restructuring in one commit.
- Never work around a problem when the real fix is known. If the real fix is out of
  scope, say so.

---

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
  splits — happens once, on entry, at the one writer. Derived data is reproducible from
  raw data plus the code version.
- One instrument master. Facts about a ticker come from reference data, never from its
  name.

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
- A golden reference run on fixture data is committed. Any change to a golden number
  needs a plain-English explanation in `docs/DECISIONS.md` and the operator's approval.
- Every order is traceable end to end: signal → intent → risk decision → order → fill,
  linked by ids.

## B6. Research discipline

- Parameters are chosen in-sample only. Results show in-sample and out-of-sample side by
  side, after costs, with the worst fold reported and judged on.
- Every winner is corrected for luck, and records how many trials it was picked from.
- Promote the centre of a plateau, never a lone peak.
- A daily Sharpe above 2 is a red flag, not a win.
- A strategy is promoted only through the engine, with contract tests and a golden run.
