# How to Paper Trade Kalshi Strategies with Zero Network Access

Before your pipeline ever touches a venue API, it should prove itself on data
you fully control. Not because synthetic data can validate a strategy — it
can't, and anyone who says otherwise is selling something — but because it
validates the *pipeline*: parsing, replay, fills, fees, settlement, and the
statistics on top. Pipeline bugs are far more common than edges, and far
cheaper to find offline.

## Step 0: install (60 seconds)

```bash
git clone https://github.com/jhunter11/pmqs && cd pmqs
pip install -e .
```

Zero runtime dependencies. Python 3.10+.

## Step 1: generate a synthetic market

```bash
python -m pmqs.capture --fixture --out fixture.jsonl
# wrote 2440 synthetic events to fixture.jsonl (no network used)
```

This writes a deterministic stream of orderbook snapshots and settlements for
40 markets. The generator random-walks a latent probability, quotes a spread
around it, and settles each market by drawing from its final latent
probability. Read that twice: **outcomes are drawn from the same process
that generates the prices.** No strategy can have a real edge on this data,
by construction. That's a feature — it makes the fixture the perfect
substrate for testing whether your *negative* path works. A validation stack
that can't fail an edgeless strategy on edgeless data is broken.

## Step 2: write a strategy against the replay interface

```python
from dataclasses import dataclass
from pmqs import Order, OrderbookSnapshot

@dataclass
class MyStrategy:
    def on_snapshot(self, snapshot: OrderbookSnapshot, ctx) -> list[Order]:
        best_ask = snapshot.best_yes_ask()
        if best_ask is not None and best_ask <= 30:
            return [Order(ts_ms=snapshot.ts_ms, market=snapshot.market,
                          side="yes", action="buy", quantity=10)]
        return []
```

The contract is deliberately narrow: you see one snapshot at a time and your
own positions (`ctx.position(market)`), and you emit orders stamped with the
current snapshot's timestamp. That narrowness is the honesty: there is no
dataframe of the future to accidentally peek into. Backdated orders raise.

## Step 3: replay with honest execution settings

```python
from decimal import Decimal
from pmqs import ConservativeFillModel, FeeSchedule, Replayer, read_events

fill_model = ConservativeFillModel(
    fee_schedule=FeeSchedule(),
    latency_ms=500,                # your real loop speed, measured not hoped
    size_haircut=Decimal("0.5"),   # half the displayed size is really yours
)
with open("fixture.jsonl", encoding="utf-8") as f:
    result = Replayer(fill_model=fill_model).run(read_events(f), MyStrategy())
print(result.summary())
```

Orders wait out your latency and fill against the book that exists *then* —
taker-only, walking the derived ask ladder, paying conservative fees per
level consumed. Markets that settle first cancel your pending orders, the way
reality does.

## Step 4: read the gate, not the PnL

```
settled markets : 40
post-fee PnL    : $-37.23
verdict         : FAIL
  - post-fee PnL is not positive ($-37.23)
  - bootstrap CI lower bound not positive (-2.4622)
  - mean CLV not positive (-3.2222c): fills do not beat the close
```

FAIL, with reasons, on edgeless data — the correct answer, delivered by every
part of the pipeline working together. Now, and only now, are you entitled to
point the same unchanged code at data you captured from the real venue with
your own API key (`pip install -e ".[capture]"`), because you know the
plumbing tells the truth.

The whole loop — fixture, replay, gate — is
[examples/run_fixture_backtest.py](../../examples/run_fixture_backtest.py)
in the PMQS repo. Runs in about a second. Costs nothing to find out your
pipeline is broken, and slightly more than everything to find out live.
