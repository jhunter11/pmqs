# Fee arithmetic in PMQS

PMQS implements a configurable binary-contract fee curve. This note describes the library defaults and rounding behavior. It does not verify a venue's current fee schedule.

For `n` contracts at price `P` dollars, the unrounded fee is:

```text
fee = rate * n * P * (1 - P)
```

`FeeSchedule` defaults to a taker rate of `0.07`. It can apply a maker fraction, ticker-prefix overrides, and a selected rounding rule. These values must match the market and historical period being studied.

## Rounding changes small fills

At a 50-cent price, one contract produces an unrounded fee of $0.0175 under the default taker rate. The default cent ceiling rounds that fill to $0.02. A single fill of 100 contracts produces a $1.75 fee.

Those examples explain why multiplying a rounded one-contract fee by total volume can give the wrong answer. Fees are computed per fill. Splitting the same volume into smaller fills can increase the total under a ceiling rule.

The optional `TENTH_MILL_CEIL` setting rounds to $0.0001. The implementation does not maintain a separate accumulated rebate balance. Use a rounding mode only when it represents the accounting assumptions for the study.

## Check units at the call site

Prices enter `FeeSchedule.fill_fee()` as integer cents. The method returns a dollar amount and uses decimal arithmetic. Contract counts must be positive, prices must fall between 1 and 99 cents, and the liquidity argument must name a supported side.

For a purchase held to a one-dollar settlement, a break-even estimate includes the purchase price and the fee per contract. If the purchase price is already the ask, adding a half-spread again would count that entry cost twice. A later exit introduces another execution price and potentially another fee.

See [the implementation](../../src/pmqs/fees.py) and its tests before adding a schedule. Keep the raw rate, rounding mode, and fill grouping in the experiment record.
