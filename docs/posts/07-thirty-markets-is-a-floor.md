# Thirty Settled Markets Is a Floor: Sample Size for Event-Contract Strategies

"My bot is up 40% this month" is the most common sentence in prediction-market
Discord servers, and it is almost always statistically meaningless. Not wrong,
necessarily — meaningless, in the precise sense that the same result is
comfortably consistent with a losing strategy on a lucky run.

## The unit of evidence is the settled market

Start here, because it changes every count that follows: **fills are not
observations.** Every fill in one market resolves with that market's single
settlement. Buy YES five times in a market that settles NO and you have one
piece of evidence, sized into five pieces. Count fills as independent and
your effective sample inflates by the average fills-per-market — and your
confidence interval shrinks by its square root, purely as an artifact.

So: not "400 trades." Ask "how many settled markets?"

## What small samples can and can't say

The per-market PnL of a typical event-contract strategy has a standard
deviation on the order of the stake — outcomes are near-binary. A rough 95%
CI on mean per-market PnL is `±2σ/√n`:

| Settled markets | CI half-width (in units of per-market σ) |
|---|---|
| 10 | ±0.63σ |
| 30 | ±0.37σ |
| 100 | ±0.20σ |
| 300 | ±0.12σ |

If your true edge is 0.1σ per market — a *good* edge in this business — you
need on the order of **hundreds** of settled markets before the CI reliably
excludes zero. At 10 markets, a true-zero strategy shows a "40% month" about
as often as a real one does.

This is exactly the shape of a real verdict from our own research: an MLB
strategy with positive mean EV whose 95% CI on EV-per-contract came out at
**(−0.045, +0.180)**. Positive mean, zero inside the interval. The honest
reading — "consistent with an edge, equally consistent with nothing" — held
it at paper stage. The exciting reading would have funded it.

## Why 30 is a floor and not a target

The [PMQS](https://github.com/jhunter11/pmqs) edge gate requires ≥30 settled
markets before it will even *evaluate* the other conditions. Thirty is not
where evidence becomes strong — it's roughly where a bootstrap CI stops being
decorative. Below it, resampling 10 numbers ten thousand times mostly
rearranges your luck.

The gate's other conditions do the real work (CI lower bound above zero,
positive CLV — see post #5), but they need a floor to stand on. Treat 30 as
"minimum to be discussable" and 100+ as "minimum to be confident," and
remember both counts reset whenever you change the strategy — evidence
gathered under the old parameters belongs to the old strategy. Test twenty
variants against the same 30 markets and keep the best, and you've just
moved the overfitting one level up; the count that matters is per *decision*,
not per backtest run.

## The practical playbook

1. Capture continuously, starting now — settled markets accrue in calendar
   time and you cannot backfill what you didn't record (venue data terms
   restrict redistribution, so vendor archives won't save you either).
2. Prefer strategy families that touch many independent markets (40 weather
   stations settle daily) over ones that touch three per week.
3. Cluster everything by market. Per-fill statistics are how you lie to
   yourself politely.
4. Pre-register your floor and refuse to peek early. The gate exists so this
   isn't a matter of discipline: `pmqs.validate.evaluate(min_settled=30)` is
   the default, and FAIL is the default verdict until the evidence earns
   otherwise.
