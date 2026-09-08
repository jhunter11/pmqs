# Sample size and dependence

PMQS defaults to a minimum of 30 settled markets for its evidence gate. This is a configurable screening rule. It is not a statistical guarantee, and passing it does not establish that a sample can detect the effect being studied.

The implementation can calculate its bootstrap interval with at least two market results. A sample below the configured floor still fails the gate even when those other calculations are available.

## Choose the sampling unit

Fills in the same market share a settlement outcome and may share the same signal. Treating each fill as an independent experiment can understate uncertainty. PMQS aggregates PnL by settled market and resamples those market results.

Market-level resampling still assumes that the sampled units adequately represent the target population. Contracts tied to one event, overlapping horizons, and repeated observations during one regime can violate that assumption. Group or block related observations when the research design requires it; the current gate does not choose those groups automatically.

## Plan around a useful effect

Before collecting an evaluation sample, define the smallest effect that would justify further work. Estimate variability from separate development data and account for clustering and repeated comparisons. Use those assumptions to plan sample size or a stopping rule.

There is no universal market count that makes an edge reliable. More data can narrow sampling uncertainty while preserving a biased capture, an optimistic fill model, or selection on the same outcomes.

Keep the final evaluation period separate from strategy development. Report the number of markets, their relationships, the confidence method, and all strategy variants considered. The default bootstrap interval does not correct for an unreported search across many models.
