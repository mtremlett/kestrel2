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

Last updated: 13 November 2026 (any broker behind the send path).

### Where it is

Scenes 5 of 7. Built and real (its decisions in `docs/DECISIONS.md`): the five rules
(`strategy`); sizing, cost and the gate (`orders`); the pretend broker (`broker`); the send
path, the ledger, the book and reconciliation on one comparison (`book`); the day's trading
(`day.trade`). Any broker can stand behind them (`broker.Broker`: five questions, holdings
and stops as entries, read once for each order). Unfinished, raising NotImplementedError by
design: `day.run`, the day's record (phase 2); scenes 6 and 7 both read it, so pass together.

### Next step

The kill switch and its drill (EMG-02; his ruling: first of the lane's own book), cancelling
a sixth question of any broker. Then the costs whole (R-RUNGS-1), and the day's record
(`day.run`), scene 6 moved onto the fourteen months.

### Done for other lanes

- R-PAPER-2: done in this pull request

### Requests to PAPER

- [ ] R-MONEY-4 (later, opened 2026-11-13 18:35 UK): `paper.differences` asks `book.differences`.

### Requests to DATA

- [ ] R-MONEY-2 (blocking, opened 2026-11-13 18:15): the scenes moved onto the fourteen months.
- [ ] R-MONEY-3 (later, opened 2026-11-13 18:15): a daily rate, pounds per dollar, in the store.

### Found, not fixed

- **Costs:** spread, slippage and UK tax are in no fill, round trip, `orders.cost` or the gate
  yet; money has no one rounding policy (to the penny); the fees are IBKR UK's fixed schedule,
  not the tiered one; scene 3 does not part the currency cost from commission.
- **Nobody is told of a mismatch yet.** Until someone acts, a line whose stop was cancelled is
  unprotected, and one partly sold by hand keeps a stop for more shares than are held.
- **The ledger** is not forced to disk, and a lost one reads as "no fills" without a word.
- **The gate** takes the book as a bare mapping, trusts the stop of an order built by hand,
  and sizes at the last close: a gap up at the open can fill above a fifth.
- **The day run** decides each line's whole history again every day (24 seconds in scene 5),
  reads the archive it is handed (R-DATA-3), and has no halt to read yet.
- **The rules:** a decision depends on where the history starts; "warming up" and "staying
  out" both read as hold; twenty days means twenty bars; the true range lives in `strategy`.
- **For the paper adapter:** fills must be the desk's own orders and stops only; orders still
  working must be counted by the gate and by reconciliation; a connection lost while reading
  is not a stated answer; a stop on a line the book lacks needs its own test there.
- **Untested at the pretend broker:** `inject` on any symbol; a planted position beside the
  desk's stop; a partial fill of one share; several stops sold on one open.

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

Last updated: 13 November 2026 (each line's UK tax).

### Where it is

Phase 1's data is in. The twenty lines are in the
instrument master (`desk/lines.py`), by the operator's ruling of 13 November: ten in
London in pounds, ten in the US in dollars. One client for the free archive
(`desk/archive.py`, Yahoo's public chart service) fetches every bar since 2010 and reads
it once, on entry. Fetched into a store on 13 November for the 13th: **sixteen of the
twenty are clean and ready**: all ten US lines from 2010, and SMGB, IITU, VHYG, IB1T, ISF
and VUSA. Four are parked, each with a named reason (below, under "found, not fixed"). Two
store rules came from his rulings the same day: a London auction price up to 3% outside
the day's range stretches it, and only a fault in the last sixty sessions parks a line
(older bad days are dropped and listed in the line's fault record; a price step parks
however old).

The desk has one price store with one writer (`desk/store.py`): it rebuilds itself from the archive each morning,
keeps only bars that can be true, and parks a line it cannot clean with a dated reason;
the line comes back by itself once its bars are clean. Gaps and staleness are judged
against each venue's own calendar (`desk/venues.py`, London and US, 2010 to 2027). Its
tests were seen failing first; a blind review's five blocking findings were each made a
failing test, then fixed; and twenty-five deliberate breaks of the store, the
calendar and the instrument master were each caught by a test. This session's three store
rules were each driven against deliberate breaks in both directions, and caught.

The scenes' rehearsal data (`tests/scenes/rehearsal.py`, this lane's) is now fourteen
months long, September 2024 to 14 November 2025, each line on its own venue's calendar:
London lines trade 307 days, US lines 303. It rises, falls, breaks out, dips sharply and
falls again, and each of the five rules buys and sells on every one of the nineteen clean
lines (his ruling of 13 November). The scenes still see only its last six weeks, which
hold no holiday on either side, until scene 2 can count two calendars (below).

One line the archive cannot be reached for, or whose answer is refused, is now parked alone
with the reason, and the other lines carry on (`archive.gather`, `store.Refused`): a dropped
connection, a half-delivered answer, a timeout, a missing page or an answer about the wrong
line each park only that line, and the store keeps no bars for it, so none from an earlier
day can be read as today's. An answer of a shape the desk does not know still stops the
whole fetch. Its tests were seen failing first; six deliberate breaks were each caught; a
blind review's one blocking finding (a half-delivered answer stopped everything) was made a
failing test and fixed.

A frozen feed is now caught: five sessions or more in a row, each repeating the bar before
it (its volume too, or with none) or flat at its close with nothing traded, are dropped and
listed, and the line parks if the run reaches the last sixty sessions. On the real archive
the twenty lines' longest such run since 2010 is three sessions (2MU, December 2022), so it
parks no clean line: the same four stay parked, for their old reasons. Tests seen failing
first; nine deliberate breaks each caught; a blind review, nothing blocking, its one design
point taken (a bar repeated whole, volume too, is frozen).

A suspension can now be recorded on its line in the instrument master (`Line.suspended`),
as a real move is: the store expects no bar on that day, so the line is not parked for the
gap. A gap nobody has recorded still parks a line whose last sixty sessions it touches, and
its reason now says the way out: "a gap in the archive, or a suspension the line does not
record". A bar the archive gives on a recorded day is refused, and a day its venue did not
trade cannot be recorded. None of the twenty has a suspension today. Tests seen failing
first; four deliberate breaks each caught.

A real one-day crash is no longer thrown away as "a wrong unit". Only a bar, or a short run,
with a price a hundredfold out of line with its neighbour (pence among pounds) is dropped as
bad data; any other move out of line, even for one day, is kept in the history and parks the
line, however old, until each of its closes is recorded on the line (`Line.real_moves`), as a
step in the price already did. On the real archive this kept 5QQQ's crash of 7 April 2025
(the tariff sell-off: down 40% at the low, half won back the next day), which the store had
been dropping; the same four lines park as before, and no clean line is touched. A crash
straight after days in the wrong unit is now kept too. Tests seen failing first; seven
deliberate breaks each caught; a blind review, nothing blocking, its one finding of the
same kind fixed.

The research list is built (`lab/universe.py`), by his ruling of 13 November: the S&P 500
(503 tickers), the Nasdaq 100 (101), the FTSE 350 (347: three members London quotes in
euros are left off, a currency no line can state yet) and the 200 most-traded US funds of a
field of 330. Shares on two lists counted once, that is **1,065 tickers**, not the "about
1,500" first guessed: the four lists overlap. It sits in `lab/`, which the trading core may
never import, so being on it makes nothing tradable; a ticker the desk also trades (ten are)
is the instrument master's own line. One command (`universe.keep`) fetches each ticker's
bars since 2010 and keeps them through the one store's checks, one ticker at a time, each
venue in its own folder, since one symbol can be two companies (BA is Boeing in New York and
BAE Systems in London; thirteen symbols are shared). Driven on the real archive for 13
November, in about ten minutes: every one of the 1,065 answered, 4.1 million daily bars;
**864 are clean and 201 parked**, every one of the 201 for a one-day move larger than the
store believes that nobody has recorded (406 moves; the commonest days are the flash crash
of 6 May 2010, March 2020 and the day after the Brexit vote). Tests seen failing first; of
thirty-one deliberate breaks, twenty-eight were caught at once, two once their tests were
added, and the last, a change of order, changes nothing; a blind review's two blocking
findings are fixed or decided (`docs/DECISIONS.md`).

Every line now states what a purchase pays in UK transaction tax (`Line.uk_tax`), asked by
the money lane (R-MONEY-1). One table in the instrument master holds the two rates: nil for
a fund or an exchange-traded product, and a UK share's stamp duty, half of one per cent of
what is paid. A line can state only one of the two, and only a London line can pay: any
other figure, or a US line with UK tax, cannot be made. Each of the twenty trading lines
states nil. For the five London funds (SMGB, IITU, VHYG, ISF, VUSA) that is confirmed from
the tax office's own manual. For the five London products (3LGO, 2MU, 5QQQ, IB1T, SGLN) it
is how the law reads and what brokers say, but no official page or issuer's document naming
them was reached: it is to be seen on a real contract note (`docs/DECISIONS.md`). The
research list's 347 London shares are each charged stamp duty, an assumption not checked
name by name (below). One London line of the rehearsal data (L01) is now a UK share: over
the fourteen months the rules buy it three times and its stamp duty comes to £29.66, so the
day's record has a tax to count. Tests seen failing first; seventeen deliberate breaks,
fifteen caught, one that changes nothing, and one no test can see yet (the rehearsal line's
tax: nothing reads it until the money lane builds the day's record); a blind review's two
blocking findings, both of wording that claimed more than was proven, are taken.

### Next step

R-MONEY-2, the money lane's other blocking request: the scenes moved onto the whole
fourteen months (`SCENES_FROM = FIRST`), a short session of its own; until it is done the
scenes see six weeks in which nothing is bought, so no tax is charged there either. Then
the research list's parked fifth: 201 tickers wait for their large moves to be recorded,
most of them real days of a real market. Decide and build how research reads them without
loosening the trading store.

### Done for other lanes

- R-MONEY-1: done in this pull request. `line.uk_tax` is the part of a purchase's value paid
  in UK tax (`lines.NO_TAX` or `lines.STAMP_DUTY`, an exact decimal); a sale pays none. In
  the rehearsal data L01 pays it. For the money lane to know: the tax is not yet in
  `orders.cost` or the gate, so a taxed buy sized to its fifth can pass it by the duty (L01's
  first buy is £1,967.67 before £9.84 of duty, so it fits today); the tax office collects it
  to the penny, which belongs to the day record's one rounding policy; and the money lane's
  note that the ten London lines are "assumed nil" can now point here.

### Requests to GRID

- [ ] R-DATA-1 (later, opened 2026-11-13 18:15): a cell names its ticker's venue. `lab/cell.py` accepts
  only the twenty trading lines and knows a line by its symbol alone; the research list has
  thirteen symbols that are two companies. Take a `Line` from `universe.UNIVERSE`, and read
  its bars from its venue's folder: `store.read(root / line.venue, line.symbol)`.
- A parked research ticker keeps its sound bars and can be read, but 201 of them hold a
  move nobody has confirmed; `universe.keep` returns them by line with the reason.
- Every ticker is a member today: a result over the past on this list has survivor bias,
  and its report must say so (canon B6).

### Requests to MONEY

- [x] R-DATA-2 (blocking, opened 2026-11-13 18:15): scene 2's count made each line's own, the number of
  bars each line has, added up, times five (done by the money lane before requests were
  numbered).
- [ ] R-DATA-3 (later, opened 2026-11-13 18:15): the day run reads the archive through `archive.gather`
  and hands its answers to `store.prepare` whole, so a refused line arrives as
  `store.Refused` and parks with its reason; `day.run`'s `archive` parameter would then be
  `Mapping[Line, Sequence[Bar] | Refused]`.
- `SESSIONS` will then be every day either venue trades; a day run on it meets days only
  one venue trades (Thanksgiving, Easter Monday).
- [ ] R-DATA-4 (later, opened 2026-11-13 18:40 UK): every `Line(...)` in the money lane's tests
  states its UK tax as a fifth fact (`NO_TAX` or `STAMP_DUTY`). Once the paper lane's do too,
  the data lane removes the default, so a line cannot be made without saying what it pays,
  as with leverage.

### Requests to PAPER

- [ ] R-DATA-5 (later, opened 2026-11-13 18:40 UK): every `Line(...)` in `tests/unit/test_paper.py`
  states its UK tax as a fifth fact (`NO_TAX` or `STAMP_DUTY`), for the same reason as
  R-DATA-4. And when the first conformance trade buys a London product, its contract note
  shows whether stamp duty was charged: tell the data lane what it says.

### Found, not fixed

- **What each line's UK tax leaves open** (blind review; its two blocking findings taken):
  - **The five London products' nil is not confirmed from an official source.** 3LGO, 2MU,
    5QQQ, IB1T and SGLN are debt of issuers outside the UK, not funds, so the 2014 exemption
    for funds does not name them. Nil is how the law reads and what brokers say; the
    issuers' prospectuses could not be fetched. He can settle it in a minute: the order
    preview for any of them at his own broker shows whether stamp duty is charged. If one
    pays, it is one word on its line.
  - **A line made without stating its tax pays nil.** Leverage cannot be left out; the tax
    can, because the other lanes' tests build lines from four facts and this lane may not
    edit them. The twenty lines, the research list and the rehearsal lines each state it.
    Asked of the money and paper lanes (R-DATA-4, R-DATA-5); then the default goes.
  - **The research list's London shares are all charged a UK share's stamp duty, unchecked
    name by name.** A member registered outside the UK most likely pays none (the review
    names, from memory, EXPN, GLEN, WPP, WIZZ, CCH, HSX, LRE and Channel Islands trusts
    such as 3IN, INPP, TRIG, SEQI, BHMG, HVPE, NBPE, PSH, VOF, VEIL, TFIF, RTW), so research
    overstates their cost by half a per cent a purchase. One registered in Ireland (DCC,
    GFTU, GNC) pays Ireland's 1%, and IAG may pay Spain's tax instead: rates no line can
    state yet, so their cost is understated. Nothing trades on this list.
  - **The takeover panel's levy is not modelled:** a flat pound or so on a trade over
    £10,000 in a UK company's shares, on sales too. No trade is that large at £2,000 a
    holding, and none of the twenty is a UK company's share.
  - **Each line's kind was written from what the session knows of the ten products**, not
    read from the broker or the exchange. The paper lane's next step reads each line as the
    broker knows it; a fund that turned out to be a share would show there.
  - Nothing tests that the rehearsal's taxed line is bought; scene 7 will, once built.
- **Four of the twenty lines are parked, each for a reason in the archive's data:**
  - 3LGO has no history in the free archive at all (the same product in dollars, 3GOL,
    has fourteen years). He chose to keep 3LGO; it waits for history to gather.
  - 2MU moved more in a day than the store believes a market moves, five times (5 August
    2024, 26 September 2024, 19 December 2024, 4 April 2025, 24 October 2025): real crashes
    of a 2x product, most likely. Each needs its confirmed close recorded in
    `Line.real_moves`, from the issuer or a second source, before the line comes back.
  - 5QQQ jumped from 0.0024 to 1.18 pounds on 22 August 2024: a share consolidation the
    archive did not adjust. Its history before that date is on another scale.
  - SGLN's first weeks, April to June 2011, swing between two price levels ten times: the
    archive garbled them. A price step parks however old, so the line stays parked.
- **The free archive promises nothing.** Yahoo's chart service is free and keyless but
  unofficial; it may change or stop. Stooq, the other free archive, now answers with a
  bot check, which this desk does not get around.
- **None of the five rules ever buys in the six weeks the scenes see today.** The fourteen
  months are built and proven to trade; scene 5 needs the scenes moved onto them (above).
  Until then no test reads the months before October, so only the script recorded in
  `docs/DECISIONS.md` shows they park nothing clean and that each rule trades in them.
- **The research list, as fetched on 13 November** (`lab/universe.py`):
  - A fifth of it is parked: 201 of 1,065, for 406 unrecorded one-day moves (93 US tickers,
    108 London). Eighty-nine have one move only. Nothing fills `Line.real_moves` for a
    research ticker, and its list has no place for one.
  - It is today's members only, so the past studied on it is the survivors' past. The
    lists' members year by year are not held.
  - The research store is not kept anywhere yet: the fetch that proved it wrote 327 MB to a
    scratch folder on his PC. `universe.keep` rebuilds it in about ten minutes; where it
    lives, and its nightly refresh, come with the grid's first pass.
  - A ticker the archive refuses for a day (a timeout, a throttled answer) loses its bars
    until the next run, by the store's one rule (`docs/DECISIONS.md`). The proving run
    paused a fifth of a second between tickers and was never refused; `universe.keep`
    itself does not pace its requests.
  - A ticker that leaves a list keeps its old files in the store, and a run stopped part
    way leaves no mark of which tickers it reached. The store holds no record of the day or
    the list it reflects.
  - Three FTSE 350 members quoted in euros in London (BCG, MTLN, PEY) are left off: a line
    is in pounds or dollars. Five quoted in dollars there are in.
  - The 200 funds are the most traded of a field of 330 drawn up by the session, not of
    every US fund: no free list of all of them by value traded was found. Funds that move
    against their market, whose multiple has changed, on a single share or tracking
    volatility are not in the field.
  - Each ticker's name was checked only by the archive answering to it: a symbol that
    exists but belongs to another company would pass.
  - On the 1,065 the store dropped 770 frozen runs, 750 days with a price outside the
    day's range and 265 bars on closed days, and found 314 gaps; none is recent enough to
    park a ticker, but the rules were tuned on twenty lines, and thinly traded London
    trusts may truly sit still for a week.
  - PRN (a FTSE 250 member) is a reserved file name on older Windows; it wrote normally here.
- **What the blind review of the store's rules left open** (its one blocking finding - a run
  of days in the wrong unit taken as a lasting step - is fixed and tested; the first fix
  dropped 2MU's real December 2024 crash as bad days, so a run is now bad days only when it
  sits a hundredfold out):
  - A stretched bar's new high or low is not recorded anywhere as differing from the
    archive's.
  - A line's bars and its fault record are swapped in one after the other, so a crash
    between the two leaves them disagreeing.
  - The sixty-session window looks back a hundred days on the calendar, which knows 2010
    onward, so a trading day before mid-April 2010 cannot be prepared.
- **What the blind review of the store left open** (its five blocking findings, and one
  its re-review found in the repair, were fixed and each is now a test):
  - The calendar knows 2010 to 2027 only. A bar from another year is refused and its
    line parked; history before 2010 needs that decade's one-off closures first.
  - A split the archive did not adjust parks the line if it is 2-for-1 or larger; a
    smaller wrong factor (a 3-for-2 split, pounds read as dollars) cannot be told from
    a real move by price alone and passes.
    So does a whole history quoted in pence by an archive that says pounds: pence
    become pounds only when the archive names them pence.
  - A real move larger than the store believes (a fall of 37.5%, a rise of 60%) parks
    the line until its confirmed close is recorded on the line (`Line.real_moves`).
    Nothing fills that record yet; 2MU is parked for want of it.
  - Two bad bars in a row are kept and the line parked, not cleaned: safe only while a
    parked line is never traded or read for a decision.
  - Parking lives only in what `store.prepare` returns (each line's faults are now
    saved beside its bars, but not whether they parked it), and a line dropped from the
    archive leaves its old files readable. The day run (phase 2)
    must read parking from the prepare it runs.
  - A vendor that leaves out a day a line did not trade (a suspension) parks the line
    while the gap is in its last sixty sessions, until the suspension is recorded on the
    line (`Line.suspended`), from the exchange or a second source. Nothing fills that
    record yet, and nothing tells a lost day from a suspension by itself.
- **What the blind review of the refused line left open:**
  - A whole outage (no network, the archive down) parks every line one by one, each with
    its own reason, rather than saying once that the archive is down. Safe, as nothing
    trades, but noisy.
  - Any `ValueError` while reading an answer parks the line, as the answer's fault. Today
    each one comes from the answer; a future fault of the desk's own there would park a
    line instead of stopping. One named error raised by `archive.parse` would close this.
  - An answer of an unknown shape (a missing field) stops the whole fetch, by design: it
    would hit every line alike.
  - Nothing in the product calls `archive.gather` yet; the day run (phase 2) will.
- **What the blind review of the one-day crash left open:**
  - A bad print of a size other than a hundredfold (a tenth, a decimal slip) is now kept
    and parks its line however old, and the only way out, `Line.real_moves`, records real
    moves: there is no record of a known bad day. None of the twenty has one today.
  - No test pins the hundredfold margin itself (62.5 times) on either side.
- **What the blind review of the frozen feed left open:**
  - A freeze younger than five sessions is not caught: up to four days of a stale price
    can be traded on. Lowering the five would park real lines (2MU has runs of three).
  - A run whose first stale day already sits flat, with no volume, at a new price counts
    from the day after it, so it needs one session more to be caught.
  - A frozen run's days are also counted as missing sessions, so its reason says it twice.

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
