# Check the assumptions behind a backtest

A replay can produce an attractive result with inputs that were unavailable at the decision time or prices that could not support the order. PMQS includes checks for several of these errors. It still depends on the researcher to supply appropriate data and strategy code.

## Prices and size

A midpoint is a reference price, not an executable quote. A marketable purchase crosses to the ask; a sale crosses to the bid. PMQS derives those sides from binary bid ladders and walks the displayed levels under a configured size haircut.

The haircut is an assumption about available liquidity. It does not measure queue position or predict which quotes survive until an order arrives. Compare results under several plausible settings and report partial fills and unfilled orders.

## Time

The replayer calls the strategy on the current snapshot. It queues the returned orders and processes them on a later snapshot after the configured delay. It rejects an order whose timestamp differs from the decision snapshot.

This sequence removes same-snapshot fills from that path. It does not stop a strategy from consulting a file that contains future outcomes. It also cannot establish that a source timestamp means observation time rather than publication, receipt, or processing time.

## Accounting and selection

Charge fees using the configured schedule and rounding rule for each fill. Reconcile positions and settlement cash by market. Keep open positions separate from settled results.

Repeated fills in one market share settlement risk. PMQS therefore resamples market-level PnL for its bootstrap interval. Related markets can remain dependent, and selecting a strategy on the same sample can bias the reported interval.

Keep a record of each tested variant and freeze the final configuration before evaluating it on later data. The [playbook](../validation-playbook.md) describes the default screen and its limits.
