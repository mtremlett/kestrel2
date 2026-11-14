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
