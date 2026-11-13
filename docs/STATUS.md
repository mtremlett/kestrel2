# Status

**Read this first, then `docs/PLAN.md`, then run `python check.py`.**

Five lanes run side by side (`docs/PLAN.md`). The shared part below is changed only by a
session the operator starts himself; each lane writes only in its own section, so that
parallel pull requests never touch the same lines. A lane's section says where it is, its
next step, what it found and did not fix, and any question it holds for the operator.

## Shared

Last updated: 13 November 2026.

### Where we are

Phase 2 under way. Scenes 1, 2 and 3 pass: scenes passing 3 of 7.

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
engine) and RUNGS (the ladder's rungs). Every lane runs on Fable while its allowance is
under 45%, then on Opus until a Fable reset (his ruling). A
runner outside this repository starts each lane's next session when the last one ends,
inside the plan's included usage, stopping at 80% of the week.
GitHub merges a pull request only when its check is green and its branch already holds
everything on main, so two green lanes cannot combine into a red main.

### Open questions for the operator

1. **A second GitHub account** for sessions to work through, so that the guards cannot be
   removed by the account that enforces them. On 13 November he chose to start the lanes
   on his own account now; the question stays open for later.

### Found, not fixed

- **Two of the line limits are prose, not guards.** CLAUDE.md says its 80 lines and
  CANON.md its 200 are held by a guard; no test reads either, and CANON.md is 224 lines.
- **The runner's own lines to his phone wait for his key.** A lane that halts, pauses at
  the weekly cap or needs his decision, and the 07:00 line, are sent by the runner on his
  PC from a file holding the bot key, which he copies beside the runner himself. Until he
  does, they are written to the runner's log only.
- **A Windows Update restart overnight stops the lanes until he logs in.** The runner
  starts at his logon; starting it without one needs his password in Task Scheduler,
  which is his call. He is pausing updates.
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

Last updated: 13 November 2026 (the one comparison).

### Where it is

The desk now has one rule for "is the book the broker's?" (`book.differences`), which the
paper lane asked for (R-PAPER-1) so the pretend broker and the real paper account are judged
alike. It sets the book beside what a broker says it holds, entry by entry. Every entry must
be the book's own shares of that line; entries that only add up to them are named, a line
the book holds and the broker does not list is named, and a line the broker lists at no
shares is not a holding. One thing is stricter than the paper door's rule was: a line held
in two entries is never the book's, so two accounts each holding the book's shares can no
longer read as clean. The same rule judges the stops resting at the broker. Reconciliation
before every order (`book.reconcile`, `book.send`) now asks it, and over the rehearsal's
fourteen months the desk trades exactly as before: the same 68 fills and 34 round trips,
with and without every first order rejected. The paper door keeps its own copy of the rule
until the paper lane moves it onto this one (asked below). Its test was seen failing
first. A blind review found nothing blocking: it checked the rule on 210,525 made-up
accounts against its own statement of it, without one wrong answer either way, and set the
old reconciliation against the new over 8,000 random runs with every fault, without one
difference. Sixty-seven deliberate breaks were driven, its and the lane's: seven gaps in
the tests were found, each now closed and caught, and four breaks cannot change any answer.

The desk checks its book against the broker's before every order (`book.reconcile`, on
the send path, so nothing goes round it). Line by line it sets the shares its ledger adds up
to beside the shares the broker reports and the stop resting there, and names each line
that differs: a position bought or sold by hand, or a stop cancelled. While any line
differs the desk buys nothing. It still sells a line whose shares agree, one that has lost
its stop included, and never a line whose shares differ, since the broker may not hold
them. The day carries on and keeps each refusal as that order's stated answer; buying
starts again by itself once the two agree. Over the rehearsal's fourteen months the two
never differ and the desk trades exactly as before. Tests seen failing first; forty-four
deliberate breaks over two rounds: the first round missed five of thirty-one, each a gap
in the tests, now closed and driven again; all are caught. A blind review found nothing
blocking; its findings are taken or recorded (below).

**Scenes 6 and 7 will pass together, not one after the other** (`docs/DECISIONS.md`): both
read the day's one record, and a reconciled day's profit cannot be published until every
cost line is real. Scenes stay at 5 of 7 until then.

Scene 5 passes: the desk sells, and closes round trips. Its day (`day.trade`) runs after
the market opens: it writes in the ledger the stops the open sold, keeps the day's
exchange rates, and acts only on decisions dated the session before, on lines whose venue
trades that day. Each rule's position is read from the book: a line belongs to the rule
whose buy opened it, only that rule's sell sells it (all of it), and a rule whose buy was
refused or whose stop sold may buy again. Sales go first, through the one gate (the desk
is long only), and take their shares off the line's resting stop; then each buy is sized
from the book after the send before it, and a line sold that morning is not bought again.
Each round trip pairs a sale with the buys it closes, oldest first, in pounds at each
fill's own day's rate, after commission and currency conversion; on the rehearsal's
fourteen months the rules' own sales close round trips. Scene 2 now counts each line
against its own venue's calendar, so the scenes can move onto the fourteen months. The
tests were seen failing first. Of twenty-five deliberate breaks, twenty-two were caught at
once, one (a pound rate other than 1) once its test was corrected, and the two missed showed
code that did nothing, now removed. A blind review found nothing blocking; its fixes are
taken (below).

