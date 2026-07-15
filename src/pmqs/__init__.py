"""PMQS - Prediction Market Quant Stack.

Execution-aware backtesting, paper trading, and honest edge validation for
Kalshi and other prediction markets. PMQS sells rigor, not signals: nothing
in this package claims, implies, or manufactures a trading edge.
"""

from pmqs.fees import FeeSchedule, RoundingMode
from pmqs.fills import ConservativeFillModel, Fill, Order
from pmqs.fixtures import FixtureConfig, generate_events, write_fixture
from pmqs.ledger import Ledger
from pmqs.orderbook import (
    BookLevel,
    Event,
    OrderbookSnapshot,
    SettlementEvent,
    parse_event,
    read_events,
)
from pmqs.replay import BacktestResult, Replayer
from pmqs.strategy import Strategy, StrategyContext, ThresholdScaffold
from pmqs.validate import EdgeEvidenceReport, evaluate

__version__ = "0.1.0"

__all__ = [
    "BacktestResult",
    "BookLevel",
    "ConservativeFillModel",
    "EdgeEvidenceReport",
    "Event",
    "FeeSchedule",
    "Fill",
    "FixtureConfig",
    "Ledger",
    "Order",
    "OrderbookSnapshot",
    "Replayer",
    "RoundingMode",
    "SettlementEvent",
    "Strategy",
    "StrategyContext",
    "ThresholdScaffold",
    "evaluate",
    "generate_events",
    "parse_event",
    "read_events",
    "write_fixture",
]
