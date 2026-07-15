# The Edge-Evidence Playbook (free edition)

How to know whether your prediction-market strategy is real, before it costs
you money. This is the methodology PMQS's `validate.evaluate()` gate encodes.

## The uncomfortable premise

Almost every retail "profitable bot" claim dies under one of six questions:

1. **Did you pay fees?** The standard taker curve peaks at 1.75c per contract
   at 50c. A strategy trading near the middle of the book pays the venue
   relentlessly. PMQS charges conservative cent-ceiling fees per fill.
2. **Did you cross the spread?** You do not trade at mid. If your backtest
   fills at mid, every trade starts with a phantom half-spread profit.
   PMQS fills are taker-only against displayed liquidity.
3. **Did you wait for your own latency?** A signal computed on a book you can
   no longer trade against is a story, not a fill. PMQS executes orders
   against the book that exists *after* your configured latency.
4. **Could you actually get that size?** Displayed size includes quotes that
   cancel faster than you arrive. PMQS applies a size haircut (default: half).
5. **Are your samples independent?** Twenty fills in one market are one bet,
   not twenty. PMQS aggregates PnL per settled market and bootstraps over
   markets.
6. **Did you beat the close, or just the scoreboard?** Winning bets at prices
   worse than the closing line is what luck looks like. Positive closing-line
   value (CLV) is what information looks like.

## The gate

A strategy is a **candidate** edge only when all four hold simultaneously:

| Requirement | Why |
|---|---|
| ≥ 30 settled markets | Below this, confidence intervals are decorative. |
| Post-fee PnL > 0 | Obvious, and still routinely faked via fee omission. |
| Bootstrap 95% CI lower bound > 0 (per-market means) | A positive average that could plausibly be zero is not evidence. |
| Mean CLV > 0 | You were early to information, not lucky at settlement. |

FAIL is the default and the normal outcome. Most strategies, honestly
measured, lose to fees and spread — knowing that *before* deploying capital
is the entire value of a backtest.

## What passing the gate does NOT mean

- It does not mean the edge persists out of sample.
- It does not survive regime change, venue rule changes, or fee changes.
- It does not size your positions (that is a separate risk problem).
- It is a *promotion to paper trading*, not to capital.

## Recommended workflow

1. Capture your own data (`pmqs.capture`), continuously, before you need it.
2. Prove your pipeline on the synthetic fixture (`--fixture`) — zero network.
3. Replay your strategy with honest latency and haircut settings.
4. Read the gate's reasons. Fix the *measurement* before touching the model.
5. Only after a PASS: paper trade live, and require the paper results to pass
   the same gate again on fresh markets.

The paid PMQS Pro materials go deeper: leakage taxonomies, settlement-source
reconciliation, stress-testing fills at +1c/+2c adverse execution, walk-forward
protocol design, and worked examples of strategies dying honorably at each
stage. The gate above, though, is complete and free — there is no secret
stricter version. Rigor is not the upsell; depth is.