The desk now knows what it holds (`book.positions`): the shares of each line its ledger's
fills add up to, never the orders it meant to send, and never a position bought by hand at
the broker. Every fill the broker made is written in the ledger before an order is judged
and again after it is sent (`book.collect`), so a stop sold overnight, or on the very day
of its buy, frees its holding at once. The pre-trade gate reads that book: a sixth line is
refused, and the shares a line already holds and the shares ordered share its one fifth,
counted together at today's price. A second buy of a held line is sized to what is left.
The tests were seen failing first; fifteen deliberate breaks were each caught; a blind
review found nothing blocking, and its fix (a stop sold on its buy's own day reached the
book only on the next send) and its test gap (a crashed order's fill counted as a holding)
are taken and tested.

Scene 4 passes: the desk sends an order and its stop rests at the broker (`book.send`).
Before sending, the desk asks the broker whether it already has the order; if so it
records what the broker did and sends nothing, so a desk that dies mid-send and restarts
never buys twice. Only an order the broker never received passes the pre-trade gate and is
sent. Each fill is written once in the desk's ledger under the broker's own execution id.
A rejection, a partial fill and a dropped connection each come back with a stated reason;
a dropped order may be sent again, since the broker never had it. The contract test was
seen failing first; eleven deliberate breaks of the send path were each caught.

The desk has a pretend broker to trade against in simulation (`desk/broker.py`), built to
behave like the real one. A buy fills at the day's opening price under the broker's own
execution id, and leaves a stop resting at the broker for the shares it got, so the stop
protects the position even with the desk switched off. The stop is tested at every open,
and on the day of the buy itself: a day that falls through it sells at the stop, or at the
open when the day opens below it. Faults on request, each stated and never silent: a
rejection, a partial fill (half, the rest cancelled), a dropped connection (the order never
arrived), and the desk dying after the broker has the order. The desk can then ask the
broker what it did with an order id, so it never needs to send twice; a repeated id is
refused and counted. A position can be planted as if bought by hand. Its own contract test
was seen failing first; thirty deliberate breaks of the broker were each caught; a blind
review found nothing blocking, and its one fix taken (below) is tested.

The desk now sizes a buy from one capital number (`desk/orders.py`), by the operator's
ruling of 13 November: at most five holdings, each costing at most a fifth of the capital,
a leveraged line counted at what it controls (5QQQ may take £400 of £10,000), and the stop
set before the order exists, where the market under the line has fallen 10%. Whole shares
only, priced in pounds under Interactive Brokers UK's published fixed fees, the currency
conversion counted. The sizer and the pre-trade gate read the same number: change it and
both move. Leverage is a fact on every line in the instrument master. Thirty deliberate
breaks are each caught; a blind review's blocking finding (a pound line at any
exchange rate slipped past the gate) is fixed, and its other one is recorded below.

The desk has its five
daily strategies (`desk/strategy.py`), chosen by the operator on 13 November: five
textbook rules at their published settings, long only, untuned - Connors' RSI-2
pullback, Bollinger's 20/2 pullback, the Turtles' 20/10 breakout, the 50/200-day cross
and Supertrend 10/3. Each is shown one bar at a time after its close, so it cannot read
a later bar; scene 2 proves the decisions up to any day are the same with the later
bars deleted. A second implementation written apart from the desk's found the same
trade days on sixty long walks, and forty-four of forty-five deliberate breaks were
caught; the forty-fifth cannot change a decision.

### Next step

First the paper lane's other blocking request (R-PAPER-2): the send path and the day run
accept any broker that behaves as the pretend one does, not the pretend one by name. That
broker should give its holdings and its resting stops as entries, a name and its shares
each, so a real account's rows reach `book.differences` whole and are never added together
on the way. Then the kill switch and its drill, by his ruling of 13 November that it comes
first of the lane's own book: the paper
lane sends no order until it is drilled, and nothing the money lane waits for holds it up.
Then the costs whole in the one cost model (`desk/orders.py`): what a sale itself costs, and
spread and slippage on both legs, the stop's sale included, each a stated assumption; the
rungs lane waits for them too. Then the day's record (`day.run`): the day reconciled at its
end, a mismatch named and its profit withheld, else the profit after every cost beside what
holding the market earned. It needs each line's UK tax from the data lane (below). Scene
6's test must move onto the fourteen months and check the book against the broker's every
day: no rule holds anything at the end of the rehearsal data, on its six weeks or on the
whole of it, so "the broker holds something" cannot be read there.

### Done for other lanes

- R-PAPER-1: done in this pull request

### Requests to PAPER

- [ ] R-MONEY-4 (later, opened 2026-11-13 18:35 UK): `paper.differences` asks `book.differences` and
  drops its own comparison, so the rule has one home in fact. It hands over the book and the
  account's entries under one name each, and words what comes back:
  `book.differences({f"{s} STK {line.currency}": n ...}, [(f"{h.symbol} {h.kind} {h.currency}", h.shares) ...])`
  gives a `Difference(name, broker, book)` for each entry that is not the book's, in the
  order the door names them today. The orders stay the door's own. The blind review built
  exactly this in a copy: all forty of the door's tests pass unchanged. Two things change,
  both safer: two entries that are each the book's shares, clean today, are named; and an
  entry that matches the book beside another entry with shares is named too, so it reads
  "the broker holds 25, the desk's book 25". A name that comes back more than once is held
  in more than one entry: the door should say so in its sentence. The name must keep the
  kind and the currency, or another product under the same symbol would read as the book's.

### Requests to DATA

- [x] R-MONEY-1 (blocking, opened 2026-11-13 18:15): each line's UK transaction tax as a fact on the line
  (`Line`): what a purchase pays, nil for a fund or an exchange-traded product, 0.5% stamp
  duty for a UK share, each of the ten London lines confirmed; and one London line in the
  rehearsal data that pays it. Scene 7 requires every cost line charged at least once, and
  scenes 6 and 7 cannot pass until the day's record can count the tax.
- [ ] R-MONEY-2 (blocking, opened 2026-11-13 18:15): the scenes moved onto the fourteen months
  (`SCENES_FROM = FIRST`). Scene 2 now counts each line against its own venue's calendar,
  and scene 7 needs days on which the rules trade; none trades in the six weeks.
