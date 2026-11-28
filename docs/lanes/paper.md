# The paper lane

The paper lane's own decisions, each a dated `###` entry saying what was decided, the
options, why, and the evidence; newest last. Only this lane's scribe writes here, so no
other lane's pull request touches these lines. Held to a size a session reads whole
(`BUDGET.json`, `max_lines_per_lane_doc`): when it is full, the scribe folds the oldest
settled entries into one short summary entry; git keeps every word.

## Decisions

### 2026-11-13 — the paper account is read, never written, and only if it is a paper one

**Decided**, by the lane as the desk's mentor (no one watching), for the first box of its
book: the desk's one door to the paper broker (`desk/paper.py`) reads the account's
holdings and resting orders and names every difference from the desk's book. It sends the
gateway four things and no others: a greeting, a start, and two questions.

**The choices, and why.**
- *How to speak to the gateway.* Options: the broker's own Python client or a popular
  wrapper (each a new dependency, and `desk/` may import the standard library alone); or
  the gateway's own language over a plain connection. Chosen: the plain connection. This
  step needs two questions and four kinds of answer, about a hundred lines.
- *Which version of that language.* The gateway changes the shape of its messages from
  version to version. Options: accept a range and carry a reader for each; take the newest
  (it has since moved to another encoding); offer one version and refuse any other answer.
  Chosen: one, version 176, which the gateway on his PC accepts and a widely used published
  client reads. A gateway that will not speak it stops the check with that reason.
- *The desk's client id.* Options: 0 (the gateway's master id, which can take over orders
  placed by hand: never); a small number the old desk may still use; one fixed number of the
  desk's own. Chosen: 222. If anything else ever holds it, the gateway refuses the desk
  with a stated reason; the desk does not hunt for a free one.
- *Only a paper account.* The broker starts a paper account's code with a D and no other
  account's. The door refuses any other code: in the gateway's list of accounts, before a
  single question is asked, and on every holding and every order. So a gateway logged in
  to a real account by mistake cannot be read as "quiet", let alone traded. A second lock
  beside the port.
- *What "quiet" means today.* A holding is matched to the book by its symbol, its kind (a
  share or fund) and its currency, so the same name in another currency, or as another kind
  of product, is a difference. A line the broker lists at no shares is no holding. Each
  entry the broker gives must itself be the book's shares: the first version added a line's
  entries together, and the blind review showed that a holding changed while it was being
  read, or 25 bought in one place and 25 sold short in another, would then pass as the
  book. Every order resting at the broker is a difference, whoever placed it, the desk's
  own client included: the desk rests none on paper yet. When the desk's own stops rest
  there (the next box), the check must be taught to know them, and only them.
- *What the check gives back.* The differences, in words (`paper.differences`,
  `paper.mismatches`); none means quiet. It was first called "quiet", which a caller could
  read backwards and trade exactly when the account was not; the review caught the name.
- *The gateway's news.* It sends notices that its price feeds are up or down, which this
  door does not use: those nine codes are passed over. Any other notice or error (the
  client id taken, the link to the broker lost) stops the reading, as does a kind of message
  the desk does not know. A reading that stops is never a clean one.
- *The plan's first box, split in two.* The check exists and has run clean once; nothing
  yet runs it each day or makes the desk wait for it. That half belongs to the adapter,
  which must refuse to send until the day's check is clean, so it stays an open box.

