# The included threshold strategy fails the fixture gate

The September 8, 2026 run used `examples/run_fixture_backtest.py` without parameter changes. It completed successfully and returned an evidence verdict of `FAIL`.

The fixture uses 40 markets, 60 snapshots per market, and seed 7. The strategy threshold is 35 cents, with a requested quantity of 20 YES contracts. The fill model applies 500 milliseconds of delay, a 50 percent liquidity haircut, and the default fees.

| Measurement | Recorded result |
| --- | ---: |
| Fills | 18 |
| Unfilled orders | 0 |
| Orders cancelled at settlement | 0 |
| Fees | $4.83 |
| Settled markets | 40 |
| PnL after fees | -$37.23 |
| Mean PnL per market | -$0.9308 |
| Bootstrap 95 percent interval for that mean | [-$2.4622, $0.8115] |
| Mean closing-line value | -3.2222 cents |
| Mean markout | -0.3889 cents |

The sample exceeds the default 30-market floor. It fails the other three checks: total PnL is negative, the lower confidence bound is negative, and mean closing-line value is negative.

These results describe this strategy and synthetic sample. They do not show that every threshold strategy must lose. The fixture also does not rule out every possible signal. This example has not established a profitable strategy.

Run `python -X utf8 examples/run_fixture_backtest.py` from the repository root to reproduce the report. Changes to the fixture, strategy, fees, or rounding can change the output, so preserve the source revision with any comparison.