- [ ] R-MONEY-3 (later, opened 2026-11-13 18:15): a daily exchange rate, pounds per dollar, in the store.
  The day run is handed the day's rates (`day.trade`'s `rates`); the scenes give 0.79.

### Found, not fixed

- **What the blind review of the day run left** (nothing blocking; its fixes taken: a
  rule's own sale required by scene 5, scene 2 counted against each venue's calendar, a
  day's kept rate never repriced, and a missing rate refused before anything is sent):
  - Money has no one rounding policy yet: a round trip's shared commission is divided in
    whatever decimal setting the caller has. The day record (scene 7) must fix one, to the
    penny, for every pound figure.
  - "A line its rule sold this morning is not bought again" is tested only through a
    stop's sale; the code is the same for both.
  - Spread, slippage and UK tax are not in a round trip's costs yet: the day record must
    add both legs' spread and slippage, the stop's sale included.
  - The day run decides each line's whole history again every day: fourteen months of
    days take about twenty-four seconds in scene 5. Fine for now; a longer replay will
    need the rules' state carried from day to day.
  - The day run reads the archive it is handed; preparing it through the store
    (`store.prepare`, asked by the data lane) is still to come, before paper.
- **What the blind review of reconciliation left** (nothing blocking; taken: a line that
  has lost its stop may still be sold, a stated error for cancelling a stop that does not
  rest, and tests for a line only the book holds and for an order the broker already has):
  - **Nobody is told yet.** A mismatch stops the buying and is in each order's answer, but
    reaches the operator only when the day's record and the messages exist. Until a person
    acts, a line whose stop was cancelled sits unprotected unless its rule sells it, and a
    line partly sold by hand keeps a stop for more shares than are held, which would sell
    the broker short. The desk cannot place or change a stop by itself.
  - A lost ledger does not show at the pretend broker: it gives every fill it ever made, so
    the ledger is written again whole, in silence. Reconciliation sees only a change with
    no fill behind it. At a real broker, which gives recent fills only, a lost ledger would
    name every held line and stop the buying.
  - A gate refusal of a sale during the day (selling more than the book holds) is now one
    of the day's answers and no longer stops the day. It cannot arise today.
  - **For the paper adapter (phase 3):** the broker's fills must be the desk's own orders
    and their stops only, or a hand trade's fill would be written in the ledger and the two
    books would agree; orders still working, a stop placed before its buy fills, and
    positions that lag fills would each read as a mismatch and stop the morning's buying,
    so reconciliation there needs the broker's working orders; a dropped connection while
    reading positions or stops is not yet a stated answer, only in placing an order.
- **What the blind review of the one comparison left** (nothing blocking; its six test
  gaps taken, a stop for fewer shares than the line holds among them, which the pretend
  broker can make after all):
  - The send path reads the broker's holdings twice, once to name the lines that differ and
    once to ask whether the order's own line does. At the pretend broker those are one
    moment; at a real one they are two. When any broker can stand behind the send path
    (R-PAPER-2), it should read once and judge both from that reading.
  - A line the broker lists at no shares, which the book does not hold, no longer makes a
    sale of that line "unsure". The pretend broker lists no such line; right for a real one.
  - Two breaks no test can see at the pretend broker: a stop resting on a line the book
    does not hold (the book learns of every fill, so it always holds it), and a sale of a
    line only the broker holds (the gate refuses it anyway). The rule itself is tested on
    both; a real broker's adapter needs its own test of each.
- **What the blind review of the book left** (nothing blocking; its fix and test gap taken):
  - The book reaches the gate as a bare mapping of line to shares. Only the send path
    passes the real book; a typed book that only `book.positions` can make would stop a
    caller passing an empty one.
  - At a real broker an order waits for the open, so two orders sent overnight would each
    pass the gate on a book that holds neither. The paper adapter (phase 3) must count the
    orders the broker is still working, as well as the fills.
  - Unit test lines stand close to product lines (the guard keeps them at or under): each
    step's tests must come with its code.
- **What the blind review of the pretend broker left for the send path and the day run**
  (its one finding fixed: a fault was used up by an order that met no market):
  - **What the blind review of the send path left** (nothing blocking; its test gap - an
    order the broker already holds must not be judged by the gate again - is fixed):
    the ledger is swapped in whole but not forced to disk, so a power cut (not a crash of
    the desk) can lose it; and a ledger deleted later reads as "no fills" without a
    word. Neither can send twice, since the broker is asked first (what reconciliation
    sees of a lost ledger is above).
  - The broker fills at the bare open and sells a stop at exactly its level. Spread and
    slippage are not in its prices, so the day run must charge both, on both legs, the
    stop's sale included, or profit reads too high.
  - An order is sized at the last close and fills at the next open. On a gap up the fill
    costs more than the gate allowed; the book must hold a line to what was filled.
  - `inject` takes any symbol and a negative quantity (a hand sale) unchecked. Untested
    so far: a planted position on a line that also has the desk's stop, a partial fault
    on a one-share order, and several stops firing on one open.
- **What the blind review of sizing left for the book** (its blocking finding - a pound
  line accepted any exchange rate - is fixed and tested):
  - The gate trusts the stop of an order built by hand; only the sizer sets the 10% rule.
    Scene 4's own orders carry a stop of 30, about a third below their price.
  - Stops and costs are exact decimals, not rounded: a real broker refuses a stop off its
    price step, so the paper adapter (phase 3) must round each stop to its line's step,
    down, and the instrument master must carry that step.
  - The fees are Interactive Brokers UK's fixed pricing. If his account is on tiered
    pricing, the schedule is a different one; and UK stamp duty is assumed nil for the ten
    London funds and products, to be confirmed line by line before the day counts UK tax.
- **What the blind review of the five strategies left for later scenes** (its blocking
  findings, test gaps, are fixed):
  - A decision depends on where the history starts (the averages' seeds, Supertrend's
    carried bands, the 50/200's observed cross). Measured: walk 1 with its first 30 bars
    dropped changes two Bollinger decisions. If the archive's first date moves, the same
    day can decide differently; a replay is identical only on identical saved data.
  - "Still warming up" and "chose to stay out" both read as hold; "the 20 days before"
    means the 20 bars before, so a day the store dropped is skipped over.
  - Wilder's smoothing and the true range live inside `strategy`. If the stop at entry
    is set from the true range, it is asked of `strategy`, not written a second time.
- **What a blind review of the scenes left open** (the rest was fixed before commit):
  the currency cost is not separated from commission in scene
  3; "a day with a cost line missing is refused" is held by the types, not by a day
  that should have paid UK tax showing none; scene 5 does not tell a sale by the
  strategy's rule from one by the resting stop; "no halt in force" has no interface yet.

### Unfinished code

Every one of these raises NotImplementedError, by design, until its phase builds it.

| part | phase |
|---|---|
| `day.run`: the day's reconciled record (its mismatches, profit, costs and the market), after `day.trade` | 2 |

Built and real: the day's trading (`day.trade`, `strategy.today`), sales and round trips
(`orders.Sale`, `book.round_trips`, `book.record_rates`), the send path, the ledger, the
book and its reconciliation (`book.send`, `book.fills`, `book.collect`, `book.positions`,
`book.reconcile`), the pretend broker (`broker.Pretend`), sizing, cost and
the gate across the book (`orders.size`, `orders.cost`, `orders.gate`), the five strategies (`strategy.decide`), the twenty lines, the archive
client (`archive.fetch`), the price store (`store.prepare`, `store.read`, `store.faults`),
the venue calendars,
the typed records (`Line`, `Bar`, `Parked`, `Decision`, `Settings`,
`Order`, `Fill`, `Sent`, `RoundTrip`, `Costs`, `Record`), and `Order` refusing a missing
stop, or one not below its price.

## PAPER

Last updated: 13 November 2026 (the lines as the broker lists them).

### Where it is

**The desk now knows each of its twenty lines as the paper broker lists it**
(`desk/listing.py`): the broker's own number for the line, the exchange it lists it on,
whether it prices it in pence or in pounds, and its price steps. It asks the broker each
time, read-only, through the same door as the account check, and writes none of it down:
two questions, neither of which can place an order, held byte for byte by a test.

**Run on the real gateway, 13 November, about 18:35 UK: twenty of twenty listed**, each
exactly once under the desk's own name and currency. All ten London lines are on London's
funds list; eight US lines on Nasdaq and two (SPY, GLD) on Arca.

- **Six London lines are priced in pence at the broker, four in pounds.** 3LGO, 2MU, IITU,
  5QQQ, ISF and SGLN in pence; SMGB, VHYG, IB1T and VUSA in pounds. The broker calls the
  currency of all ten pounds, and the desk's prices are all pounds. A stop sent in the
  wrong unit would sit a hundred times too high or too low, so the desk converts in one
  place (`Listing.floor`): a price in pounds goes down onto the broker's step and comes
  out in the broker's unit. £37.556 on IITU becomes 3755.
- **The steps are the broker's own rule, by price.** IITU, 3LGO, 5QQQ and SGLN move in
  tenths of a penny under £5 and whole pence above £25; ISF in fifths of a penny at £10;
  VUSA in quarters of a penny; every US line in cents.
- **Proved on the broker's own prices.** The open, high, low and close of each line's last
  thirty sessions, read from the broker (read-only), 2,392 prices. On nineteen lines every
  price sits on the step the desk works out, in the unit it works out, and the prices move
  in exactly that step, nothing finer and nothing coarser: whole pence on IITU, 3LGO and
  SGLN, tenths of a penny on 5QQQ, fifths on ISF. A step read in the wrong unit would be a
  hundred times out. 2MU agrees below £500; above it 36 of its 77 prices do not (below,
  found not fixed).
- **A line the broker does not list as the desk's is named, and the rest carry on**: not
  there at all, there twice, or under the name but another kind of product, another
  currency or an exchange outside the line's venue. It comes back as "unlisted" with the
  reason, a different kind of record, so no order can be built for it by mistake.
- **An answer the desk cannot read stops the whole reading**: a message of another shape,
  an answer to a question it did not ask, steps that are not steps, any error but "no such
  line", a gateway that hangs up, or an account that is not a paper one.

The tests were seen failing first. A blind review found two blocking faults, both fixed and
tested: a notice that the gateway cannot look lines up was passed over, so an outage could
have read as "the broker lists nothing"; and an infinite or not-a-number price was let
through. Its second reading approved the repair. Of 113 deliberate breaks, 101 were caught
at once and five showed a gap in the tests, each closed; five different ones survive, four
that cannot change a result and one (adding an exchange) that is a deliberate edit
(`docs/DECISIONS.md`). Since the review, that same notice stops the account check too.

The account check, built the session before (`desk/paper.py`): the desk can read the paper
account and say whether anything but the desk trades it. It connects to IB Gateway's paper
port on his PC under the desk's own client id (222), asks two questions - what the account
holds, and which orders rest on it - and hangs up. It places, changes and cancels nothing:
the four messages it can send are fixed, and a test holds them byte for byte. The standard
library alone, about two hundred lines.

**Run on the real account, 13 November, about 17:45 UK: quiet.** The account lists
seventeen lines the old desk once held, every one at no shares, and no order rests on it.
Against the desk's book (empty: the desk has sent nothing on paper) the check named no
difference. Held open a second time under the same client id, the gateway refused the
desk with its reason, and the desk stopped, as it should.

What the check holds to (`paper.differences`, `paper.mismatches`):
- **Only a paper account is read.** The broker starts a paper account's code with a D. Any
  other code, in the gateway's list of accounts, on a holding or on an order, stops the
  desk before it asks that account anything. A gateway logged in to a real account cannot
  be read as quiet.
- **A holding must be the book's.** Matched by its symbol, kind and currency; more, fewer,
  short, in another currency, as another kind of product, or split over two entries that
  only add up to the book: each is named. A line the book holds and the broker does not is
  named too.
- **Every resting order is named**, whoever placed it, the desk's own client included: the
  desk rests none on paper yet.
- **A reading that stops is never a clean one.** A gateway that speaks another version,
  hangs up, sends half a message, a message cut short, an unknown kind of message, or any
  notice other than the state of its price feeds, stops the check with the reason.

The tests were seen failing first. A blind review found one blocking fault (entries that
added up to the book were passed as the book), fixed and tested, and nine lesser points,
taken or recorded below. Sixty-five deliberate breaks are each caught; six showed a gap in
the tests on the way, each closed (`docs/DECISIONS.md`).

### Next step

First, a short step now that the money lane has built the one comparison of a book with
a broker (`book.differences`, R-PAPER-1, #52): the account check hands it the account's
entries and keeps only what is the paper door's own (paper accounts only, the kind and
currency of a holding, the resting orders), so the rule has one home.

Then the fills and the orders the broker reports, read-only: each fill under the broker's own
id, its price turned from the broker's unit back into the line's currency (pence into
pounds on six London lines), and the desk's own orders and stops told from anyone else's,
so the daily check can know the desk's resting stops. Then placing, behind `Pretend`'s
interface: no order until that day's check is clean and the kill switch is drilled. The
account check should be run again on a second day before the first order.

### Requests to MONEY

- [x] R-PAPER-1 (blocking, opened 2026-11-13 18:15): one home for "the book against the broker".
  `paper.differences` is that rule for the real account; scene 6 (`day.run`) needs it
  against the pretend broker. One comparison should serve both, in `desk/book.py`, taking
  the book and the broker's holdings; the paper door would then hand it the account's
  entries and add only the orders.
- [ ] R-PAPER-2 (blocking, opened 2026-11-13 18:15): `book.send`, `book.collect` and `day.trade` accept
  any broker with `Pretend`'s interface, not `Pretend` by name, so the paper adapter can
  stand behind them.

### Done for other lanes

- R-DATA-5: done in #53 for its first half (every `Line(...)` in this lane's tests states
  its UK tax). Its second half stays open with the conformance trades: what the contract
  note of the first London product bought says of stamp duty.

### Requests to DATA

- [ ] R-PAPER-3 (later, opened 2026-11-13 18:55 UK): each line's ISIN as a fact on the line
  (`Line`), so the paper door can know the broker's line is the desk's by its ISIN, not by
  its ticker. The broker gives it for all twenty (IITU is IE00B3WJKG14, AAPL US0378331005);
  each should be confirmed from the issuer or the exchange, not copied from the broker.

### Found, not fixed

- **The old desk's scheduled tasks are all disabled**, he confirmed as administrator on
  13 November. The daily read-only check of the account stays all the same: it is the
  proof, every day, that nothing else trades it.
- **Nothing runs the check each day yet**, and nothing makes the desk wait for it: one
  clean reading at one moment is all there is. It is the lane's next box.
- **An open order has never been seen from the real gateway**, since none rests on the
  account. Its shape in the tests is the published client's, checked field by field by the
  blind review. Any order is named whatever its details; the first conformance trade must
  confirm them.
- **2MU's real prices do not keep to the broker's own steps above £500.** The broker's rule
  for it says steps of £5 there; on the days it traded above £500 it moved in steps of £1
  (36 of 77 prices are off the £5 step). Below £500 it moves in exactly the rule's £2. A
  stop put down onto a £5 step there sits up to 1% lower than asked. Whether the broker
  takes a stop on its own step that the exchange does not quote is unproven. 2MU is parked
  today; its conformance must be seen before it trades on paper.
- **Fills, holdings and the broker's own bars come in the broker's unit.** On the six
  London lines priced in pence, a fill's price will arrive a hundred times the desk's.
  Only a price going out is converted so far (`Listing.floor`); the way back belongs to
  the next step, in the same place.
- **Nothing reads the listings each day yet, and nothing refuses an order on an unlisted
  line**: the adapter will, when it places. Today's reading is one moment's.
- **The account check still knows a holding by its name, kind and currency**, not by the
  broker's own number for the line, which the listing now gives. Matching on the number
  would be exact; it belongs with the move onto `book.differences` (next step).
- **The same answer carries facts the desk does not read yet:** each line's trading hours
  at the broker for the coming week, which the conformance trades need (given in central
  European time for London: from 08:00 UK, to 16:30 UK on 3LGO, 2MU, 5QQQ and IB1T and to
  16:50 on the other six; the US lines 09:30 to 16:00 New York); the smallest order (a
  whole share on those four, fractions elsewhere; the desk trades whole shares); and the
  kinds of order each line takes (a market order, a stop and good-till-cancelled on all
  twenty).
- **The broker gives daily bars for all twenty lines on this paper login** (thirty sessions
  each were read, read-only, to prove the steps). The data lane's check of the archive
  against the broker's price of record can be built on it; the six pence lines would need
  dividing by a hundred.
- **The broker's names for exchanges are a short list in the module** (London's funds
  list; Nasdaq and Arca), each seen from the gateway on one of the twenty. When VUAG, EQQQ
  and IDTL join the twenty they should list on London's funds list too; a line on any
  other exchange (New York, say) comes back unlisted, by design, until its exchange is
  added.
