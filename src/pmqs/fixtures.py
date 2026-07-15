"""Deterministic synthetic market generator.

Produces JSONL event streams for tests, demos, and CI without touching any
venue API. The generated books random-walk a latent probability, quote a
configurable spread around it, and settle each market by drawing the outcome
from its *final* latent probability -- so no strategy can have a real edge on
this data by construction. That makes it the correct substrate for proving
the plumbing and the *negative* path of the edge gate.

Synthetic data proves your pipeline. It can never prove an edge.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterator

from pmqs.orderbook import BookLevel, Event, OrderbookSnapshot, SettlementEvent


@dataclass(frozen=True)
class FixtureConfig:
    n_markets: int = 40
    snapshots_per_market: int = 60
    step_ms: int = 10_000
    start_ts_ms: int = 1_750_000_000_000
    spread_cents: int = 2
    depth_levels: int = 3
    level_quantity: int = 200
    walk_step: float = 0.02
    seed: int = 7


def generate_events(config: FixtureConfig = FixtureConfig()) -> Iterator[Event]:
    """Yield a time-ordered interleaved stream of book and settlement events."""
    rng = random.Random(config.seed)
    probabilities = {
        f"SYNTH-M{i:03d}": rng.uniform(0.15, 0.85) for i in range(config.n_markets)
    }
    events: list[Event] = []

    for market, prob in probabilities.items():
        # Stagger market start times so the stream interleaves.
        offset = rng.randrange(0, config.step_ms)
        ts = config.start_ts_ms + offset
        current = prob
        for _ in range(config.snapshots_per_market):
            current = min(0.95, max(0.05, current + rng.uniform(-1, 1) * config.walk_step))
            mid_cents = round(current * 100)
            half = max(1, config.spread_cents // 2)
            best_bid = max(1, min(99, mid_cents - half))
            best_ask = max(best_bid + 1, min(99, mid_cents + half))

            yes_bids = []
            no_bids = []
            for level in range(config.depth_levels):
                bid_price = best_bid - level
                ask_price = best_ask + level
                quantity = config.level_quantity + rng.randrange(0, 100)
                if bid_price >= 1:
                    yes_bids.append(BookLevel(bid_price, quantity))
                if 1 <= 100 - ask_price <= 99:
                    no_bids.append(BookLevel(100 - ask_price, quantity))
            no_bids.sort(key=lambda lvl: lvl.price_cents, reverse=True)

            events.append(
                OrderbookSnapshot(
                    ts_ms=ts,
                    market=market,
                    yes_bids=tuple(yes_bids),
                    no_bids=tuple(no_bids),
                )
            )
            ts += config.step_ms

        result = "yes" if rng.random() < current else "no"
        events.append(SettlementEvent(ts_ms=ts, market=market, result=result))

    events.sort(key=lambda e: e.ts_ms)
    yield from events


def write_fixture(path: str, config: FixtureConfig = FixtureConfig()) -> int:
    """Write a JSONL fixture file; returns the number of events written."""
    count = 0
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        for event in generate_events(config):
            handle.write(event.to_json() + "\n")
            count += 1
    return count
