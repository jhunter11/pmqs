# Kalshi Fees, Explained Precisely

Most fee explanations you'll find are either vague ("about 1%") or wrong
("7% of your stake"). The math is simple, but the details — the parabola, the
rounding direction, the per-series exceptions — decide whether small edges
live or die. Here it is precisely, with the caveats labeled.

*(Verify everything below against the venue's current official fee schedule
before relying on it. Rates and per-series multipliers change; this post
describes the widely published structure as of mid-2026.)*

## The formula

```
taker fee = rate × contracts × P × (1 − P)
```

where `P` is the contract price in dollars and `rate` is 0.07 for most
series. Maker fees, where charged, are a fraction of the taker fee
(currently published at 25%). Note what this is **not**: it is not a
percentage of your stake. It's a parabola in price:

| Price | Fee per contract | As % of stake |
|---|---|---|
| 5c | 0.3325c | 6.7% |
| 10c | 0.63c | 6.3% |
| 30c | 1.47c | 4.9% |
| **50c** | **1.75c (peak)** | **3.5%** |
| 70c | 1.47c | 2.1% |
| 90c | 0.63c | 0.7% |
| 95c | 0.3325c | 0.35% |

Two non-obvious consequences:

1. **Mid-book strategies pay the most.** If your signal lives in the 40–60c
   zone (most "uncertain outcome" strategies do), you're paying peak fees on
   every fill.
2. **As a fraction of capital at risk, cheap contracts are expensive.** The
   fee on a 5c contract is 6.7% of your stake. "Buy cheap longshots" starts
   nearly 7% underwater.

## The rounding

Classically published behavior: each fill's fee is rounded **up to the next
cent**. This punishes small fills disproportionately — one contract at 50c
carries a theoretical fee of 1.75c, rounded up to **2c**, a 14% surcharge for
trading small.

The venue's modern (2026) documented mechanics are finer-grained: the trade
fee is computed to $0.0001 precision, and a separate balance-precision
rounding fee with a **rebate accumulator** issues whole-cent rebates when
accumulated overpayment exceeds a cent, persisting across the fills of an
order. Net of rebates, the modern mechanism converges near fair value.

For backtesting, this creates a choice, and the honest answer is to be
conservative: charge the classic cent-ceiling per fill. A strategy that
survives the harsher rounding cannot be undone by the gentler one. That's
the default in [pmqs.fees](https://github.com/jhunter11/pmqs); the $0.0001
mode is available when you want the tighter estimate.

## Per-series exceptions

Some market categories have carried different multipliers over time. Don't
hardcode 0.07 — parameterize it. In PMQS:

```python
from decimal import Decimal
from pmqs import FeeSchedule

fees = FeeSchedule(series_taker_rates={"KXBTC": Decimal("0.10")})
fees.fill_fee(contracts=100, price_cents=50, market="KXBTC-26JUL15-B")
# charged at the override rate; longest matching ticker prefix wins
```

## What fees mean for your strategy

The break-even win probability for buying YES at price `P` (in dollars) is:

```
P + rate × P × (1 − P)
```

At 50c that's **0.5175** — you need to be right 51.75% of the time just to
tread water, before spread. Add a 2-cent spread crossed on entry and you're
at ~53.75% on a coin-flip-priced contract. This is the entire reason most
naive strategies lose slowly rather than win slowly: the market doesn't have
to beat them; the cost structure does.

A backtest that omits any of this is measuring a different (better) game
than the one you'll play. [PMQS](https://github.com/jhunter11/pmqs) charges
these fees per fill, at conservative rounding, by default — which is one of
several reasons its verdicts run less flattering, and more useful, than most.