- **What the blind review of the listings left** (its two blocking findings are fixed and
  tested: a notice that the gateway cannot look lines up was passed over as price-feed
  news, so an outage could have read as "the broker lists nothing"; and an infinite or
  not-a-number price or step was let through):
  - **The desk's own resting orders will probably stop both readings.** The gateway is
    believed to send a client its own open orders, unasked, when it connects; the door
    stops on an order it did not ask for. Nothing rests today. The next step, which reads
    orders, must teach the door before the first stop rests. The questions' numbers (0 to
    19) also share one space with order numbers; they must be kept apart then.
  - **A price for the broker is a plain number, like a desk price.** Once it leaves
    `Listing.floor`, nothing stops a caller setting 3755 pence beside 37.556 pounds. The
    adapter must keep it inside the door, or give it a kind of its own.
  - **The paper stop and the simulation's stop differ by up to one step**: the sizer and
    the pretend broker use the stop unrounded. The conformance trades will show it.
  - **Nothing decides yet what the desk does when a line it holds comes back unlisted.**
    Not buying it is plain; its resting stop and its sale are the adapter's to settle.
  - **The broker's line is known by its name, kind, currency and exchange**, not by its
    ISIN, which is in the same answer, unread; the instrument master holds none (asked of
    the data lane, below). A ticker given to another product on the same exchange would
    pass. The broker's own name for each line is in the answer too: SPCX is "SPACE
    EXPLORATION TECHN-CL A" there, which the data lane may want to set beside the
    archive's history under that ticker.
  - **A conversation has no time limit of its own**: fifteen seconds for each message, and
    a gateway that kept sending price-feed news would never be cut off. Silence stops the
    desk, as a timeout.
  - **Whether the gateway says "no such line" while its look-up is down, and whether it
    tells a client that connects after the loss, is unproven.** The desk stops on the
    notice when it is sent.
  - A step that is no number at all stops the desk loudly but without a plain sentence.
