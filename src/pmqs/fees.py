"""Kalshi-style fee math.

The published general formula (verify against the current official fee
schedule before relying on it -- rates and per-series multipliers change):

    taker fee = round_up( rate * contracts * P * (1 - P) )

with ``P`` the price in dollars and ``rate`` 0.07 for most series. Maker fees,
where charged, are a fraction (currently 25%) of the taker fee.

Two rounding modes are provided:

- ``CENT_CEIL``: round each fill's fee up to the next cent. This matches the
  classic published behavior and is the *conservative* default: a backtest
  that survives cent-ceiling fees will not be undone by gentler rounding.
- ``TENTH_MILL_CEIL``: round up to the nearest $0.0001, matching the exchange's
  documented 2026 fill-level trade-fee precision. The venue additionally
  applies a balance-precision rounding fee with a rebate accumulator across
  the fills of an order; net of rebates that mechanism converges toward fair
  value, so this mode is a slightly optimistic lower bound.

All amounts are Decimal dollars.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_CEILING, Decimal
from enum import Enum
from typing import Mapping


class RoundingMode(Enum):
    CENT_CEIL = "cent_ceil"
    TENTH_MILL_CEIL = "tenth_mill_ceil"


_QUANTA = {
    RoundingMode.CENT_CEIL: Decimal("0.01"),
    RoundingMode.TENTH_MILL_CEIL: Decimal("0.0001"),
}


@dataclass(frozen=True)
class FeeSchedule:
    """Configurable fee schedule with per-series overrides.

    ``series_taker_rates`` maps a market-ticker *prefix* to a taker rate, so
    premium categories can be modeled without code changes, e.g.::

        FeeSchedule(series_taker_rates={"KXBTC": Decimal("0.10")})

    The longest matching prefix wins.
    """

    default_taker_rate: Decimal = Decimal("0.07")
    maker_fraction: Decimal = Decimal("0.25")
    charge_maker_fees: bool = True
    series_taker_rates: Mapping[str, Decimal] = field(default_factory=dict)
    rounding: RoundingMode = RoundingMode.CENT_CEIL

    def taker_rate(self, market: str) -> Decimal:
        best = ""
        for prefix in self.series_taker_rates:
            if market.startswith(prefix) and len(prefix) > len(best):
                best = prefix
        return self.series_taker_rates[best] if best else self.default_taker_rate

    def fill_fee(
        self,
        *,
        contracts: int,
        price_cents: int,
        market: str,
        liquidity: str = "taker",
    ) -> Decimal:
        """Fee in Decimal dollars for a single fill."""
        if contracts <= 0:
            raise ValueError("contracts must be positive")
        if not 1 <= price_cents <= 99:
            raise ValueError("price_cents must be in [1, 99]")
        if liquidity not in ("taker", "maker"):
            raise ValueError("liquidity must be 'taker' or 'maker'")

        if liquidity == "maker" and not self.charge_maker_fees:
            return Decimal("0.00")

        price = Decimal(price_cents) / Decimal(100)
        rate = self.taker_rate(market)
        if liquidity == "maker":
            rate = rate * self.maker_fraction
        raw = rate * price * (Decimal(1) - price) * Decimal(contracts)
        return raw.quantize(_QUANTA[self.rounding], rounding=ROUND_CEILING)
