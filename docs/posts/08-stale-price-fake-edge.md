# How a Stale Price Field Manufactured a Fake +$101 Edge

This is a post-mortem from our own research. We're publishing it because the
bug class it describes is, in our experience, the single most common source
of "profitable" prediction-market strategies — more common than overfitting,
more common than fee omission — and because it fooled us too.

## The setup

Short-horizon BTC bracket markets settle on an average of the index over the
final window. Near expiry, that average is largely pinned by where spot
already is, so a convergence model repricing the market against live spot
should be able to flag books that haven't caught up. We built the model,
verified its math against Monte Carlo, and pointed a gap recorder at live
markets: log the model's fair value, the venue's price, and the difference.

The recorder started printing edge. Over a session it accumulated roughly
**+$101 of apparent edge**. The model looked wonderful.

## The bug

The spot input feeding the model wasn't live spot. It was a **candle-close
field** — a value that updates when the bar completes, standing in for a
value that moves continuously.

Walk through what that does. BTC moves. The venue's market makers reprice
immediately. Our model, still holding the last candle close, computes fair
value from where spot *was* — and scores the difference as the venue being
wrong. The faster the market moved, the bigger and more frequent the
"mispricings." The bug generated apparent profit *proportional to
volatility*, which is precisely the signature a real convergence edge would
have. It even back-checked plausibly: volatile sessions "earned" more.

Nothing crashed. Nothing looked wrong. Every individual number was a real
number from a real feed. The system was simply answering a different
question than the one we thought we were asking: not "is the venue slow?"
but "has BTC moved since the last candle closed?" — a question whose answer
is reliably yes and reliably worthless.

## The fix, and the rule it became

The immediate fix was mechanical: use the real-time feed, and — more
importantly — **carry the input's age on every observation** (`spot_age_sec`
on each row), refuse to compute gaps on stale inputs, and tag every recorded
observation with the exact basis it was computed against, so no later
analysis could silently rest on an unexamined input.

The rule it became is worth stealing verbatim: **apparent edges are
first-guess measurement defects.** Guilty until proven innocent. In three
separate strategy families, the largest "edges" we ever measured were all
data bugs first — stale inputs, basis mismatches between the signal's index
and the settlement's index, timestamps mixing exchange time with local time.

## How to catch it before it catches you

- **Ask every input its age.** If an observation doesn't carry a source
  timestamp, you don't know what time it's from — you're hoping.
- **Scan for the frozen-then-jump signature.** A feed that repeats an
  identical value for many observations and then jumps is stale until proven
  otherwise. It's a fingerprint, and it's mechanically detectable.
- **Watch markout.** If the market systematically moves *away* from your
  fills right after you trade (ours would have), you're trading on old
  information — the market is telling you, at retail prices.
- **Distrust edges that scale with volatility** until you can explain
  exactly why they should.

The free [PMQS](https://github.com/jhunter11/pmqs) core enforces time-order
on event streams and measures markout on every backtest; the Pro layer ships
the frozen-then-jump capture auditor and settlement reconciliation built from
this incident, plus the full case study (including the latency benchmark
that eventually put the strategy in observe-only mode: model compute was
~0.6µs, the network round trip ~34ms — the market always moved last).

The meta-lesson costs nothing and is worth the most: **the more exciting the
number, the more likely it's a measurement defect. Audit first. Believe
later.**