- **The guard on the live port reads for one number.** It would not catch the live port of
  the broker's desktop program. The door's own test now holds its port and machine, and the
  paper-only lock stands behind it; a session he starts could make the guard refuse any
  port in `desk/` but the paper one.
- **Some bad answers stop the desk loudly but without a plain sentence:** a share count
  that is no number, and a byte that is not text. A list of accounts ending in a comma
  would be refused as "not a paper account"; the real gateway sends none.
- **A gateway that has lost its link to the broker** may still answer from memory. It
  announces the loss to clients connected at the time, and the desk stops on that notice;
  whether a client connecting afterwards is told is unproven.
- **The gateway must be running and logged in**, and it logs itself out each day. Keeping
  it up belongs to "unattended running", later in the book.
- **Each of this lane's changes adds no more test lines than product lines**, so it leaves
  the shared margin between unit tests and product where it was.
- **A deliberate break can report the wrong result from Python's cache.** A break written
  within a second of the last, to a file of the same size, ran the old code once in this
  session and named the wrong test. Every lane drives breaks; they should be run with the
  cache off (`PYTHONDONTWRITEBYTECODE=1`). A session he starts could record this in
  `docs/FAILURE_PATTERNS.md`.

## DATA

Last updated: 13 November 2026 (this section cut to its open items; git keeps the rest).

