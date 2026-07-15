"""Event replay engine: the honest alternative to vectorized backtests.

Events stream through in time order. Strategies see one snapshot at a time
and can only place orders; orders wait out the configured latency and then
execute against the *next* book that arrives at or after
``decision_ts + latency_ms`` -- never the book the signal was computed on.
Pending orders die when their market settles first.

This structure makes the two classic backtest lies structurally impossible:
lookahead (nothing downstream of the current event exists yet) and
zero-latency fills (you always pay the book as it will be, not as it was).
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Iterable

from pmqs.fills import ConservativeFillModel, Fill, Order
from pmqs.ledger import Ledger
from pmqs.markout import collect_clv, collect_markouts
from pmqs.orderbook import Event, OrderbookSnapshot, SettlementEvent
from pmqs.strategy import Strategy
from pmqs.validate import EdgeEvidenceReport, evaluate


@dataclass(frozen=True)
class BacktestResult:
    ledger: Ledger
    fills: tuple[Fill, ...]
    unfilled_orders: int
    cancelled_orders: int
    report: EdgeEvidenceReport
    markout_mean_cents: Decimal | None

    def summary(self) -> str:
        lines = [
            f"fills           : {len(self.fills)}",
            f"unfilled orders : {self.unfilled_orders}",
            f"cancelled       : {self.cancelled_orders} (market settled first)",
            f"fees paid       : ${self.ledger.total_fees()}",
            (
                f"markout mean    : {self.markout_mean_cents}c"
                if self.markout_mean_cents is not None
                else "markout mean    : n/a"
            ),
            self.report.summary(),
        ]
        return "\n".join(lines)


@dataclass
class _PendingOrder:
    order: Order
    execute_at_ms: int


@dataclass
class Replayer:
    fill_model: ConservativeFillModel
    markout_horizon_ms: int = 60_000
    min_settled: int = 30
    ledger: Ledger = field(default_factory=Ledger)

    def run(self, events: Iterable[Event], strategy: Strategy) -> BacktestResult:
        pending: dict[str, deque[_PendingOrder]] = defaultdict(deque)
        snapshots_by_market: dict[str, list[OrderbookSnapshot]] = defaultdict(list)
        unfilled = 0
        cancelled = 0

        for event in events:
            if isinstance(event, SettlementEvent):
                cancelled += len(pending.pop(event.market, ()))
                self.ledger.settle(event.market, event.result)
                continue

            assert isinstance(event, OrderbookSnapshot)
            snapshots_by_market[event.market].append(event)

            # 1) Execute matured pending orders against THIS book.
            queue = pending[event.market]
            while queue and queue[0].execute_at_ms <= event.ts_ms:
                item = queue.popleft()
                fill = self.fill_model.execute(item.order, event)
                if fill is None:
                    unfilled += 1
                else:
                    self.ledger.record_fill(fill)

            # 2) Then let the strategy react to it.
            for order in strategy.on_snapshot(event, self.ledger):
                if order.ts_ms != event.ts_ms:
                    raise ValueError(
                        "orders must carry the current snapshot ts_ms; "
                        "backdated or future-dated orders are lookahead"
                    )
                queue.append(
                    _PendingOrder(
                        order=order,
                        execute_at_ms=event.ts_ms + self.fill_model.latency_ms,
                    )
                )

        # Orders still pending at end of data never happened.
        unfilled += sum(len(q) for q in pending.values())

        fills = tuple(self.ledger.fills)
        markouts = collect_markouts(fills, snapshots_by_market, self.markout_horizon_ms)
        markout_mean = None
        if markouts:
            total = sum((m.edge_cents for m in markouts), Decimal("0"))
            markout_mean = (total / Decimal(len(markouts))).quantize(Decimal("0.0001"))

        report = evaluate(
            self.ledger.per_market_pnl(settled_only=True),
            collect_clv(fills, snapshots_by_market),
            min_settled=self.min_settled,
        )
        return BacktestResult(
            ledger=self.ledger,
            fills=fills,
            unfilled_orders=unfilled,
            cancelled_orders=cancelled,
            report=report,
            markout_mean_cents=markout_mean,
        )
