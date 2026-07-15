"""Conservative paper-fill simulation.

The single biggest source of fantasy PnL in prediction-market backtests is
the fill assumption. This model is deliberately pessimistic:

- Orders are *taker only*: they cross the spread against displayed liquidity.
  If you want maker fills in a backtest you must prove queue position, which
  captured snapshots cannot do honestly.
- Only a configurable fraction of displayed size (``size_haircut``) is
  assumed to be really available to you.
- Orders execute against the book that exists *after* ``latency_ms`` has
  passed since the decision (the replayer enforces this), not the book the
  signal was computed on.
- No price improvement, ever.

If the strategy still clears the edge gate under these assumptions, the
result is worth a second look. If it only works with optimistic fills, it
does not work.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from pmqs.fees import FeeSchedule
from pmqs.orderbook import BookLevel, OrderbookSnapshot


@dataclass(frozen=True)
class Order:
    ts_ms: int  # decision time
    market: str
    side: str  # "yes" | "no"
    action: str  # "buy" | "sell"
    quantity: int

    def __post_init__(self) -> None:
        if self.side not in ("yes", "no"):
            raise ValueError("side must be 'yes' or 'no'")
        if self.action not in ("buy", "sell"):
            raise ValueError("action must be 'buy' or 'sell'")
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")


@dataclass(frozen=True)
class Fill:
    ts_ms: int  # execution time (book time), not decision time
    market: str
    side: str
    action: str
    quantity: int  # contracts actually filled (may be < order quantity)
    vwap_cents: Decimal
    fee: Decimal  # Decimal dollars
    levels: tuple[tuple[int, int], ...]  # (price_cents, qty) actually consumed

    @property
    def notional(self) -> Decimal:
        """Cash value of the fill excluding fees, in Decimal dollars."""
        return (self.vwap_cents / Decimal(100)) * Decimal(self.quantity)


@dataclass(frozen=True)
class ConservativeFillModel:
    fee_schedule: FeeSchedule
    latency_ms: int = 500
    size_haircut: Decimal = Decimal("0.5")
    max_levels: int = 5

    def __post_init__(self) -> None:
        if self.latency_ms < 0:
            raise ValueError("latency_ms must be non-negative")
        if not Decimal(0) < self.size_haircut <= Decimal(1):
            raise ValueError("size_haircut must be in (0, 1]")
        if self.max_levels < 1:
            raise ValueError("max_levels must be >= 1")

    def _ladder(self, order: Order, book: OrderbookSnapshot) -> tuple[BookLevel, ...]:
        """The ladder a taker order consumes, best price first."""
        if order.action == "buy":
            return book.yes_asks() if order.side == "yes" else book.no_asks()
        return book.yes_bids if order.side == "yes" else book.no_bids

    def execute(self, order: Order, book: OrderbookSnapshot) -> Fill | None:
        """Fill ``order`` against ``book``; returns None when nothing fills."""
        if book.market != order.market:
            raise ValueError(
                f"order market {order.market!r} does not match book {book.market!r}"
            )

        remaining = order.quantity
        consumed: list[tuple[int, int]] = []
        for level in self._ladder(order, book)[: self.max_levels]:
            if remaining <= 0:
                break
            available = int(Decimal(level.quantity) * self.size_haircut)
            if available <= 0:
                continue
            take = min(remaining, available)
            consumed.append((level.price_cents, take))
            remaining -= take

        if not consumed:
            return None

        filled = sum(q for _, q in consumed)
        weighted = sum(Decimal(p) * q for p, q in consumed)
        vwap = weighted / Decimal(filled)

        fee = Decimal("0.00")
        for price_cents, qty in consumed:
            fee += self.fee_schedule.fill_fee(
                contracts=qty,
                price_cents=price_cents,
                market=order.market,
                liquidity="taker",
            )

        return Fill(
            ts_ms=book.ts_ms,
            market=order.market,
            side=order.side,
            action=order.action,
            quantity=filled,
            vwap_cents=vwap,
            fee=fee,
            levels=tuple(consumed),
        )
