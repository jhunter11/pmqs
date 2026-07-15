from decimal import Decimal

from pmqs.fills import Fill
from pmqs.markout import closing_line_value, markout
from pmqs.orderbook import BookLevel, OrderbookSnapshot


def snapshot(ts_ms: int, bid: int, ask: int) -> OrderbookSnapshot:
    return OrderbookSnapshot(
        ts_ms=ts_ms,
        market="M",
        yes_bids=(BookLevel(bid, 100),),
        no_bids=(BookLevel(100 - ask, 100),),
    )


def buy_fill(ts_ms: int = 1000, vwap: str = "50", side: str = "yes") -> Fill:
    return Fill(
        ts_ms=ts_ms,
        market="M",
        side=side,
        action="buy",
        quantity=10,
        vwap_cents=Decimal(vwap),
        fee=Decimal("0.02"),
        levels=((50, 10),),
    )


def test_markout_positive_when_market_moves_with_buy() -> None:
    series = [snapshot(1000, 49, 51), snapshot(61_000, 55, 57)]  # mid 50 -> 56
    result = markout(buy_fill(), series, horizon_ms=60_000)
    assert result is not None
    assert result.edge_cents == Decimal("6")


def test_markout_negative_when_market_moves_against_buy() -> None:
    series = [snapshot(1000, 49, 51), snapshot(61_000, 43, 45)]  # mid 50 -> 44
    result = markout(buy_fill(), series, horizon_ms=60_000)
    assert result is not None
    assert result.edge_cents == Decimal("-6")


def test_markout_none_when_no_future_snapshot() -> None:
    series = [snapshot(1000, 49, 51)]
    assert markout(buy_fill(), series, horizon_ms=60_000) is None


def test_no_side_markout_uses_complement_mid() -> None:
    series = [snapshot(1000, 49, 51), snapshot(61_000, 55, 57)]  # yes mid 56 -> no mid 44
    result = markout(buy_fill(vwap="50", side="no"), series, horizon_ms=60_000)
    assert result is not None
    assert result.edge_cents == Decimal("-6")


def test_clv_uses_last_defined_mid() -> None:
    series = [snapshot(1000, 49, 51), snapshot(5000, 60, 62), snapshot(9000, 70, 72)]
    value = closing_line_value(buy_fill(vwap="50"), series)
    assert value == Decimal("21")  # 71 - 50