### Where it is

Phase 1's data is in: the twenty lines with their leverage and UK tax (`desk/lines.py`), one archive
client, one store with one writer (`desk/store.py`), both venues' calendars for 2010 to 2027,
fourteen months of rehearsal data, and the research list (`lab/universe.py`: 1,065 tickers, 864
clean, 201 parked). Sixteen of the twenty lines are clean and four parked (below).

### Next step

R-MONEY-2, the money lane's blocking request: the scenes moved onto the whole fourteen months. Then
the lane's objective, the research list's parked fifth (`docs/PLAN.md`). R-MONEY-3 (a daily
pounds-per-dollar rate in the store) and R-PAPER-3 (each line's ISIN) are open, for later.

### Done for other lanes

- R-MONEY-1: done in #47

### Requests to GRID

- [ ] R-DATA-1 (later, opened 2026-11-13 18:15): a cell takes a `Line` from `universe.UNIVERSE` and
  reads `store.read(root / line.venue, line.symbol)`: thirteen symbols are two companies, by venue.

### Requests to MONEY

- [ ] R-DATA-3 (later, opened 2026-11-13 18:15): the day run reads the archive through
  `archive.gather` and hands `store.prepare` its answers whole, so a refused line parks with its reason.
- [x] R-DATA-4 (later, opened 2026-11-13 18:40 UK): each `Line(...)` in its tests states its UK tax.

### Requests to PAPER

- [x] R-DATA-5 (later, opened 2026-11-13 18:40 UK): each `Line(...)` in its tests states its UK tax.

### Found, not fixed

- **UK tax (NS-05).** Nil for the five London products is how the law reads, not yet seen on a
  contract note (the paper lane reports the first). A line made without its tax still pays nil; the
  default can go now. The research list's London shares all pay 0.5%, unchecked name by name
  (Jersey, Ireland's 1%, Spain). The takeover levy is not modelled.
- **Four lines parked:** 3LGO (no history), 2MU (five real crashes unrecorded), 5QQQ (an unadjusted
  consolidation), SGLN (garbled weeks of 2011). Each is a step in the book.
- **The archive** is free and unofficial, and fetching does not pace itself (DAT-08).
- **The research list** is today's members only (BT-09), has no kept home, keeps a departed ticker's
  files, loses a ticker's bars on a refused day, and leaves off three London members quoted in euros.
- **The store:** nothing fills `Line.real_moves` or `Line.suspended`; a wrong factor under 2-for-1
  passes; a bad print not a hundredfold out, and a freeze under five sessions, have no rule; bars and
  faults are written apart; parking lives only in what `store.prepare` returns; any `ValueError` in
  an answer parks its line. Unpinned by a test: the hundredfold margin, and that L01's tax is charged.

## GRID

Last updated: 13 November 2026. Took over the ladder lane's cell, batch and results on 13
November, when the operator split the ladder into GRID and RUNGS.

### Where it is

The ladder has its unit of work (`lab/cell.py`): one of the five strategies on one of the
twenty lines over a window of days. It runs the desk's own decisions, never a copy of them,
over the line's whole history up to the window's end, and records the days each trade was
bought and sold. Each record carries a fingerprint of the code that made it and of every
bar it read, so a later batch can keep results and re-run only what changed. It names no
price or profit yet: no result is reported without its costs (`docs/DECISIONS.md`).

It now has a batch service (`lab/batch.py`) that runs many cells in turn and writes each
result down as it finishes. A cell that fails is recorded with its error and the rest carry
on; a batch stopped part way, even in the middle of writing a line, takes up where it
stopped when started again, never running a finished cell twice. A failed cell is tried
again on the next start. A batch refuses to start when the code on disk is no longer the
code it loaded.

A result is now kept by what made it: the code and every bar the rule was shown. Each run
reads every cell's bars again and re-runs a cell only when its code or its bars have
changed; a bar corrected after a window's end leaves that window's result alone.

The fast grid engine is built (`lab/grid.py`, numpy) and proven against the desk's own
engine: for each of the five strategies it works out, for a line's whole history at once,
whether the strategy is in the market after every bar, and on the golden series and on
prices as long as the archive's it holds exactly what the desk holds, day by day. It never
guesses. The desk counts in exact decimals and the grid in floating point, so wherever two
numbers are too close for floating point to tell which is larger the grid refuses the cell
by name (`TooClose`) and gives no answer; the desk's own engine must decide it. On prices
like the archive's it refused nothing; on made-up prices on a coarse tick it refuses a
close exactly on a Supertrend band. Measured on 4,000 days of one line: the desk's engine
takes about 100 ms for the five rules, the grid 6 to 8 ms, after 17 ms once per line to
read its prices in. Two blind reviews found three ways to a wrong answer, all on prices no
market has; each is fixed and tested, and the second review's whole random comparison, run
again on the repaired engine, found no difference from the desk. Nothing uses the grid yet: the unit of work still runs the desk's own.

### Next step

Move the unit of work onto the grid (`lab/cell.py`): a cell's trades from the grid's
answer, and from the desk's own engine whenever the grid refuses, the same record either
way, the grid's file counted in the code version. Then auto-tune.

### Asked of the money lane

- **The five rules take no settings.** The grid's first pass is "every strategy at every
  setting", and the grid may only be trusted where it matches the desk's engine (canon B2).
  Until `desk/strategy.py`'s rules can be made at other settings (the window lengths, the
  RSI's bar, the bands' widths), the grid is proven, and so runs, at the published five only.

### Found, not fixed

- **What the blind reviews of the grid engine left** (three wrong answers found, each fixed
  and tested: an RSI on days that move a thousand-millionth of the price, a Supertrend band
  when a close sits far outside its day's range, and ties among prices of 26 digits and
  more; and six safeguards no test held, each now held by one). There was no third review
  of the last repairs; the second review's own random comparison was run again and is clean:
  - **A line with five or more identical closes in a row, at prices as long as the
    archive's, is refused for the RSI** (and twenty or more for the Bollinger rule): an
    average of equal long prices is a tie floating point cannot call. The desk's engine
    decides those cells, so the answer is right and only slower. The store drops a frozen
    feed, but a thinly traded research ticker may have such runs; worth counting on the
    research universe before the first pass.
  - Reading a line's prices in costs twice what the five rules do (17 ms against 8 ms on
    4,000 days), nearly all of it turning each decimal into a whole number. It is paid once
    per line, not per cell. And the Supertrend and the RSI still walk the days one at a
    time for Wilder's smoothing and the carried bands. Fine until the first pass is timed.
  - Deliberate breaks that survive, which no series found can show: the Supertrend's band
    carried on the day's own close for the day before's (no position differed on some 700
    series searched); a close set against its own day's upper band; the Bollinger check
    for whole prices whose squares pass 2**53 (it needs an exact tie among very large
    numbers); Wilder's smoothing on a series exactly as long as its window (nothing reads
    that value); and the margin of the Supertrend's upper band and of its carrying measured
    against the close alone, or against the day's prices and not all so far (the committed
    case is the lower band's; the review's random comparison covers the rest, outside the
    repository).
  - On whole-number prices, about thirty unchanged closes in a row fade the RSI's gain and
    loss to nothing and the grid refuses the line for that rule; the desk's engine decides.
  - The golden series are read from the money lane's `tests/unit/test_strategy.py`
    (`GOLDEN`, `_walk`, `_jumpy`, `_bars`, `START`): if that file renames them, the grid's
    test stops and the two lanes must move together.
