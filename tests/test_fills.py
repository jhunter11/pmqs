from decimal import Decimal

import pytest

from pmqs.fees import FeeSchedule
from pmqs.fills import ConservativeFillModel, Order
from pmqs.orderbook import BookLevel, OrderbookSnapshot


def model(haircut: str = "1.0") -> ConservativeFillModel:
    return ConservativeFillModel(
        fee_schedule=FeeSchedule(), latency_ms=0, size_haircut=Decimal(haircut)
    )


def book() -> OrderbookSnapshot:
    # YES asks implied at 50 (x100) then 52 (x100).
    return OrderbookSnapshot(
        ts_ms=5000,
        market="M",
        yes_bids=(BookLevel(45, 300),),
        no_bids=(BookLevel(50, 100), BookLevel(48, 100)),
    )


def test_buy_walks_ask_ladder() -> None:
    fill = model().execute(Order(ts_ms=1, market="M", side="yes", action="buy", quantity=150), book())
    assert fill is not None
    assert fill.quantity == 150
    assert fill.levels == ((50, 100), (52, 50))
    assert fill.vwap_cents == (Decimal(50) * 100 + Decimal(52) * 50) / Decimal(150)
    assert fill.ts_ms == 5000  # stamped with book time, not decision time


def test_haircut_limits_available_size() -> None:
    fill = model("0.5").execute(
        Order(ts_ms=1, market="M", side="yes", action="buy", quantity=150), book()
    )
    assert fill is not None
    # Only 50% of each level's 100 displayed is assumed available.
    assert fill.levels == ((50, 50), (52, 50))
    assert fill.quantity == 100


def test_no_liquidity_returns_none() -> None:
    empty = OrderbookSnapshot(ts_ms=1, market="M", yes_bids=(BookLevel(45, 10),))
    fill = model().execute(Order(ts_ms=1, market="M", side="yes", action="buy", quantity=10), empty)
    assert fill is None


def test_sell_hits_bids() -> None:
    fill = model().execute(
        Order(ts_ms=1, market="M", side="yes", action="sell", quantity=100), book()
    )
    assert fill is not None
    assert fill.levels == ((45, 100),)


def test_fee_accumulates_per_level() -> None:
    fill = model().execute(Order(ts_ms=1, market="M", side="yes", action="buy", quantity=150), book())
    assert fill is not None
    schedule = FeeSchedule()
    expected = schedule.fill_fee(contracts=100, price_cents=50, market="M") + schedule.fill_fee(
        contracts=50, price_cents=52, market="M"
    )
    assert fill.fee == expected


def test_market_mismatch_raises() -> None:
    with pytest.raises(ValueError, match="does not match"):
        model().execute(Order(ts_ms=1, market="OTHER", side="yes", action="buy", quantity=1), book())
