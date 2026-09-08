# Run a synthetic replay

The included fixture creates market snapshots and settlements from a fixed random seed. It exercises replay, fees, fills, and the evidence report without credentials or network access.

From the repository root, run:

```bash
python -m pip install -e ".[dev]"
python examples/run_fixture_backtest.py
python -m pytest -q
```

On a Windows terminal that cannot print the report's Unicode characters, use `python -X utf8 examples/run_fixture_backtest.py`.

## What the example configures

The script uses 40 markets, 60 snapshots per market, and seed 7. Its threshold strategy buys up to 20 YES contracts when the configured 35-cent threshold permits an order. The fill model uses a 500-millisecond delay, a 50 percent displayed-size haircut, and the default fee schedule.

The strategy has no demonstrated predictive signal. Its purpose is to exercise the accounting path and produce an expected failure under this fixture. Different generated samples or parameters can produce different numerical results.

## Inspect the output

The report includes fill counts, unfilled and cancelled orders, fees, markout, settled-market PnL, a bootstrap interval, and closing-line value. The [recorded run](06-we-backtested-buy-cheap-yes.md) gives the September 8, 2026 result for this configuration.

A successful process exit means the example ran. It does not mean the strategy passed its evidence gate. Read the verdict and each reason separately.

Change one input at a time when checking a replay assumption. Keep the seed and configuration with the result so another reader can reproduce the comparison. For actual capture, use the separate optional capture module and review data permissions and credential handling first.
