# Reading a binary order book

PMQS represents a binary market with two bid ladders. Each ladder contains prices in cents and available contract counts. Both ladders list the highest bid first.

```json
{"orderbook": {"yes": [[48, 120], [47, 300]], "no": [[50, 90], [49, 250]]}}
```

A NO bid at price `p` implies a YES ask at `100 - p` under the complementary one-dollar payoff model. In this example, the best YES bid is 48 cents and the derived YES ask is 50 cents. A NO bid of 49 cents produces a YES ask of 51 cents.

## Preserve the side and order

Do not read the NO ladder as a list of YES asks at unchanged prices. The equality at 50 cents is a special case. At other prices, it conceals a side-conversion error.

Derived asks need ascending prices, with the cheapest first. The source bid ladders use descending prices. Tests should include unequal prices and several levels so that an incorrect conversion or sort order becomes visible.

```python
from pmqs import OrderbookSnapshot, BookLevel

book = OrderbookSnapshot(
    ts_ms=1_720_000_000_000,
    market="SYNTHETIC-EXAMPLE",
    yes_bids=(BookLevel(48, 120), BookLevel(47, 300)),
    no_bids=(BookLevel(50, 90), BookLevel(49, 250)),
)
assert book.best_yes_ask() == 50
assert book.spread_cents() == 2
```

## Investigate invalid captures

The snapshot validator rejects crossed books, duplicate price levels, and incorrectly sorted ladders. The stream validator checks event order. A failure can indicate mixed timestamps, a capture error, or an adapter that misunderstood the feed.

Keep the rejected input and investigate its cause before using it in a replay. These checks do not prove that a valid-looking book was fresh or executable. A feed adapter also needs tests against the source format it actually receives.
