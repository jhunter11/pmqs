# Research validation playbook

PMQS tests defined assumptions about a replay. Its evidence gate combines sample count, results after fees, a bootstrap interval, and closing-line value. Each check has limits that the researcher must assess for the data and strategy.

## Check the replay inputs

Verify the fee schedule for the period covered by the capture. The library's default rates are model settings; they do not establish a venue's current fees. Use executable bid or ask prices and keep spread costs separate from fees.

Set execution delay and a displayed-size haircut before evaluating a strategy. The replayer processes a pending order against a later snapshot once its delay has elapsed. That model does not reproduce cancellations, queue position, or every live execution condition.

Check timestamp definitions, source age, event order, and settlement identifiers. A correctly ordered stream can still contain stale values. Strategy code can also read external information that the replay engine does not control.

## Read the gate

The default configuration requires all four conditions:

| Check | Scope |
| --- | --- |
| At least 30 settled markets | A configurable screening floor, without a power guarantee |
| Positive total PnL after fees | Accounting over the included markets |
| Positive lower bootstrap confidence bound | Resampled mean PnL per market |
| Positive mean closing-line value | Fill prices compared with the last usable supplied midpoints |

The bootstrap uses markets as its sampling unit. Shared events, overlapping contracts, and time trends can still make those units dependent. The implementation does not correct for repeated strategy selection or searching many parameter settings.

Closing-line value excludes fees and depends on the quality of the reference quotes. A positive value can support further investigation, but it cannot prove an information advantage or future profit.

## Preserve a separate evaluation set

Run the synthetic fixture first to check installation and accounting. Record the strategy version, data hash, parameters, and execution assumptions for each later run.

Use development data to change the strategy, then evaluate the frozen version on later markets. Report failed variants and missing observations. If the strategy passes this screen, collect fresh paper results and check the same assumptions again. The gate provides no authorization to place live orders.

The [method notes](posts/README.md) explain the individual checks and the included fixture result. Private companion materials are outside this release.
