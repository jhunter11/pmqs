# PMQS: Prediction Market Quant Stack

[![CI](https://github.com/jhunter11/pmqs/actions/workflows/ci.yml/badge.svg)](https://github.com/jhunter11/pmqs/actions/workflows/ci.yml)

A Python library for prediction-market replay, paper fills, and strategy evidence checks.
The core uses the standard library and targets Python 3.10 or later.

PMQS models execution delay, spread, fees, and displayed liquidity. It rejects defined input errors, including backdated orders and crossed books.
These checks address specific failure modes. They cannot certify arbitrary data or strategy code against every form of leakage.

## Run the fixture

```bash
python explore.py
```

The menu explains the evidence gate and runs synthetic examples without credentials or network access.
To install the package and run the backtest directly:

```bash
python -m pip install -e ".[dev]"
python examples/run_fixture_backtest.py
python -m pytest -q
```

The built-in strategy fails the evidence gate. That is the expected fixture result.

## Modules

| Module | Behavior |
| --- | --- |
| `pmqs.orderbook` | YES and NO bid ladders, derived asks, and stream validation |
| `pmqs.fees` | Configurable fee rates and rounding rules |
| `pmqs.fills` | Taker paper fills with spread crossing and a liquidity haircut |
| `pmqs.replay` | Delayed execution against a later book snapshot |
| `pmqs.ledger` | Cash, positions, settlement, and realized results by market |
| `pmqs.markout` | Price movement after fills and closing-line value |
| `pmqs.validate` | Minimum sample, profit, confidence-interval, and closing-line checks |
| `pmqs.capture` | REST capture to JSONL and a fixture mode |
| `pmqs.fixtures` | Deterministic synthetic events |

## Evidence gate

The default gate requires all four conditions:

1. At least 30 settled markets.
2. Positive results after fees.
3. A positive lower bootstrap confidence bound, with resampling by market.
4. Positive mean closing-line value.

Markets form the resampling unit because fills within a market can share outcomes.
Dependence across markets and selection bias still require separate analysis.
Passing the gate marks a research candidate. It does not establish a durable or executable edge.

## Use your own capture

The optional capture dependency supports signing read requests with your own credentials.
Use data that you have permission to collect and retain. Keep keys outside the repository.

```bash
python -m pip install -e ".[capture]"
python -m pmqs.capture --help
```

Fee schedules and venue behavior can change. Configure them for the period represented by your data.
PMQS does not place live orders and does not include a profitable strategy.

## Documentation

- [Research playbook](docs/validation-playbook.md)
- [Contributing](CONTRIBUTING.md)
- [Security](SECURITY.md)

The playbook and dated posts describe research methods and earlier project plans.
Private companion projects are outside this release.

## License

MIT. See [LICENSE](LICENSE).
