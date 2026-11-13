# Architecture

The machine-readable version is `manifest.toml`, and a guard enforces it: a module not
listed there cannot exist. This file explains the shape in words.

## Two packages, one wall

    desk/   the trading core. Data in, decisions out, orders through one broker door.
            Imports the standard library and nothing else. May never import lab/.

    lab/    research and the ladder. Judges strategies using the core's own code.
            May import desk/, and must.

**Why the wall.** A verdict reached by a second implementation of a strategy is a verdict
about that second implementation. The predecessor's simulator ran different code from the
desk it was certifying, so its results said nothing about what would actually trade.

**Why only the standard library in the core.** Not purity — reach. The predecessor's
daily run could pull in 352,000 lines, which meant a change anywhere could break trading.
Every third-party package in the core is a line in `manifest.toml` and needs the
operator's approval on the pull request.

## Inside the core: pure middle, adapters at the edge

Everything that decides is data in, data out: given these bars and this book, buy this
many shares with a stop there. It touches no network, no file and no clock, which is why
it can be tested exhaustively in seconds.

Everything that touches the world sits behind a thin adapter with no logic in it: the
broker, the price archive, the clock, the messenger. Each has exactly one implementation
for real use and one pretend version for tests, and the pretend one is a fake of the
*adapter*, never of the code being tested.

## One owner per concept

One price store with one writer. One instrument master. One capital number. One cost
model. One book, built from what the broker reports and never from what the desk meant to
buy. One messenger with a delivery record.

When something needs a second reader, it does not get one: the question goes to the
single owner. Two paths to one answer will disagree, and then both are published.

## What is deliberately absent

No plugin system, no configuration framework, no abstraction with fewer than three real
callers, no option for a case not required today, no compatibility shim. Each of those
was present in the predecessor and each one earned its place by seeming harmless.

## The module list

`manifest.toml` — every module, the one thing it owns, and what it may import. Register
the module there, then write the file. The guard refuses the file otherwise, which is the
point: it forces the question "who already owns this?" before the answer is a new file.