**Evidence.** From the real gateway on his PC, read-only, 13 November at about 17:45 UK,
through the door's own code: it greeted in version 176, named one account, a paper one,
and listed seventeen lines the old desk once held, each at no shares, and no order
resting; against the desk's empty book the check named nothing. With the desk's client id
already connected, a second connection was refused by the gateway ("326: the client id is
already in use") and the desk stopped on it. The tests' messages are the gateway's own
from that reading, with the account's code changed; only the open order is taken from the
published client, since none rested to copy. The contract test was seen failing first (no
module), and again for each of the review's fixes. A blind review checked every message
number and field position against the published client and found them right; its one
blocking finding (entries added together) is fixed and tested, and its nine lesser points
are taken or recorded in `docs/STATUS.md`. Sixty-five deliberate breaks were driven in a copy
outside the repository: fifty-nine were caught at once, and six showed a gap in the tests,
each now closed and caught (the symbol read from the wrong field, asking before the
gateway is ready or has named its accounts, another port, the two lists ending in the
other order, and reading the connection as text). One lesson for every lane's breaks: a
break written less than a second after the last, to a file of the same size, can run the
old code from Python's cache and report the wrong result; the breaks were run again with
the cache off before these numbers were written.

### 2026-11-13 — each line as the broker lists it: asked each time, pence and pounds, and a line it does not list

**Decided**, by the lane as the desk's mentor (no one watching), for the next box of its
book: the desk asks the paper broker how it lists each of the twenty lines
(`desk/listing.py`) and gets back, for each, the broker's own number for the line, the
exchange it lists it on, whether it prices it in pence or in pounds, and its price steps.
Two questions are sent through the one door, neither of which can place an order.

**The choices, and why.**
- *Where the broker's facts about a line live.* Options: on the line in the instrument
  master (the money lane's review of sizing had suggested the master carry the price step);
  in a table in the paper module; or asked of the broker each time. Chosen: asked each
  time, nothing written down. A price step is not one number: the broker gives a rule of
  bands (IITU moves in tenths of a penny under £5 and whole pence above £25), the rule
  differs from line to line, and the broker and the exchange change it. A copy would be a
  second home that goes stale in silence; the question also proves, each time, that the
  broker still lists the line. The instrument master keeps the desk's facts, the broker
  its own.
- *How the desk knows the broker's line is its own.* The desk asks by the line's name, as a
  share or fund, in its currency. The answer must come back exactly once, under that name,
  kind and currency, on an exchange of the line's venue. The broker's names for those
  exchanges are written in the module, each one seen from the gateway on one of the twenty
  (London's funds list; Nasdaq and Arca; none of the twenty lists in New York): a line
  listed anywhere else is unlisted until its exchange is added on purpose.
- *A line the broker does not list.* Options: stop the whole reading; or name that line
  with the reason and carry on. Chosen: carry on, as the data lane ruled for a line the
  archive refuses. A leveraged product can be closed by its issuer; nineteen sound lines
  should not stop for it. The line comes back as "unlisted" with the broker's own words or
  what differed, a different kind of record from a listing, so the adapter cannot build an
  order for it by mistake. An answer the desk cannot read (a message of another shape, an
  answer to another question, any error but "no such line") still stops the whole reading:
  a reading that stops is never a clean one.
- *Pence and pounds.* The broker prices six of the ten London lines in pence (3LGO, 2MU,
  IITU, 5QQQ, ISF, SGLN) and four in pounds (SMGB, VHYG, IB1T, VUSA), while it calls the
  currency of all ten pounds; the desk's prices are all pounds. The broker's rule of steps
  speaks in pounds. So a desk price is first put down onto its step in pounds, then
  multiplied into the broker's unit (`Listing.floor`): £37.556 on IITU becomes 3755. This
  was not taken from the broker's documents but tested on its own prices (below).
- *Which steps.* A line has a rule for each place the broker can send its order. The desk
  reads the rule of the broker's own router, where its orders will go, the route the
  question itself is asked on.
- *Down, never to the nearest.* A stop is put down onto the step, so it stays below the
  price it was set from (an order whose stop is not below its price cannot exist). The
  cost is a stop up to one step lower than the 10% rule's exact figure. A price with no
  step at or below it is refused, and so is one that is not a finite number.
- *A listing the desk cannot trust is no listing.* The record cannot be made at all
  unless it has a real number for the line, a unit the line's currency is priced in (a
  hundredth for pounds alone: pence; never for dollars, and never a tenth), and steps
  that are steps: finite, above nothing, starting from a price of nothing, each band above
  the last and starting on its own step. The reading stops on anything else. So the wrong
  unit, the fault that would put a stop a hundred times out, cannot be carried in a
  listing.
- *The gateway's notice that it cannot look lines up.* The account check passed over nine
  notices about the gateway's price feeds. One of them (2157) says the service that
  answers questions about lines is down; the blind review showed that passing it over
  could let an outage be read as "the broker lists nothing", every line unlisted. It now
  stops any reading, the account's too: one rule, and a gateway in that state is not one
  to trust on anything. The other eight are still passed over.

**Evidence.** From the real gateway on his PC, read-only, 13 November at about 18:35 UK,
through the module's own code, and again after each repair: twenty of twenty lines listed,
each exactly once under the desk's name and currency; all ten London lines on London's
funds list, eight US lines on Nasdaq, SPY and GLD on Arca; six London lines priced in
pence, four in pounds; twelve different rules of steps among them. A name the broker does
not know was asked on purpose and answered "No security definition has been found", the
answer the desk reads as unlisted; a name asked without its currency came back twice
(Boeing in New York and its Canadian receipt), the case the desk names as listed twice.

*Pence or pounds was proved on prices, not taken from a manual.* The open, high, low and
close of each line's last thirty sessions were read from the broker (a question about past
prices, read-only, asked from outside the repository): 2,392 prices. Put through
`Listing.floor`, every price of nineteen lines came back unchanged: it already sat on the
step, in the unit, that the desk had worked out. Then the finer test, since a rule read a
hundred times too fine would pass the first: in each band of each line's rule the prices
were found to move in exactly the listing's step and no finer one, in twenty bands of
twenty-one (whole pence on IITU, 3LGO and SGLN; a tenth of a penny on 5QQQ; a fifth on ISF;
a quarter of a penny on VUSA; a cent on every US line). The twenty-first is 2MU above £500,
where the broker's rule says £5 and the market moved in £1; below £500 it moves in the
rule's £2 exactly. That one is recorded in `docs/STATUS.md`; 2MU is parked.

The contract test was seen failing first (no module), and again for each repair. A blind
review, which checked every field the desk reads against the gateway's twenty real answers
and the published client, found two blocking faults: the look-up notice passed over, and
infinite or not-a-number prices and steps let through. Both are fixed and tested, with its
lesser points on the rule's number, the unit and the broker's number for the line. Its
second reading approved the repair and found the rules being read before the line was known
to be the desk's; that is fixed and tested too. What it left is in `docs/STATUS.md`.

Deliberate breaks, driven in copies outside the repository with Python's cache off: 113
over three rounds, 101 caught at once. Five showed a gap in the tests, each closed and
caught when driven again (a cut-short "no such line" notice, a London line priced in
pounds, an infinite band edge, and a listing one field short or one over whose rules still
read). Five different breaks survive, seven runs in all. Four cannot change a result: a
band taken to begin just above its edge, which differs only on a rule whose edge is off the
step below it, and none of the twelve real rules is; a pairing check behind a length check
that already forces it; and two that pick the last of exactly one. The fifth adds New York
to the US exchanges, which no test forbids: adding an exchange is a deliberate edit.

### 2026-11-13 — the paper lane's book ordered: read-only first, placing last, one new module per box

Options and choices (from #68):
1. Kill-switch refusal: first in the book, or after the adapter whose send it guards. Chosen:
   after. The refusal is a line in the adapter's send and reads the money lane's drill record,
   which is not built. Nothing is loosened: paper-conformance, the first real paper order, waits
   for paper-drill.
2. Should paper-drill and paper-conformance name the money lane's kill switch in `after`? Chosen:
   only this lane's ids for now, as the money lane has not noted its book and the check refuses an
   `after` naming no box. The wait is held by the box text, the four boxes in front, and the lane
   objective. Owed: add the id to paper-drill's `after` once it exists.
3. Order: reports, daily check, adapter, stops, drill refusal, then a real order, following "built
   from what it reads towards what it sends".
4. New modules (`reports`, `gateway`, `clearance`, `placing`) or all in `desk/paper.py`. Chosen:
   their own: paper.py is 216 of 400 lines, and separate files let paper-gateway run beside the
   chain. A session finding one unnecessary need not create it.
5. paper-conformance holds every file (`files: *`): it runs on the real account in market hours
   and may fix any module where the broker differs, so it runs alone.

### 2026-11-14 — a buy goes with its stop; the line settled after any order (paper-adapter, paper-stops, #123)

Decided by the PAPER lane as the desk's mentor, no one watching.

- *How a buy and its stop go together.* Options: (a) send the stop after the buy fills: a second or two with no stop, and a
  dead desk leaves shares unprotected; (b) attach the stop to the buy so the broker holds both, then settle; (c) rest the
  stop first: impossible without risking a short sale. Chosen: (b); if the stop's half is refused the buy never reaches the market.
- *Which shares the stop is for, and on what evidence.* Options: (a) the desk's own sum, checked against the account;
  (b) the account's shares alone; (c) size from the account, and act only when the account moved by exactly the order's
  fills and "filled" is borne out by fills. Chosen: (c), after the blind review showed five ways the sum is silently wrong.
  When the three disagree nothing is changed and an error is raised.
- *A sale: take shares off the stop before or after.* Chosen: after, by what happened; one mechanism for buys and sales.
  For a moment the stop is for more shares than held (recorded, not fixed).
- *Replace a stop, never change it in place* (changing a stop attached to a buy is unproven); new first, then cancel the old,
  so a line is never under none. A line whose stops are unsettled is refused, buy and sale alike. A stop already right is
  kept whatever its name; a stop the broker is not holding counts as none.
- *The broker's notice 202 (order cancelled) is news, not a fault, in every reading.* This changes one line of #110's test:
  cancelling a buy makes the broker cancel its stop and say so. The comparison of book with broker still names any line left bare.
- *A stop with no price at the broker* stops the buy with an error before anything is dialled. The stop rests until
  cancelled (GTC), plainest kind. A stop that ends some other way while being cancelled is an error unless the shares are as read.
- *Both boxes ticked.* No test order was sent to the real Gateway: one wrong field could make a real order on a shared account.
- The tests' pretend Gateway moved into the door's test file (no test changed): the placing tests were at the 400-line cap.
- Evidence: tests seen failing first; blind review, one blocking finding fixed; 60 + 25 + 31 deliberate breaks, 2 that cannot differ.

### 2026-11-14 — the paper book's next boxes ordered for the runner (#128)

Decided by the PAPER lane as the desk's mentor, no one watching.

- *Messages and the unattended day ahead of conformance.* Options: conformance next; boxes needing no market first. Chosen:
  the latter: it is a weekend, and conformance holds every file so would stall the lane until Monday. The code already
  refuses any order without a drilled kill switch and clean check.
- *Supervision after conformance:* its box needs seven days without an operator action and would hold the first paper trades.
- *Conformance keeps `files: *`:* nobody has seen where real results are recorded; a missed file would stop the session.
- New modules named before they exist: `desk/messenger.py`, `desk/running.py`, `desk/supervisor.py`. paper-running also holds
  `desk/placing.py` for R-MONEY-8 and waits for paper-messages so there is one messenger.

### 2026-11-14 — the desk's one voice (#142)

Decided by the PAPER lane as the desk's mentor, no one watching.

- *Alarm on silence:* the desk alarming itself (a dead desk cannot); only a human rule; a watch outside the desk reading the delivery record. Chosen the watch, with the human rule beside it.
- *Hours:* morning 08:00 (05:40 was in his night), owed by 08:30; evening 21:05, owed by 21:30 (21:00 sat on New York's bell on 465 of 502 sessions). Nothing sent from 22:00; only the alarm goes at any hour.
- *The record is SQLite,* not a CSV: two writers by design, and two processes drove the CSV unreadable within six writes.
- *Asked on the record before the door; told twice rather than never.* A lost Telegram answer means a resend.
- *Over-long messages* are cut at the door and kept whole on the record. *The key* comes from `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`; giving it to the desk is his alone.
- *The morning message claims only what it asked* (Gateway, the day's check, kill switch and drill). The merge line and runner alerts stay outside until paper-cards.
- Evidence: two blind reviews, three blocking findings fixed; 518 deliberate breaks, 473 caught as driven, gaps closed and driven again.

### 2026-11-14 — the unattended desk (#152)

Decided by the PAPER lane as the desk's mentor, no one watching.

- *A step, not a loop:* a restart then needs no special path; what is done is known from the desk's records (and `running.csv`).
- *Recovery runs whenever the check names something* (not at start, not every step). The stop kept is the newest whose buy really bought, for the shares held, only where they are the book's; read before the dead desk's orders are cancelled. It waits while the kill switch is on or undrilled.
- *The check comes before a record too* (blocking finding). *A round is made once a day,* all answers told to him; an unclean check keeps it owed. Orders go whenever clear, however late (cut-off asked of MONEY).
- *A line with no bar of the session before is left out and named,* not the whole round refused.
- *Record hour:* five minutes after the last closing auction. *His hours:* nothing before 08:00 or from 22:00; a Gateway failure goes at any hour, once per day.
- *The adapter itself refuses an order not dated the session before* (R-MONEY-8), by the venue's calendar.
- Evidence: tests seen failing first; two blind reviews (2 blocking fixed); 78 deliberate breaks, 78 caught; dried read-only at the real Gateway.

### 2026-11-14 — the daily kill-switch drill (#155)

Decided by the PAPER lane as the desk's mentor, no one watching.

- *When:* only when the last drill is over 31 days old; once each day before that day's first work; at each process start. Chosen daily: a step has no start, and a month-old drill says nothing of today's code. The 31-day refusal stays in the adapter as the floor.
- *Where:* after the ledger, before the check (the check may put right with orders). *A failed drill stops everything but the ledger* and the step fails; told once in his words, wrapped from the money lane's error.
- *Any day the desk works,* on the UTC day. No message for a drill that passed.
- Evidence: tests seen failing first; one blind review, nothing blocking; 31 deliberate breaks, all caught; dried at the real paper Gateway with the switch on.

### 2026-11-14 — a buy goes with its stop; the line settled after any order (paper-adapter, paper-stops, #123)

Decided by the PAPER lane as the desk's mentor, no one watching.

- *How a buy and its stop go together.* Options: (a) send the stop after the buy fills: a second or two with no stop, and a
  dead desk leaves shares unprotected; (b) attach the stop to the buy so the broker holds both, then settle; (c) rest the
  stop first: impossible without risking a short sale. Chosen: (b); if the stop's half is refused the buy never reaches the market.
- *Which shares the stop is for, and on what evidence.* Options: (a) the desk's own sum, checked against the account;
  (b) the account's shares alone; (c) size from the account, and act only when the account moved by exactly the order's
  fills and "filled" is borne out by fills. Chosen: (c), after the blind review showed five ways the sum is silently wrong.
  When the three disagree nothing is changed and an error is raised.
- *A sale: take shares off the stop before or after.* Chosen: after, by what happened; one mechanism for buys and sales.
  For a moment the stop is for more shares than held (recorded, not fixed).
- *Replace a stop, never change it in place* (changing a stop attached to a buy is unproven); new first, then cancel the old,
  so a line is never under none. A line whose stops are unsettled is refused, buy and sale alike. A stop already right is
  kept whatever its name; a stop the broker is not holding counts as none.
- *The broker's notice 202 (order cancelled) is news, not a fault, in every reading.* This changes one line of #110's test:
  cancelling a buy makes the broker cancel its stop and say so. The comparison of book with broker still names any line left bare.
- *A stop with no price at the broker* stops the buy with an error before anything is dialled. The stop rests until
  cancelled (GTC), plainest kind. A stop that ends some other way while being cancelled is an error unless the shares are as read.
- *Both boxes ticked.* No test order was sent to the real Gateway: one wrong field could make a real order on a shared account.
- The tests' pretend Gateway moved into the door's test file (no test changed): the placing tests were at the 400-line cap.
- Evidence: tests seen failing first; blind review, one blocking finding fixed; 60 + 25 + 31 deliberate breaks, 2 that cannot differ.

### 2026-11-14 — the paper book's next boxes ordered for the runner (#128)

Decided by the PAPER lane as the desk's mentor, no one watching.

- *Messages and the unattended day ahead of conformance.* Options: conformance next; boxes needing no market first. Chosen:
  the latter: it is a weekend, and conformance holds every file so would stall the lane until Monday. The code already
  refuses any order without a drilled kill switch and clean check.
- *Supervision after conformance:* its box needs seven days without an operator action and would hold the first paper trades.
- *Conformance keeps `files: *`:* nobody has seen where real results are recorded; a missed file would stop the session.
- New modules named before they exist: `desk/messenger.py`, `desk/running.py`, `desk/supervisor.py`. paper-running also holds
  `desk/placing.py` for R-MONEY-8 and waits for paper-messages so there is one messenger.

### 2026-11-14 — a kept listings file naming other lines is read again (R-RUNNER-42, #223)

Options: raise; re-read. Chosen: re-read, because the line set is the desk's own and may change. Unlisted answers are kept too, as the broker's answer for the day. Decided by the lane as the desk's mentor.

### 2026-11-15 — the paper day tells him of a disagreement through the note path (R-RUNNER-91, #295)

Options: a direct `messenger.send` (loses the message if Telegram is down and raises into the money path); the step's note path (sent at every step until delivered, never raises). Chosen: the note path; a blind review found the direct version lost the message.

### 2026-11-15 — a paper sale cancels the line's stop first (R-MONEY-17, #296)

Options for "no sale while a stop rests, unless tied": (a) refuse every such sale (the desk could never exit, every held line has a stop); (b) an OCA group at the broker (new message fields, unprovable on the Gateway that session); (c) cancel the stop and confirm it gone before the sale. Chosen (c); (b) stays the real cure (R-PAPER-25). A stop that ends another way while cancelled gives Refused, not Unprotected: no halt and no message for a benign case. Known risk of (c): a gateway dying after the cancel leaves shares bare until `running.recover` (R-MONEY-30, done in #657).

### 2026-11-15 — the step looks at the market first; the hold is bounded (R-MONEY-25, #300)

Daily bars for the look: the archive (about 4,000 requests a day, and a rehearsal would hit it) or `keeper.saved` (no network, loud `Stale`); chosen `keeper.saved`. The hold lasts only while the reason is EARLY, at most the watch's 20-minute limit; holding forever would stop London for a dead keeper. A look that raises holds the rounds but not the check, recovery or record (failing the whole step was the reviewer's first finding).

### 2026-11-15 — the record waits on `keeper.HELD` (R-DATA-14, #302)

Options: `keeper.target` only; `keeper.HELD`; read `kept.json`. Chosen `keeper.HELD`, the simplest that closes the window (a late keeper still fails loudly as Stale). The evening message therefore reports the previous day until MONEY moves it (R-PAPER-27); left, as messenger was outside the claim.

### 2026-11-15 — a timeout names its call; the limit is raised separately (R-RUNNER-177, #369)

Options: (a) change `paper.SECONDS` and `test_gateway` (outside the claim); (b) a separate longer limit for conversations only (does not help if the knock times out); (c) only name the failing call. Chosen (c) and ask for (a); done as #373.

### 2026-11-15 — the Gateway's wait is 30 s (R-RUNNER-180, #373)

Options 15 / 30 / 60+. Chosen 30: matches `messenger.SECONDS`, doubles a stalled PC's time, far inside one step. Measured read-only on 4002: knock 0.004-0.013 s, account read 0.10 s warm. A true cold start could not be timed without restarting his Gateway. Numbers are in `docs/DECISIONS.md`.

### 2026-11-15 — an Alarm is told by the step's existing trouble note (R-MONEY-36, #385, #483)

Option A: the step's trouble note, which carries the Alarm's words once a day; option B: a separate Alarm handler (a second path for a job that has one). Chosen A under the canon's one-path rule, so no new code. Gap: an Alarm at night is told at 08:00; the kill switch is on by then.

### 2026-11-16 — nothing to change for the opening buy cancelled at 08:06 (R-RUNNER-196, #437)

The conformance buy was cancelled by the desk's own 30 s wait (`Paper.place`), not refused. Options: lengthen the wait for the open; skip rounds before 08:05; leave as is. Chosen: leave. Cancelling is the safe behaviour and waiting longer is a trading-path change with no evidence the order would fill; rounds already start 08:20.

### 2026-11-16 — the rehearsal is barred only near a live market (R-RUNNER-190, #462)

Options: whole-day bar as before; none; a window that fails closed. Chosen the window: barred while a session is open, opens within 90 minutes (a 30-minute run plus an hour), or ended under 30 minutes ago; re-judged before every step. The review found boundaries must fail closed.

### 2026-11-16 — one home for the record's lock wait (R-RUNNER-113, #461)

Same meaning in `messenger.py` and `supervisor.py`, so the messenger imports the supervisor's `WAIT` rather than two renamed constants.

### 2026-11-16 — hourly P&L lives in `command.py` (R-RUNNER-207, #471, #492)

(1) After a real step in `command.py`, not in `running.step` (breaks its test; a rehearsal would send P&L about a past day). (2) A line with no bar yet shows "no bar yet" and counts at its last close. (3) "Holding the market" is the capital times the yardstick's move since its last close. (4) Sent at the first step of each UK hour while a venue is open. Each figure names its base; a line held and added today is measured from the close (simplest), not blended.

### 2026-11-16 — the day's gap uses one cost model on both sides (R-RUNNER-144, #464)

The expected and real fills are marked at the day's close and costed by `orders.charges`, so the gap is the fills' prices alone (the broker's real fees are not read by `reports.py`). Sign: real less expected, negative worse.

### 2026-11-16 — the messenger's email strikes live on its own record (R-RUNNER-16, #484)

Each step is a new process, so the count of Telegram refusals is a counter in the messenger's SQLite record (deriving it from unsent rows misses a retried line). A refused email never stops the Telegram attempt and is tried again on the next line.

### 2026-11-16 — conformance beside the desk's book (R-RUNNER-201, #452)

(a) A lead of 5 minutes before a round (options none/5/15), so a run of about two minutes ends first. (b) A run inside a round is "nothing done", exit 0. (c) The desk's share is every holding on the account when the run begins; the broker has no per-client holdings. (d) One file per run, the once-a-day bar deleted. All on his "always go with recommended". The ledger half (R-PAPER-29) waits on MONEY.

### 2026-11-16 — a stop above the market is a recorded finding; ids carry the minute (#488)

Options for the stop that rests PreSubmitted and never sells: keep it a failure (a red run every 30 minutes, nothing learned) or record it as the finding. Chosen record; loosens no guard. Unique ids by HHMM stamp, not a counter file (no new state).

### 2026-11-16 — the supervisor registers the step at all hours (paper-supervised, #490)

Options: a time window on the Job (more supervisor code); all hours, since the step asks the Gateway first. Chosen all hours; the 03:00 restart may then show as bad receipts, so a window may be needed when the supervisor takes over from the runner.

### 2026-11-16 — health is told from outside the supervisor (paper-supervised, #499)

Options: inside the supervisor's loop (a dead supervisor tells nothing); a separate command run from outside. Chosen outside, since health is judged from outside by ruling. The name is the UTC hour, not the fault text, to avoid storms.

### 2026-11-16 — the Trading 212 client uses urllib (R-RUNNER-17, #495)

Options: `requests`; `urllib`. Chosen `urllib` because a new package is his call; Basic auth with key:secret. Public surface fixed to cash, holdings, fills; any other path is refused.

### 2026-11-16 — conformance step 5 compares IBKR's own stop fill (R-RUNNER-212, #512)

"Same bar" is the real stop fill's price, as intraday bars are not archived. A refused step fails the run (code 1) but later steps and the put-back still run.

### 2026-11-16 — FIRST-LIGHT is read from the end of the records (NS-10, #511)

Not from calendar dates, because `day._kept` guarantees one record per session in order; comparing with the venue calendar would duplicate that guarantee.

### 2026-11-16 — the bars question takes the contract as parameters (R-DATA-9, #509)

`listing` imports `paper`, so importing it back is a cycle and duplicating its lookup is a second path. Chosen: the caller passes the contract number and route.

### 2026-11-16 — the kill and halt line names when, not why (R-RUNNER-161, #502)

Halts are desk-wide. Options: add the reason (rejected: collides with the disagreement-alert test outside the claim); when only (taken).

### 2026-11-16 — backups go to two folders under PYTHON (DQ-05, DQ-09, #515)

"Off the PC": (a) a cloud or network target (credentials, his alone); (b) rely on his automated backup of the PYTHON folder, ruled on 14 November, with two copies in two folders. Chosen (b) on his "go with recommended". E: is never written.

### 2026-11-16 — go flat uses a halt, not the kill switch (R-RUNNER-162, #558)

Options: a new kill-like record (a new part on MONEY's path, forbidden by the request); the existing halt (sales still go, lift is his alone). Chosen the halt. While the kill switch is on, `book.send` refuses sales too, so go flat sells nothing; whether to change that is MONEY's.

### 2026-11-16 — conformance expects the gate's own refusal (R-RUNNER-92, #565)

The gate refuses SPY with its ISA words because that test precedes the retail one in `day._buy`. Options: require the retail wording (a change to `day.py`, outside the claim); accept the gate's refusal in whatever words. Chosen the latter.

### 2026-11-16 — the soak ledger is a new `soak.csv` (R-RUNNER-223, #572)

Options: reuse the per-run csv (no single place to read a day); a new file. Chosen the new file as the lighter. Refusals exit 0 and are logged.

### 2026-11-16 — the paper broker's stop mover is named `restop` (R-RUNNER-250, #584)

Options: `move_stop`; `restop`, matching the pretend broker already in flight (#579). Chosen `restop`. A same-level move sends nothing (`settle`'s existing keep rule). The Broker Protocol declares it (MONEY).

### 2026-11-16 — own orders are told from the account's by the broker's id (R-RUNNER-251, #599)

Options: by ref prefix; by client id (rejected, the held stops are the desk's client too). Chosen the id at the start; the rehearsal beside a held account is GO only if holdings and working orders are as found.

### 2026-11-17 — conformance restores its client for the run (R-RUNNER-256, #623)

The leak was fixed at the source with try/finally; `history.py` and `live.py` set the client the same way but run as their own processes, so the claim was left narrow (superseded by the Door, #651).

### 2026-11-17 — the pretend rests a stop when the real one rested (paper-conformance, #610)

Options: change `Pretend` for LSE lines; price the pretend side from the real result as #512 does. Chosen the latter, smaller and already the pattern.

### 2026-11-17 — R-RUNNER-257 stopped for a wider claim (#628)

Options: (a) land a `Door` beside the globals, deleting nothing; (b) stop and ask for the full claim. Chosen (b): the canon forbids a second path and growing code to work around a known fix. The Door design landed as #651.

### 2026-11-17 — restop is asked for every line of the desk (R-RUNNER-255, #645)

Not only the round's venue, since the book spans both; idempotent through the kept levels.

### 2026-11-17 — a lost stop is put back through `Paper.settle` (R-MONEY-30, #657)

Options: a new `Broker.restop` for no-stop lines; reuse `settle`. Chosen reuse: one path, no second door, rests first so never bare.

### 2026-11-17 — `gateway.known` keeps `ask` second (R-RUNNER-258, #651)

The request settled the design; the one choice was keeping the argument order because the messenger's test calls it that way.

### 2026-11-17 — a US line's contract request sends no primary exchange (R-RUNNER-278, #706)

Two exchange names are recorded for US lines (NASDAQ, ARCA). Options: send the first of the set (a guess) or leave it blank. Chosen blank.

### 2026-11-17 — the pound's disagreement is used and faulted, not refused (R-RUNNER-282, #716)

Options: refuse the step, or use IBKR's rate and record a fault. Chosen the latter: IBKR is primary by his ruling and refusing would stop trading on a bad free quote. The band is 2% (a pound moves under 1% a day). The record is a plain `pound.log` in the desk folder, as the claim allowed no other file.

### 2026-11-17 — an Alarm is not caught again in day.py (R-MONEY-36, #741)

Options: (a) catch Alarm in day.py and message separately, a second path for a job that has one (forbidden by the canon); (b) rely on `running.step`'s one failure path. Chose (b).

### 2026-11-17 — conformance's store home is optional for now (R-RUNNER-281, #738)

The claim excluded desk/conformance.py, so `home` defaults to None (archive). Options: required root (needs the file outside the claim); optional (chosen, lands green).

### 2026-11-17 — a failed pull is a receipt, the old code runs on (OPS-05, #752)

Options: (a) a failed pull ends the supervisor; (b) it is kept as a receipt of job "update" and the old code runs on. Chose (b): a dropped network must not stop the desk trading.

### 2026-11-17 — the soak moves into the tape; the tape's manifest row is not edited (R-RUNNER-285, #766)

Options: (a) edit the tape's manifest row to name the soak; (b) leave it, since a lane may only add rows (test_lanes), and the coordinator names the soak there. Chose (b).

### 2026-11-17 — conformance stop step judged on fills and holdings (R-RUNNER-308, #779)

Options: (a) the pretend broker says the same words as the real one; (b) compare fills and holdings. Chose (b): it is the card's own wording and the pretend broker has no cancel reasons. This reverses the 16 Nov rule that cancelled+filled meant sold by hand: the stop was the run's own swap (`_raised` rests the raised stop, then cancels the original under the same reference). The broker's words stay in the "it said" column; a sale not under the stop's name still differs and fails.

### 2026-11-17 — the lost-stop list is read from the day's list, in the evening message (R-RUNNER-291, #805)

Options: (a) widen the claim to change `running.recover`'s words (loosens a claim, more files; its report carries no order id or level); (b) read the day's list (`halt.morning`, entries written by `day._bare`), which already holds id, shares and level. Chose (b), smaller. Evening, not morning: the list is written when the day's record is made, after the close. `messenger.PUT_BACK` repeats `day._bare`'s "; put back " marker, a second home for that phrase; a later change could export it from `day.py`. A morning copy is a follow-up if he wants it.

### 2026-11-19 — a held line the round cannot judge: say the stop is not kept (R-RUNNER-312, #843)

Where the desk has no kept stop level for a held line, the message says "a level the desk has not kept". Options: omit the stop, or say so. Chose to say so, since silence is the fault being fixed.

### 2026-11-19 — an unfilled market buy: "at the market", withdrawn by the desk (R-RUNNER-326, #854)

Options: invent a limit price for the message, or say "at the market" (the desk sends no limit). Chose the truthful one. "Withdrawn" is judged by the cancel's answer being a real cancel state; a cancel refused because the broker had already ended the order counts as the broker's.

### 2026-11-19 — a market order waits 120 seconds, not 30 (R-RUNNER-339, #860)

Options: keep 30 s (three buys withdrawn on 19 Nov, none filled after the cancel); 120 s (chosen, recommended: inside a five-minute step, four times the old); 240 s (rides near the step's end with the cancel and reads after). Took the recommended, by his standing ruling of 13 Nov. `paper.FILL_SECONDS` = 120; tune from later tapes.

### 2026-11-19 — the order timing record is one long-form CSV (R-RUNNER-342, #862)

Options: one row per order, or one row per event (order_id, event, at, shares). Chose per event: fills repeat and an unaccepted order has no accepted time. Moments are the desk's clock when each message is read, since the gateway sends no status times of its own.

### 2026-11-19 — the evening stop sentence: pounds after costs (R-RUNNER-330, #874)

Options: show the result in the line's own currency, or in pounds after costs as the request said. Chose pounds after costs, priced by `book.round_trips` so the desk's one cost model is used; prices stay in the line's currency. The stop sentence comes before the unchanged "The desk's fills today" list, and appears only on a day with a stop fill.

### 2026-11-19 — a rehearsal fill is told from the real desk's by held line only (R-RUNNER-380, #909)

Options: match by the line the account held when the rehearsal began (chosen: `Apart` carries the symbol via `Holding.name`); or also check a Found order id in `desk/command.py` (out of claim, not done). So "an order it did not send itself" is not separately checked; a door with no `Apart` is unchanged.

### 2026-11-20 — R-RUNNER-348: ask for an order date field rather than parse the id again (#931, #933)

Options: (a) parse the id elsewhere in `desk/placing.py` (same defect, rejected); (b) wrap Order inside placing.py (a second path for a job that has one, refused by A2); (c) add a session-date field to Order and Sale in `desk/orders.py` and set it at every constructor, then read it in `Paper._cleared` (chosen, but another lane's files, so requested of MONEY as R-PAPER-35). Two sessions reached the same answer and changed nothing.

### 2026-11-20 — R-RUNNER-390: which gateway link news is Disconnected (#1024)

Options: (a) a wider list of kin of 2110 and 2157, including 1101 and 1102 (connectivity restored), at more risk of masking real faults; (b) 1100 (connectivity lost) with 2110 and 2157, listed once as `LINK` beside `FEEDS` in `desk/paper.py` (chosen, the narrow list). Other unknown news still raises a plain error.

### 2026-11-21 — R-RUNNER-410: placing reads `order.session` (#1264)

The field is named `session` (orders.py), not `day`. An unset session fails loudly (ValueError) rather than defaulting, as the request asked.

### 2026-11-21 — R-RUNNER-400: a separate stamp clock for order times (#1260)

Options: (a) pass a live clock to `Paper` (rejected: the rehearsal needs a fixed decision moment); (b) `placing.Paper` takes a separate stamp clock, real UTC by default, written to the millisecond (chosen). Old rows stay readable.

### 2026-11-21 — R-RUNNER-415: widen the rehearsal bar (#1280)

The card's "15:00 UTC passes" fits an order gate, but the send path (running/placing) is outside the claim. Options: (a) widen the rehearsal bar to New York pre-market (from 04:00 NY) and after-hours (to 20:00 NY) in `desk/trading_hours.py` (chosen, fits the claim; 15:00 UTC is barred, a market is open); (b) gate every real order by session (needs other files, left as a remaining item).

### 2026-11-21 — R-PAPER-28: no SMTP settings, no fallback (#1309)

Options: (a) refuse the step when no SMTP_ setting is set; (b) stay silent and run on Telegram alone (chosen: the desk works on Telegram alone, and a partly set group still fails loudly, by name).

### 2026-11-21 — R-RUNNER-253: rehearsal order ids not stamped (#1362)

Options: (a) mark the rehearsal's order ids with its run stamp (needs `desk/placing.py` and `desk/orders.py`, outside the claim; `strategy_of` parses the id); (b) leave the held-line separation as is (chosen: the stated test passes without it). (a) would still cover a collision on a line sold since, where there is no holding to match.

### 2026-11-21 — R-RUNNER-202: where the intraday round lives (#1371)

Options: (a) a new module (refused by the 100-file desk ceiling); (b) `desk/command.py` (wrong home); (c) `desk/running.py`, docstrings trimmed to 397 lines (chosen). Order id = day-rule-symbol-HHMM+side, so a bar's buy and sale differ and a bar seen twice sends nothing twice.

### 2026-11-21 — R-RUNNER-281: first buildable blocking request (#1393)

Took 281 first because 394 and 395 waited on R-RUNNER-391.

### 2026-11-21 — R-RUNNER-394: stops-not-recorded left to MONEY (#1403)

Options: (a) filter "-stop" ids in `cancel_all` (chosen, as request R-PAPER-37, since `desk/book_parts.py` is MONEY's); (b) wrap the broker in `recover` (rejected: a second path).

### 2026-11-21 — R-RUNNER-395: which lines are sent again (#1406)

Options: (a) filter in `day.trade`; (b) filter the lines handed to it (chosen: only lines whose cancels are on the desk's record, so a refused order is never sent again; no change to `day.trade`).

### 2026-11-21 — R-MONEY-54: cancel on any halt in force (#1414)

Options: (a) only the watch's halt (narrower, needs a second halt query); (b) any halt, his or the watch's (chosen: every halt means no buys, simpler).

### 2026-11-22 — morning heat shown only when recorded (#1478)

Options: say "not known" when the record holds no heat; omit the line (chosen: old records read as before). Report only.

### 2026-11-22 — compact message layout kept in messenger.py (#1482)

Options: a new `desk/layout.py` as the old pre-mortem said; in place (chosen: the 400-line cap it feared is now 800, and less code is progress).

### 2026-11-22 — the supervisor's overnight window: hours for the job, and a UTC restart window (#1631, #1639)

Options: (a) leave the step running round the clock and forgive bad receipts at night; (b) give each job hours and do not run it asleep (chosen in #1631: 05:30 to 22:00 UTC, one `awake` field; simpler, matches the runner's day, a night fault cannot wake him). For receipts, #1639 chose a UTC window 01:55-03:35 whose bad receipts do not count (covers 03:00 London in both seasons; it also forgives about an hour in winter, late or missing receipts still fault) over London time via zoneinfo (no time-zone data on this Windows Python, a dependency not worth it) and over leaving the false alarm nightly.

### 2026-11-22 — the streak is shown beside the verdict (#1636)

Options: a separate message (more lines; desk ceiling has 92 left) or the last-day lines carrying it (3 lines, chosen). The streak is the run of newest records whose verdict counts.

### 2026-11-22 — the streak's wording comes from Streak.says (#1665)

Options: keep the message's own 'streak N' (a second home for the count, failure pattern 8) or call `desk/streak.count` and use its words, "3 of 10 clean days in a row, since <day> did not count" (chosen).

### 2026-11-22 — the 05:40 card and 09:30 alarm need a wider claim (#1675)

`messenger.MORNING` start 05:40 / owed 09:30 turns messenger tests green but `desk/running.py` reads `MORNING.start` as "he is awake", so `tests/unit/test_running.py` and `tests/unit/test_command.py` ("he sleeps" at 07:55, 07:15) fail; reverted, nothing half-landed. Options: a separate start constant in messenger.py (more code; desk/ has 92 lines left) or change `MORNING` and move those tests' "he sleeps" moments before 05:40 (chosen, fewer lines). Claim for that card: desk/messenger.py, desk/running.py, tests/unit/test_messenger.py, tests/unit/test_running.py, tests/unit/test_command.py.

### 2026-11-22 — the pound is read from the price store alone (#1674)

(1) The day's recorded rate is no longer read first. Options: keep it first, or the store alone (chosen: his ruling "every price is read from the database alone"; the store gives the same rate per day). (2) A stale pound becomes a ValueError inside `rates`, because `command.NAMED` (outside the claim) does not name `keeper.Stale`. Options: widen NAMED, or translate in `rates` (chosen).

### 2026-11-22 — "the desk is not trading" means no fill today (#1753)

Options for "not trading" by 09:30 UK: no order sent; no fill; no step run. Chosen: no fill on the ledger dated today, because the ledger is the one record `desk/messenger.py` already reads, and an order that never fills is also not trading. Telegram only, once a day, never in his night (09:30 to 22:00). Remains: call `messenger.idle` from `desk/running.py` (outside the claim, R-PAPER-38).

### 2026-11-23 — the not-trading alarm is sent from `_say` (#1852)

Wired in `running._say`, the one place daily messages go, before the evening message, not a new door; `messenger.idle` already guards the hours and once-per-day. The rehearsal's message count rises 4 to 5 (it writes the alarm on a day with no fill).

### 2026-11-23 — only the 05:40 card moves earlier, not his waking hour (#1864)

MORNING starts 05:40 (the plan's time). Options: move the whole "awake" gate to 05:40, or only the card (chosen, so the account check, notes and weekly reminders never reach him before 08:00; `running.py` reads `gateway.WAKES`, not `MORNING.start`).

### 2026-11-23 — an unset email door is READY, not NOT READY (#1925)

The morning pre-flight line now carries "the email:" ("no SMTP_ setting, his phone alone" or "its settings are set"; a partial set is refused by name at start-up). Options: ready-with-note, or not-ready. Chose ready-with-note: the phone is a working door and email is only the fallback, so a desk without SMTP is not blocked from trading.

### 2026-11-23 — the evening week is the last 7 days; missed winners left out (#1940)

The weekly cost beside net profit reads the records of the last 7 calendar days. Options: Monday-to-Sunday, or last 7 days. Chose last 7 days: the message goes daily and needs no calendar edge. Missed winners are not shown: no record on main holds a signal the desk would have won on and did not take, and a faked one would break canon A5; R-PAPER-41 asks MONEY for the record.


### 2026-11-23 — the real side is right on the VHYG buy; the pretend side is asked to follow (#2026)

R-RUNNER-449 from the tapes: the 1-share VHYG market buy (plain DAY MKT) at 08:37 sat unfilled 120 s and was cancelled with 0 filled (trades-london-20261123-0835.csv); at 09:06 the same buy filled within a second at 77.90 (-0906.csv); 19 Nov alike (08:10, 08:35 unfilled, 09:36 filled). Options: (a) lengthen the real wait (rejected: no fill ever came after a cancel); (b) change the real order (rejected: the same order fills at 09:06); (c) leave the real side, ask the pretend broker's owner to leave such a buy unfilled before the hour IBKR fills (chosen, nothing hidden). Only a comment in `desk/paper.py` changed. The hour of first fill (between 08:37 and 09:06) is unmeasured; R-RUNNER-399's one-share probe at 08:45/09:00 would pin it. Request: R-MONEY-72.

### 2026-11-23 — London's round starts at 09:00; the busy-hours window stays (#2068)

London's orders filled 31 of 31 only from 09:00 UK. One number, `conformance_tape.STARTS`, now says when each round begins and `running._pending` reads it. Options: also move `ROUNDS` (the hours history and conformance keep out of) to 09:00-09:30, or leave it at 08:00-08:30. Chose to leave it: moving it breaks `tests/unit/test_history.py`, outside the claim, and conformance only stays quiet a little longer. Remains: move it with that test.

### 2026-11-23 — an intraday order is due in its own bar's session (#2075)

All 143 intraday orders since 10:43 were refused: `desk/placing.py` sent only an order dated the session before today's, the daily rule. Options: (a) a due-session field on Order and Sale (`desk/orders.py`, MONEY's, outside the claim); (b) read the intraday id's -HHMM suffix (a fact read from a name, forbidden by A2 and B3); (c) the broker built for a bar's round treats orders as due in the session they are dated (`placing.Paper(..., within=True)`). Chose (c): one rule in placing, set by the round's kind and not by the zoo, inside the claim. (a) is the real fix and is asked of MONEY as R-PAPER-42. The money path is held for a fresh A6 blind review.

### 2026-11-23 — Windows boot task: ONSTART plus hourly `tell`, started in the code folder (#2102, #2110)

`python -m desk.supervisor install ROOT` makes KestrelSupervisor (ONSTART, `run`) and KestrelTell (hourly; `tell` dedups per UTC hour); run again it replaces them. Options: ONLOGON (rejected, not at boot); a task file (rejected, more code). His yes: "Yes, add it" (Sun 22 Nov). #2110 fixed that each command ran with no working folder (a Windows task starts in System32: "No module named desk"); each now runs `cmd /c cd /d <code folder> && python -m desk.supervisor ...`. Remains: he runs the install once as administrator; not ticked.

### 2026-11-23 — the paper-watcher hold: the blocking card's own deletion taken (#2109)

Options: wait, or delete. Chose delete (his "always go with recommended"): `day_gap`, `_result`, `Gap` in `desk/reports.py` had no caller (49 lines, R-RUNNER-478). #2107 still needs 75+ more lines of room; that is a separate card for runner ops.


### 2026-11-24 — the day's rate is read in running.py, kept once (#2166)

Desk.rates answers a day's rates from their first record in rates.csv when the day has them, else fetches; a later step's different rate neither errors nor overwrites. Options: reader in `desk/book_parts.py` (refused by the lane wall), or in `desk/running.py` as the request wrote it. Chose running.py. Latent, non-blocking: a day kept with one currency never fetches the other (no writer makes a partial day).

### 2026-11-24 — the conformance share is found beside the desk's root (#2178)

The day check finds the conformance ledger as root.parent/"conformance", only for the desk's own door (222). Options: every caller passes the folder (outside the claim), or derive it in `desk/clearance.py`. Chose derive, so no caller changes. Order filter: only a client-223 SELL stop no bigger than the ledger share is left out, the narrowest rule; any other 223 order is still named.

### 2026-11-27 — the intraday round shares the desk's order cap (#2195)
Options: a new constant for the intraday round, or reuse `day._send`'s round cap and `paper.MAX_ORDERS`. Chose reuse: one number, one home. A new order is one the broker has no report for; orders it already holds use no slot. Blind review made the cap per step, not per venue.

### 2026-11-27 — carried orders go through the existing round-again path (#2200)
Options: a new send path for the morning's CARRIED list, or let `running._again` also take those ids. Chose the latter: one code path; the "orders <venue> again" note stops a second send.

### 2026-11-27 — the refused line stays the conformance reference line (#2209)
Options: keep the refused line (a US line, sends nothing) as reference, or find a non-retail London line. None exists, and the line only labels a step that sends nothing, so kept; `_barred` now judges the run's own market only.

### 2026-11-27 — an ISIN line is asked of the broker with an empty security type (#2264)
Options: always an empty type, or only when the line has an ISIN. Chose the latter so lines without an ISIN keep STK; no symbol special case. Not yet seen against the real gateway.

### 2026-11-27 — conformance sizes at the lower of close and latest price (#2251)
Options: pass `market` to size(), which would refuse the buy (emergency rule) instead of resting the stop under the market, or size at min(close, latest 5-minute close). Chose the latter; a store with no bar of today leaves the close standing.

### 2026-11-27 — the Gateway-down time is kept in a file at the data root (#2347)
Options: derive it from notes, or change the step's return. Chose a small mark file (first moment found down, cleared when the Gateway answers): the smallest change, touching only claimed files.

### 2026-11-28 — conformance settles its own earlier orders, refusing if one will not end (#2369)
Options: ignore a leftover order of client 223 and send, or refuse the run. Chose refuse, per B1 and "fail loudly"; settle reads the account the run already reads once, so no extra gateway read. A desk order (client 222) is never touched.

### 2026-11-28 — conformance mirrors the desk on a gap through the stop (#2381)
Options: keep a private lower-of price rule (the duplicate the audit named) or pass the close and today's last five-minute bar to `orders.size`. Chose the desk's: a gap through the signal's stop makes the plan refuse by the desk's own emergency rule.

### 2026-11-28 — the watcher reads the supervisor's lock, not its receipts (#2434)
Options: keep the lock design (the system's word, independent of the supervisor's own files) or judge by receipts (the supervisor's own health already does that). Lock chosen, since the point is independence; the test takes the box's check name though. His standing ruling: "please always go with recommended".

### 2026-11-28 — paper-side-stops ticked on its gate (coordinator 311)
Options: keep the box open until the paper door also has per-side set, move and cancel, or tick it on its gate. Its gate is a gateway tape with two stops on one ticker where the zoo's is cancelled and the desk's still rests. `test_two_stops_on_one_ticker_rest_apart_by_side` passes on main (#2476, #2477). Ticked, because the door now reads each side's stops by its own client id (desk 222, zoo 223), and the interface's per-side cancel landed in money-side-stops (#2479, `cancel_stop(symbol, zoo=)`). Left open, the box was never handed out (the runner calls it met) and never ticked, and PAPER idled with nothing it could start. Per-side counts and holders stay in zoo-own-side.

### 2026-11-28 — the rehearsal's shut-market wait is 3 s (#2469, #2489)
Options: a longer job timeout or skipping the send (both rejected by the card); give the wait to the rehearsal account's door (one send path, one home per wait), chosen. Seconds: 5 s overran, since a whole Friday of 313 orders cost about 10-11 s each; 2 s feared a slow gateway handshake failing before any send; 3 s chosen, the same as the handshake wait, so no lower. The step loop stops at 3300 s (300 s of margin to the runner's 3600 s kill), cancels its own and names the stop. Live doors keep 120 s. His standing ruling: "please always go with recommended".

### 2026-11-28 — a side is the placing client id (#2476)
Options: the order ref prefix (a hand list, pattern 18) or the client id (desk 222, the zoo's 223), the only thing the gateway tells apart. Client id chosen. His 13 Nov: "always go with recommended".

### 2026-11-28 — recovery takes its collect as a required argument (#2498)
Options: a default collect for `recover` (a caller could forget it and a gapped stop would not halt buying) or a required argument handed by the caller. Required chosen, so every ledger read goes through the one `running._collect`, which records the day's rates and then calls `book.collect` with the lines, the settings and a tell. paper-watcher, held back for lack of `desk/` room, is runner ops' claim gap: a deletion card of 100+ desk/ lines, taken on his "always go with recommended".
