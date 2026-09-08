# Stale price inputs can create an apparent model gap

A historical project note described roughly $101 of apparent model-versus-market gap. Its recorder used a candle-close field as a live spot input. This public release excludes the underlying capture and calculation. The number records an earlier measurement error, without a reproduced profit result.

The general failure is straightforward. A completed candle retains its closing value while the current market price changes. A model using that field can compare an old state with a newer quote and attribute the difference to market mispricing.

## Record the time basis

Store the source timestamp, receipt timestamp, and processing timestamp separately. Record whether a value represents a trade, quote, index calculation, or completed bar. Include the input's age at each decision.

Set freshness limits before evaluating the strategy. Preserve rejected observations and their reasons so that an analysis can count missing coverage. A filter that removes inconvenient outcomes after inspection can introduce a different bias.

Repeated values followed by jumps can reveal a feed that updates less often than expected. That pattern is a prompt to inspect the source semantics. An unchanged price can also be valid. Confirm the update schedule and compare an independent timestamped reference where available.

## Separate validation layers

PMQS checks ordering in validated event streams and calculates price movement after fills. Event order alone does not establish freshness. Markout can identify adverse movement. It cannot determine whether stale input, execution cost, or a weak signal caused that movement.

Audit source age, instrument identity, settlement basis, and clock alignment before treating a model gap as a research candidate. Then evaluate executable prices, fees, available size, and later outcomes. The public core does not provide the private capture audit or reproduce the historical recorder incident.