- **A helper's working copy was left in the main folder.** The tool that gives a helper its
  own copy made it under `.claude/worktrees/` of the operator's main kestrel2 folder, with a
  branch `worktree-agent-ab11b126c53bfd69e` in the shared repository. This session did not
  go into that folder to remove it. It holds no change and can be deleted.
- **What the blind review of the unit of work left for the batch** (nothing blocking; its
  test gaps on the data version and the trade pairing, and its unsorted-bars finding, are
  fixed and tested):
  - The code version is read from disk when `lab/cell.py` is imported. A long-lived
    process that imported the strategies earlier, and had them changed on disk before
    that, would key old code's results under the new code. The batch service must run each
    batch in a fresh process, or refuse when the files no longer match `cell.LOADED`.
  - Three of the five rules never trade in the contract test's twenty-five-day shapes
    (RSI-2, the 50/200 cross, Supertrend need far longer); their agreement with the desk
    is shown there only as "no trades". A fixture of more than 200 bars would cover them.
  - The key does not include the Python version, and only file contents, not file paths,
    are hashed; a file moved without a change of text keeps its key.
- **What the blind review of the batch left** (nothing blocking; its two findings on
  failed cells never retried and on cutting a torn line by rewriting the whole journal
  are fixed and tested):
  - That each line reaches the disk before the next cell starts (`os.fsync`) is not seen
    by any test; removing it leaves the tests green. Only a killed process would show it.
  - Nothing stops two processes working on one journal at once; the module says one at a
    time. A lock is owed when the batch is started by anything but a person.
  - A journal line corrupt in the middle fails loudly but names neither the file nor the
    line; a failed cell keeps its error's type and message, not where it was raised.
