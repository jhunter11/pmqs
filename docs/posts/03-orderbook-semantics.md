# A NO Bid at 50c Is a YES Ask at 50c: Kalshi Orderbook Semantics for Developers

The single most common *silent* bug in prediction-market tooling isn't in the
strategy. It's in reading the book.

## The book is two bid ladders

A Kalshi-style binary market does not publish bids and asks the way an equity
feed does. It publishes **two arrays of bids**:

```json
{"orderbook": {"yes": [[48, 120], [47, 300]], "no": [[50, 90], [49, 250]]}}
```

- `yes`: bids to buy YES, price in cents, best (highest) is the top of ladder
- `no`: bids to buy NO — **also bids**, on the other side of the same coin

There are no ask arrays. Asks are *implied*: because YES and NO sum to $1 at
settlement, **a resting NO bid at price p is exactly a YES ask at 100 − p**.
Someone bidding 50c for NO is offering to take the other side of your YES
purchase at 50c. Mechanically: you "buy YES at the 50c ask" by matching
against their NO bid at 50.

```
NO bids:   50c ×  90   →  YES asks:  50c ×  90
           49c × 250   →             51c × 250
YES bids:  48c × 120                 (and symmetrically, YES bids are NO asks)
```

## The bugs this causes

**Sign confusion.** Treating the `no` array as "asks at those prices" gives
you a YES ask of 50c when the real implied ask might be 50c only by
coincidence — at any other price the book you compute is nonsense, and your
backtest happily trades against phantom liquidity.

**Sorting confusion.** Both arrays are bid ladders (best = highest price),
but the *derived* ask ladder sorts the other way (best = lowest). If you
derive asks and forget to re-sort, your fill simulator walks the ladder from
the worst price first — a pessimism bug that kills real edges. (The opposite
sort bug is an optimism bug that funds fake ones. We've seen both, including
in our own earlier tooling — book ordering and delta handling were a flagged
defect class in a system we later rebuilt from spec.)

**Crossed-book acceptance.** If best YES bid + best NO bid > 100, both sides
could be lifted for riskless profit — real venues match that away before
publishing. If your capture ever shows it, something upstream is broken
(feed reordering, a stitching bug, mixed timestamps). Code that silently
accepts crossed books converts feed bugs into "arbitrage edges."

## What defensive code looks like

Store exactly what the venue publishes (two bid ladders) and *derive*
everything else, validating on construction:

```python
from pmqs import OrderbookSnapshot, BookLevel

book = OrderbookSnapshot(
    ts_ms=1_720_000_000_000,
    market="KXHIGHNY-26JUL16-B85",
    yes_bids=(BookLevel(48, 120), BookLevel(47, 300)),
    no_bids=(BookLevel(50, 90), BookLevel(49, 250)),
)
book.best_yes_ask()   # 50 — derived from the NO bid at 50
book.spread_cents()   # 2
book.yes_asks()       # sorted best-first, ascending price
```

Crossed books raise. Mis-sorted ladders raise. Duplicate price levels raise.
Out-of-time-order event streams raise. None of these are recoverable
conditions in research data — every one of them means your capture, not your
strategy, needs attention first.

That model (with the replayer and fee math built on top of it) is the free,
MIT-licensed core of [PMQS](https://github.com/jhunter11/pmqs). If you're
building your own stack instead, at minimum: derive asks, re-sort them,
reject crossed books, and enforce time order. Those four lines of paranoia
are cheaper than one fake edge.
