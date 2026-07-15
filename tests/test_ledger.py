from decimal import Decimal

import pytest

from pmqs.fills import Fill
from pmqs.ledger import Ledger


def make_fill(
    market: str = "M",
    side: str = "yes",
    action: str = "buy",
    quantity: int = 10,
    vwap: str = "40",
    fee: str = "0.02",
) -> Fill:
    return Fill(
        ts_ms=1,
        market=market,
        side=side,
        action=action,
        quantity=quantity,
        vwap_cents=Decimal(vwap),
        fee=Decimal(fee),
        levels=((int(Decimal(vwap)), quantity),),
    )


def test_buy_and_win_settlement() -> None:
    ledger = Ledger()
    ledger.record_fill(make_fill())  # 10 yes @ 40c + $0.02 fee = -$4.02
    ledger.settle("M", "yes")  # +$10.00
    assert ledger.total_pnl() == Decimal("5.98")
    assert ledger.n_settled() == 1


def test_buy_and_lose_settlement() -> None:
    ledger = Ledger()
    ledger.record_fill(make_fill())
    ledger.settle("M", "no")
    assert ledger.total_pnl() == Decimal("-4.02")


def test_no_side_settlement() -> None:
    ledger = Ledger()
    ledger.record_fill(make_fill(side="no", vwap="60", quantity=5, fee="0.09"))
    ledger.settle("M", "no")
    # -3.00 - 0.09 + 5.00 = 1.91
    assert ledger.total_pnl() == Decimal("1.91")


def test_sell_reduces_inventory_and_realizes_cash() -> None:
    ledger = Ledger()
    ledger.record_fill(make_fill(quantity=10, vwap="40", fee="0.02"))
    ledger.record_fill(make_fill(action="sell", quantity=4, vwap="55", fee="0.01"))
    assert ledger.position("M") == (6, 0)
    ledger.settle("M", "yes")
    # -4.02 + (2.20 - 0.01) + 6.00 = 4.17
    assert ledger.total_pnl() == Decimal("4.17")


def test_oversell_rejected() -> None:
    ledger = Ledger()
    ledger.record_fill(make_fill(quantity=3))
    with pytest.raises(ValueError, match="exceeds inventory"):
        ledger.record_fill(make_fill(action="sell", quantity=5))


def test_double_settlement_rejected() -> None:
    ledger = Ledger()
    ledger.record_fill(make_fill())
    ledger.settle("M", "yes")
    with pytest.raises(ValueError, match="settled twice"):
        ledger.settle("M", "yes")


def test_fill_after_settlement_rejected() -> None:
    ledger = Ledger()
    ledger.record_fill(make_fill())
    ledger.settle("M", "yes")
    with pytest.raises(ValueError, match="already settled"):
        ledger.record_fill(make_fill())


def test_unsettled_markets_excluded_from_evidence() -> None:
    ledger = Ledger()
    ledger.record_fill(make_fill(market="A"))
    ledger.record_fill(make_fill(market="B"))
    ledger.settle("A", "yes")
    assert set(ledger.per_market_pnl(settled_only=True)) == {"A"}
    assert set(ledger.per_market_pnl(settled_only=False)) == {"A", "B"}