- **What keeping results by key left** (blind review, its one blocking finding fixed):
  - The unit of work's fingerprint misses two breaks no test drives: a bar whose volume
    alone changed, and two bars on one day (the order check's `<=` made `<`). Its contract
    test owes a case for each.
  - Every run reads and hashes each cell's bars, and a cell with no result hashes them
    twice (once for its key, once in its run). Fine until a benchmark says otherwise.
  - The journal keeps every old record and one line per failure per run; it only grows.
- **A cell runs all five strategies to keep one.** It asks `strategy.decide`, which decides
  every rule at once; a batch of the five on one line pays five times. Fine until a
  benchmark says otherwise.
- **A missing session older than sixty sessions no longer parks a line**, so research over
  years of history (the ladder) will meet gaps it must handle.

## RUNGS

Last updated: 13 November 2026 (the luck rung). Took over the ladder lane's first rung on
13 November.

### Where it is

The ladder has its first rung (`lab/rung.py`), which says whether a strategy earns on a line
after costs by more than chance would give. Each trade is sized by the desk's own sizer at
the close it was decided on, bought at the next open through the desk's own pretend broker,
where its 10% stop rests, and sold by that stop or at the open after the rule sells. The
broker's own schedule prices both legs, and every verdict names it. A strategy passes when
it made at least thirty trades and their average return after costs is at least two
standard errors above nothing. On made-up prices it passed a planted edge on every one of
forty random histories tried and failed all forty with no edge; it fails an edge that a £3
least commission eats at a small capital, and the same edge with too few trades.

The ladder now has its luck rung (`lab/luck.py`), for the day many strategies are tried at
once. Try enough of them and some pass the first rung with no edge at all, about one in
forty. So the first rung's verdicts are judged again as one set: each one's chance of being
luck is multiplied by the number of trials it was picked from, and it passes only if that
is still 5% or less and it passed the first rung. Every trial counts, whatever became of it:
a loser, one with too few trades, and one that gave no verdict at all (a cell that failed, a
candidate dropped), which the caller must state. Each corrected verdict carries the count it
was corrected for. On made-up trades: of forty sets of forty strategies with no edge, the
first rung alone handed over a "winner" in twenty-six; after the correction, in one (5%
allows two). A real edge added to each set passed in all forty. A modest winner stands
alone and picked from eight, and falls picked from nine.

### Next step

In-sample and out-of-sample folds: a strategy's history cut into folds, each judged after
costs, the two side by side, the verdict on the worst fold; every fold a trial the luck rung
counts (canon B6, AG-01).

### Requests to MONEY

- [ ] R-RUNGS-1 (later, opened 2026-11-13 18:15): a sale's own cost, spread and slippage in
  `desk/orders.py`, from the desk's one cost model, so the first rung's costs are whole.

### Found, not fixed

- **The first rung's costs are not yet whole** (blind review). The desk's one cost model
  has commission and currency conversion only: no spread, slippage or sale-only fees (a US
  sale's regulatory fee), and no home for what a sale costs, so the rung charges a sale
  what a buy of the same shares costs beyond its value (on dollars, a little more than the
  truth). One exchange rate serves a whole window, so a dollar line's verdict carries no
  currency gain or loss. All are owed before any verdict on real prices; asked of the money
  lane: a sale's cost, spread and slippage in `desk/orders.py`.
- **What else the blind review of the first rung left** (nothing blocking now; its two
  blocking findings, the desk's stop left out and a loose test of the statistic, are
  fixed): a verdict carries its record's key, whose code version does not cover
  `lab/rung.py` or `desk/orders.py`, so verdicts must not be kept by that key; a line whose
  one share costs more than its room fails the whole verdict loudly; and at two standard
  errors about one cell in forty passes by chance, so a batch of many cells needs the luck
  rung before any winner is believed.
- **The luck rung's chance is honest only for bell-shaped trades** (blind review, its one
  blocking finding: the module had promised the 5% without saying so; it now says so). A
  rule with many small wins and a rare large loss, judged on few trades, reads as far less
  chance than it is: on made-up trades of that shape with no edge (95% win 1%, 5% lose 19%),
  about a fifth of thirty-trade trials beat a correction for a hundred trials, and about one
  in twenty of sixty-trade trials. The cure belongs to the book's box "the luck test fixed
  before any result" (a deflated Sharpe, which reads skew and fat tails) and to "failing
  fairly" (effective trades). **No winner on real prices is to be believed before then.**
- **The count is the caller's to give.** The rung counts every verdict it is handed and
  every trial the caller says left none; handed one batch, one line or one strategy at a
  time, it would count only that. A cell whose gains have no spread at all stops the first
  rung and leaves no verdict, so it too must be stated. Nothing yet keeps the count from
  batch to batch: a register of every trial ever tried is a box in the book.
- **What else the blind review of the luck rung left** (nothing blocking): the 5% line
  itself is not held by a test (a chance landing on exactly 5% does not arise from real
  numbers; "under 5%" for "5% or under" survives, as does a slightly coarser sum inside the
  chance); the chance asked for no trades, or the count given as a fraction, is not refused
  in plain words (neither can arise from a verdict); and `rung.verdict`, the first rung's
  pass rule as one function, is called by the first rung and by the luck rung's tests only.
- **Two deliberate breaks of the first rung survive, neither able to differ:** a pass bar
  of "over 2" for "2 or over" (a t of exactly 2 does not arise), and the rung's arithmetic
  setting (the caller's default is the same).
