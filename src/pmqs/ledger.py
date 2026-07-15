"""Position and cash ledger with settlement handling.

Tracks per-market YES and NO inventories and a single cash balance in
Decimal dollars. Buys reduce cash by notional plus fee; sells increase cash
by notional minus fee; settlement pays $1.00 per contract on the winning
side and zero on the losing side.

Realized per-market PnL is only defined once a market settles (or the
position is fully closed); that per-market series is what the edge gate
bootstraps over, because fills within one market are not independent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from pmqs.fills import Fill


@dataclass
class _MarketState:
    yes_contracts: int = 0
    no_contracts: int = 0
    cash_flow: Decimal = Decimal("0")  # negative = money spent on this market
    fees_paid: Decimal = Decimal("0")
    settled: bool = False
    result: str | None = None


@dataclass
class Ledger:
    markets: dict[str, _MarketState] = field(default_factory=dict)
    fills: list[Fill] = field(default_factory=list)

    def _state(self, market: str) -> _MarketState:
        return self.markets.setdefault(market, _MarketState())

    def record_fill(self, fill: Fill) -> None:
        state = self._state(fill.market)
        if state.settled:
            raise ValueError(f"market {fill.market} already settled")

        signed = fill.quantity if fill.action == "buy" else -fill.quantity
        if fill.side == "yes":
            new_position = state.yes_contracts + signed
        else:
            new_position = state.no_contracts + signed
        if new_position < 0:
            raise ValueError(
                f"sell of {fill.quantity} {fill.side} on {fill.market} exceeds inventory; "
                "short selling is expressed by buying the opposite side"
            )
        if fill.side == "yes":
            state.yes_contracts = new_position
        else:
            state.no_contracts = new_position

        if fill.action == "buy":
            state.cash_flow -= fill.notional
        else:
            state.cash_flow += fill.notional
        state.cash_flow -= fill.fee
        state.fees_paid += fill.fee
        self.fills.append(fill)

    def settle(self, market: str, result: str) -> None:
        if result not in ("yes", "no"):
            raise ValueError("result must be 'yes' or 'no'")
        state = self._state(market)
        if state.settled:
            raise ValueError(f"market {market} settled twice")
        winning = state.yes_contracts if result == "yes" else state.no_contracts
        state.cash_flow += Decimal(winning)  # $1.00 per winning contract
        state.yes_contracts = 0
        state.no_contracts = 0
        state.settled = True
        state.result = result

    # -- Reporting ------------------------------------------------------------
    def position(self, market: str) -> tuple[int, int]:
        state = self._state(market)
        return state.yes_contracts, state.no_contracts

    def per_market_pnl(self, *, settled_only: bool = True) -> dict[str, Decimal]:
        """Post-fee PnL per market. Unsettled markets are excluded by default
        because their PnL is not realized evidence."""
        return {
            market: state.cash_flow
            for market, state in self.markets.items()
            if state.settled or not settled_only
        }

    def total_pnl(self, *, settled_only: bool = True) -> Decimal:
        pnls = self.per_market_pnl(settled_only=settled_only)
        return sum(pnls.values(), Decimal("0"))

    def total_fees(self) -> Decimal:
        return sum((s.fees_paid for s in self.markets.values()), Decimal("0"))

    def n_settled(self) -> int:
        return sum(1 for s in self.markets.values() if s.settled)
