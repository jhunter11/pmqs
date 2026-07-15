from decimal import Decimal

import pytest

from pmqs.fees import FeeSchedule
from pmqs.fills import ConservativeFillModel, Order
from pmqs.fixtures import FixtureConfig, generate_events
from pmqs.orderbook import BookLevel, OrderbookSnapshot, SettlementEvent
from pmqs.replay import Replayer
from pmqs.strategy import ThresholdScaffold


def make_model(latency_ms: int = 500) -> ConservativeFillModel:
    return ConservativeFillModel(
        fee_schedule=FeeSchedule(), latency_ms=latency_ms, size_haircut=Decimal("0.5")
    )


def snapshot(ts_ms: int, ask: int, market: str = "A") -> OrderbookSnapshot:
    return OrderbookSnapshot(
        ts_ms=ts_ms,
        market=market,
        yes_bids=(BookLevel(max(1, ask - 2), 100),),
        no_bids=(BookLevel(100 - ask, 100),),
    )


class BuyOnce:
    def __init__(self) -> None:
        self.done = False

    def on_snapshot(self, snap: OrderbookSnapshot, ctx) -> list[Order]:
        if self.done:
            return []
        self.done = True
        return [Order(ts_ms=snap.ts_ms, market=snap.market, side="yes", action="buy", quantity=10)]


def test_latency_fills_against_later_book() -> None:
    events = [snapshot(0, ask=30), snapshot(1000, ask=40)]
    result = Replayer(fill_model=make_model(latency_ms=500), min_settled=1).run(
        iter(events), BuyOnce()
    )
    assert len(result.fills) == 1
    # Decision saw ask=30, but 500ms later the only available book quotes 40.
    assert result.fills[0].vwap_cents == Decimal("40")
    assert result.fills[0].ts_ms == 1000


def test_settlement_cancels_pending_orders() -> None:
    events = [
        snapshot(0, ask=30),
        SettlementEvent(ts_ms=200, market="A", result="yes"),
    ]
    result = Replayer(fill_model=make_model(latency_ms=500), min_settled=1).run(
        iter(events), BuyOnce()
    )
    assert len(result.fills) == 0
    assert result.cancelled_orders == 1


def test_orders_left_pending_at_end_are_unfilled() -> None:
    events = [snapshot(0, ask=30)]
    result = Replayer(fill_model=make_model(latency_ms=500), min_settled=1).run(
        iter(events), BuyOnce()
    )
    assert len(result.fills) == 0
    assert result.unfilled_orders == 1


class Backdater:
    def on_snapshot(self, snap: OrderbookSnapshot, ctx) -> list[Order]:
        return [Order(ts_ms=snap.ts_ms - 1, market=snap.market, side="yes", action="buy", quantity=1)]


def test_backdated_orders_rejected_as_lookahead() -> None:
    with pytest.raises(ValueError, match="lookahead"):
        Replayer(fill_model=make_model(), min_settled=1).run(
            iter([snapshot(1000, ask=30)]), Backdater()
        )


def test_fixture_end_to_end_is_deterministic_and_gate_fails() -> None:
    config = FixtureConfig(n_markets=40, snapshots_per_market=40, seed=11)

    def run():
        return Replayer(fill_model=make_model(), min_settled=30).run(
            generate_events(config), ThresholdScaffold(threshold_cents=35, quantity=20)
        )

    first, second = run(), run()
    assert len(first.fills) > 0, "scaffold should trade on cheap synthetic markets"
    assert first.ledger.total_pnl() == second.ledger.total_pnl()
    assert first.report.ci_low == second.report.ci_low
    # Synthetic prices are fair by construction; after fees and spread the
    # edge gate must reject the scaffold. If this ever passes, the gate lies.
    assert not first.report.passed
    summary = first.summary()
    assert "verdict" in summary and "FAIL" in summary
