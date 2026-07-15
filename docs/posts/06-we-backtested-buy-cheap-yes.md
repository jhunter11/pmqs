# We Backtested "Buy Cheap YES" So You Don't Have To

There's a strategy every prediction-market beginner invents in their first
week. It goes: *cheap contracts are cheap for a reason, but sometimes the
crowd overreacts — buy YES under 30c and let the longshots pay for
themselves.*

It feels like a strategy. It has a threshold, a thesis, a vibe of
contrarianism. So we wired it up exactly as a beginner would — buy 10
contracts of YES whenever the ask is at or below 30c, one position per
market — and ran it through a full honest pipeline: taker-only fills against
displayed liquidity with a 50% size haircut, 500ms decision-to-execution
latency, conservative per-fill fees, settlement handling, and the
edge-evidence gate on top.

## The result

```
fills           : 18
unfilled orders : 2
cancelled       : 1 (market settled first)
fees paid       : $1.35
markout mean    : -0.1046c
settled markets : 40
post-fee PnL    : $-37.23
mean/mkt PnL    : $-0.9307 [-2.4622, 0.4907] (bootstrap 95%)
CLV mean        : -3.2222c over 18 fills
verdict         : FAIL
  - post-fee PnL is not positive ($-37.23)
  - bootstrap CI lower bound not positive (-2.4622)
  - mean CLV not positive (-3.2222c): fills do not beat the close
```

Dead. Three separate ways.

## The three autopsy findings

**Negative CLV (−3.2c/fill) is the interesting one.** "Cheap" wasn't a
mispricing — it was the market's honest opinion, and after we bought, the
close moved *away* from us by 3 cents on average. A cheap ask is not
information about the market; it IS the market. Buying it is buying the
consensus at the consensus price, minus costs.

**The costs did the rest.** Every entry crossed the spread as a taker and
paid the fee curve. A strategy with zero information content doesn't grind to
zero — it grinds to *minus costs*, reliably.

**The CI tells you what you actually learned.** Mean per-market PnL of
−$0.93 with a 95% interval of [−2.46, +0.49]: the data can't even rule out
that the strategy is fine! That's the honest resolution of a 40-market
sample — wide enough to be humbling in both directions. (Which is why the
gate also has a sample floor; see post #7.)

## Why we ship this as the demo

This exact run is [PMQS](https://github.com/jhunter11/pmqs)'s bundled demo —
`python examples/run_fixture_backtest.py`, zero network, ~1 second. The
strategy is deliberately edge-free and the data is synthetic (outcomes drawn
from the same process that generates prices, so no edge is even possible).

We could have shipped a demo that passes. It would have been easy — loosen
the fills, drop the fees, resample per-fill instead of per-market. Every one
of those changes is a bug someone somewhere is currently calling a feature
of their backtesting product.

A validation tool's demo should demonstrate *validation*. Ours rejects its
own strategy and explains why, because that's the product: a gate whose
FAIL means something so that its PASS means something. When your real
strategy — on your real captured data — clears it under conservative
execution assumptions, that's the moment worth paying attention to.

And if you want to know what it looks like when real strategies with real
research behind them meet this standard: two of the three died too (nine
seasons of negative CLV in one case; a confidence interval straddling zero
in the other). Those post-mortems are in the PMQS Pro case-study pack. The
free gate, though, is the same gate. There is no stricter secret version —
rigor isn't the upsell.
