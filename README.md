# PMQS — Prediction Market Quant Stack

[![CI](https://github.com/jhunter11/pmqs/actions/workflows/ci.yml/badge.svg)](https://github.com/jhunter11/pmqs/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Dependencies](https://img.shields.io/badge/dependencies-zero-brightgreen)

**Execution-aware backtesting, paper trading, and honest edge validation for Kalshi and other prediction markets.**

Most prediction-market backtests are fiction. They fill at mid with no latency, ignore fees, resample correlated fills as if they were independent, and quietly peek at the future. Then the bot goes live and the "edge" evaporates into spread and fees.

PMQS is the opposite bet: a small, zero-dependency Python core that makes the dishonest shortcuts *structurally impossible*, plus an edge-evidence gate that tells you **"keep researching"** unless your strategy survives standards a real quant desk would recognize.

```
verdict         : FAIL
  - post-fee PnL is not positive ($-37.23)
  - bootstrap CI lower bound not positive (-2.4622)
  - mean CLV not positive (-3.2222c): fills do not beat the close
```

That's PMQS's built-in demo strategy failing its own gate — on purpose. If a tool never says no, it isn't validation.

## What's inside

| Module | What it does |
|---|---|
| `pmqs.orderbook` | Kalshi-native book model: two bid ladders (YES/NO), asks *derived* — a NO bid at p is a YES ask at 100−p. Crossed books and out-of-order streams are rejected, not silently accepted. |
| `pmqs.fees` | Fee math with configurable per-series rates, maker fraction, and two rounding modes (conservative cent-ceiling default; $0.0001 fill precision mode). |
| `pmqs.fills` | Conservative taker-only paper fills: cross the spread, size haircut on displayed liquidity, no price improvement, ever. |
| `pmqs.replay` | Event replayer with enforced latency — orders execute against the book *after* your configured delay, never the book the signal saw. Backdated orders raise `lookahead` errors. |
| `pmqs.ledger` | Position/cash ledger with settlement handling; per-market realized PnL (the correct unit of statistical evidence). |
| `pmqs.markout` | Markout at horizons and closing-line value: did the market move with you, and did you beat the close? |
| `pmqs.validate` | **The edge-evidence gate**: ≥30 settled markets, positive post-fee PnL, bootstrap CI lower bound > 0 (clustered by market, not fills), positive mean CLV. All four, or the verdict is FAIL with reasons. |
| `pmqs.capture` | Bring-your-own-key Kalshi REST capture to JSONL, plus a `--fixture` mode that proves the whole pipeline with zero network. |
| `pmqs.fixtures` | Deterministic synthetic market generator for tests and CI. |

## Quickstart (60 seconds, no API key)

```bash
pip install -e .
python examples/run_fixture_backtest.py     # full pipeline, no network
python -m pytest -q                          # 52 tests
```

Capture real data with your own Kalshi API key (your data, your agreement):

```bash
pip install -e ".[capture]"
python -m pmqs.capture --out my_capture.jsonl \
  --tickers KXHIGHNY-26JUL16-B85 --key-id YOUR_KEY_ID --private-key path/to/key.pem
```

Then replay your own strategy against your own capture:

```python
from decimal import Decimal
from pmqs import ConservativeFillModel, FeeSchedule, Replayer, read_events

fill_model = ConservativeFillModel(
    fee_schedule=FeeSchedule(),
    latency_ms=500,               # be honest about your loop speed
    size_haircut=Decimal("0.5"),  # assume half the displayed size is real
)
with open("my_capture.jsonl", encoding="utf-8") as f:
    result = Replayer(fill_model=fill_model).run(read_events(f), MyStrategy())
print(result.summary())
```

## What PMQS will never do

- **No signals, no picks, no "profitable strategies included."** The bundled strategy is deliberately edge-free and exists to demonstrate the gate rejecting it.
- **No performance claims.** We publish our validation standards, not fantasy returns.
- **No bundled market data.** Venue data terms restrict redistribution; you capture your own history under your own API agreement.
- **No live order placement.** PMQS is research infrastructure. What you do with your own execution stack is your business — after your strategy passes the gate, and even then the gate only means "candidate," not "guaranteed."

## Why the gate is strict

A green PnL number is the *weakest* form of evidence. Fills inside one market are correlated, so PMQS bootstraps over settled markets, not fills. Beating the scoreboard once can be luck; systematically beating the closing line is much harder to fake. Fees and spread are charged at conservative rounding. Thirty settled markets is a floor, not a target. The default answer to "is this an edge?" is **no** — the gate exists to make a "yes" mean something.

Full methodology: [docs/validation-playbook.md](docs/validation-playbook.md).

## Fee accuracy note

Rates and per-series multipliers change. `FeeSchedule` defaults to the widely published 7% taker curve with maker fees at 25% of taker, and everything is configurable (`series_taker_rates={"KXBTC": Decimal("0.10")}`). Always verify against the venue's current official fee schedule before trusting cost-sensitive results.

## Learn the method

The reasoning behind every design choice here is written up as a short field
guide in [docs/posts/](docs/posts/) — why backtests lie, the exact fee math,
orderbook semantics, closing-line value, sample-size floors, and a real
post-mortem of a stale feed manufacturing a fake edge. Start with
[Why your Kalshi bot's backtest is lying to you](docs/posts/01-why-your-backtest-is-lying.md).

## PMQS Pro

The free core is complete and MIT-licensed — it is not a demo. **PMQS Pro**
is the paid layer for people going deeper:

- **Adverse-execution stress kit** — re-run any backtest at +1c/+2c worse fills, fee bumps, latency multiples; an edge you'd fund must survive the whole grid
- **Walk-forward protocol tools** — market-level folds, embargo, pooled out-of-sample gating
- **WebSocket capture** with sequence-checked book-delta reconstruction
- **Settlement reconciliation + capture audits** (the stale-feed detector)
- **Strategy scaffold pack** — weather / crypto / sports wiring, correct plumbing, zero alpha
- **The validation course** — 8 hands-on modules graded by a real pytest harness
- **"Death of an edge" case studies** — three real strategies and the validation stage that killed each one

Same rules as the core: no signals, no picks, no income claims.
**Availability:** listing link coming with the first release — watch this repo.

## Roadmap

- Multi-venue adapters (Polymarket order books)
- Maker-fill modeling with explicit queue-position assumptions (documented as optimistic)
- Builder-code execution examples (disclosed, removable) once developer terms are reviewed

## Disclaimers

PMQS is educational and research software. It is not investment advice, not a solicitation to trade, and offers no warranty of fitness for trading. Event contracts involve risk of total loss of the amount at risk. Nothing here claims or implies a profitable trading strategy. Comply with your venue's terms of service, developer agreement, and data terms; you are responsible for your own trading, taxes, and legal obligations.

## License

MIT. See [LICENSE](LICENSE).
