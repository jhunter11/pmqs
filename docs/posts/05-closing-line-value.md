# Interpreting closing-line value

Closing-line value compares a fill price with a later reference midpoint. PMQS uses the last supplied snapshot with a defined midpoint for that market. The researcher must ensure that the supplied series covers the intended closing period.

For a purchase, the calculation is reference midpoint minus fill VWAP. For a sale, the sign reverses. NO-side fills use the complementary midpoint, `100 - YES midpoint`. Positive values therefore indicate movement in the fill's direction, measured in cents per contract.

## What the reference can miss

A last quote can be stale, thin, or far from settlement. Its midpoint may not support an executable trade. A market can also move for reasons unrelated to the strategy's signal.

The calculation excludes fees and does not measure realized profit. Positive closing-line value alone cannot establish an information advantage. Negative closing-line value identifies a pattern to investigate, without proving that every profitable settlement was luck.

PMQS averages the available values by fill. It does not weight that mean by contract count or market. A market with many fills can therefore contribute more observations than another market. Review coverage and concentration alongside the mean.

## Compare fixed horizons

`markout()` uses the first usable snapshot at or after the fill time plus a chosen horizon. It returns no result when the supplied series has no usable later quote. The report should retain the requested horizon, actual quote delay, and missing-value count.

Fixed horizons can distinguish an immediate execution problem from later price movement. They still depend on capture quality and do not prove causation. Evaluate several horizons chosen before inspecting the strategy's results.

The evidence gate requires a positive mean closing-line value as one screening condition. Read it with results after fees, market-level uncertainty, and fresh evaluation data.
