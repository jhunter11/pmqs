from decimal import Decimal

import pytest

from pmqs.fees import FeeSchedule, RoundingMode


def test_taker_fee_exact_at_even_price() -> None:
    schedule = FeeSchedule()
    # 0.07 * 0.50 * 0.50 * 100 = 1.75 exactly; no rounding needed.
    assert schedule.fill_fee(contracts=100, price_cents=50, market="M") == Decimal("1.75")


def test_taker_fee_cent_ceiling() -> None:
    schedule = FeeSchedule()
    # 0.07 * 0.5 * 0.5 = 0.0175 -> ceil to next cent.
    assert schedule.fill_fee(contracts=1, price_cents=50, market="M") == Decimal("0.02")
    # 0.07 * 0.33 * 0.67 * 7 = 0.108339 -> 0.11
    assert schedule.fill_fee(contracts=7, price_cents=33, market="M") == Decimal("0.11")


def test_taker_fee_tenth_mill_mode() -> None:
    schedule = FeeSchedule(rounding=RoundingMode.TENTH_MILL_CEIL)
    assert schedule.fill_fee(contracts=1, price_cents=50, market="M") == Decimal("0.0175")
    assert schedule.fill_fee(contracts=7, price_cents=33, market="M") == Decimal("0.1084")


def test_maker_fee_is_quarter_of_taker() -> None:
    schedule = FeeSchedule(rounding=RoundingMode.TENTH_MILL_CEIL)
    taker = schedule.fill_fee(contracts=100, price_cents=50, market="M", liquidity="taker")
    maker = schedule.fill_fee(contracts=100, price_cents=50, market="M", liquidity="maker")
    assert maker == taker * Decimal("0.25")


def test_maker_fee_can_be_disabled() -> None:
    schedule = FeeSchedule(charge_maker_fees=False)
    assert (
        schedule.fill_fee(contracts=100, price_cents=50, market="M", liquidity="maker")
        == Decimal("0.00")
    )


def test_series_override_longest_prefix_wins() -> None:
    schedule = FeeSchedule(
        series_taker_rates={"KX": Decimal("0.05"), "KXBTC": Decimal("0.10")}
    )
    assert schedule.taker_rate("KXBTC-26JUL15-B") == Decimal("0.10")
    assert schedule.taker_rate("KXETH-26JUL15-B") == Decimal("0.05")
    assert schedule.taker_rate("OTHER") == Decimal("0.07")


def test_fee_symmetry_around_fifty() -> None:
    schedule = FeeSchedule()
    low = schedule.fill_fee(contracts=10, price_cents=20, market="M")
    high = schedule.fill_fee(contracts=10, price_cents=80, market="M")
    assert low == high


@pytest.mark.parametrize("bad_price", [0, 100, -5])
def test_rejects_out_of_range_price(bad_price: int) -> None:
    with pytest.raises(ValueError):
        FeeSchedule().fill_fee(contracts=1, price_cents=bad_price, market="M")


def test_rejects_non_positive_contracts() -> None:
    with pytest.raises(ValueError):
        FeeSchedule().fill_fee(contracts=0, price_cents=50, market="M")
