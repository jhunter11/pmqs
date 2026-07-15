"""Strategy interface and a deliberately edge-free example scaffold."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from pmqs.fills import Order
from pmqs.orderbook import OrderbookSnapshot


class StrategyContext(Protocol):
    """What a strategy is allowed to see at decision time.

    Only the current snapshot and its own positions -- by construction there
    is no access to future events, which is the point of replaying instead of
    vectorizing over a full dataframe where lookahead bugs hide.
    """

    def position(self, market: str) -> tuple[int, int]:
        """(yes_contracts, no_contracts) currently held in ``market``."""
        ...


class Strategy(Protocol):
    def on_snapshot(
        self, snapshot: OrderbookSnapshot, ctx: StrategyContext
    ) -> list[Order]: ...


@dataclass
class ThresholdScaffold:
    """Buy YES when the best YES ask is at or below a threshold.

    THIS IS A SCAFFOLD, NOT AN EDGE. "Cheap YES" is not information; this
    exists so you can watch a naive rule get correctly rejected by the edge
    gate, and to show where a real signal plugs in.
    """

    threshold_cents: int = 30
    quantity: int = 10
    max_positions: int = 1

    def on_snapshot(
        self, snapshot: OrderbookSnapshot, ctx: StrategyContext
    ) -> list[Order]:
        yes_held, _ = ctx.position(snapshot.market)
        if yes_held >= self.quantity * self.max_positions:
            return []
        best_ask = snapshot.best_yes_ask()
        if best_ask is None or best_ask > self.threshold_cents:
            return []
        return [
            Order(
                ts_ms=snapshot.ts_ms,
                market=snapshot.market,
                side="yes",
                action="buy",
                quantity=self.quantity,
            )
        ]
