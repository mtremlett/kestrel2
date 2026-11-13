# Failure patterns

Each one is a way this desk has actually gone wrong, and the mechanism that now catches
it. A pattern with no mechanism is an open debt and says so.

Every mechanism named "guard" is a test in `tests/guards/test_guards.py` that has been
driven against a deliberate violation. See `docs/DECISIONS.md` for the evidence.

---

**1. The guard that excuses a whole file.** A check searches a file for an escape word
and, finding it anywhere, passes the file entirely. The live-money guard did this on day
one and was switched off by a docstring.
→ *Caught by:* guards judge one line at a time, and the words they search for are
assembled from pieces so a guard never flags its own source. A7 in the canon.

**2. The clean core with an outside.** A small walled package is built and trusted, then
the code that runs it each day is placed outside the wall, where no limit applies. The
predecessor's 2,000-line core stayed inside its cap while its runner grew to reach
352,000 lines.
→ *Caught by:* the whole repository is under one ceiling, and the manifest wall test.

**3. Progress counted in activity.** Cards landed, commits made, tests added — all rising
while the thing that matters does not move. The predecessor landed about 1,100 work cards
in six weeks and proved 10 of 64 requirements.
→ *Caught by:* the only progress number is scenes passing out of seven, and the plan
requires a batch adding net lines to name the scene it advances.

**4. The set-aside test.** A test fails, is added to a known-failures list "for now", and
is never fixed. The predecessor carried 2,221.
→ *Caught by:* a guard forbids skip and expected-failure markers. There is no list.

**5. The test that reads the live desk.** A test passes honestly on the operator's
machine because it reads his real data or his broker, and proves nothing about the code.
→ *Caught by:* a guard forbids machine-specific paths, and GitHub runs the whole check on
a machine with no access to any of it.

**6. The second version of a file.** `_v2`, `_new`, `_fixed`, or a file named after the
session that wrote it. The predecessor had 1,218 session-named test files.
→ *Caught by:* a guard on file names. Git is the archive.

**7. Repairing forward on a broken tree.** A change breaks something; the next change
tries to fix the symptom; the fix needs its own fix.
→ *Caught by:* the stop rules. A passing scene that fails stops all other work, and if one
attempt does not restore it the commit is reverted, never patched over.

**8. Two homes for one fact.** The same number, list or rule written down in two places,
which then disagree. The predecessor had three stop levels per position and two different
figures for the pot.
→ *Caught by:* the manifest names one owner per concept; duplicates are merged on sight.
→ *Debt:* no automatic check finds two homes. Human discipline, for now.

**9. Documents breeding.** Summaries, notes, handovers and reports accumulate until no
one knows which is true. The predecessor had 728.
→ *Caught by:* a guard allows exactly ten documents and no others.

**10. The silent failure.** An error caught and ignored, a default that hides missing
data, a check that prints nothing either way.
→ *Caught by:* lint rules forbidding blind exception handlers and silent passes, plus the
canon's "fail loudly".
→ *Debt:* a check that cannot fail is still possible to write. Only A7 — driving each
guard against a violation — catches that, and it is a practice, not a mechanism.
