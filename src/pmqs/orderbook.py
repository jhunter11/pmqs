"""Orderbook and event models for prediction-market backtesting.

Kalshi-style binary markets quote two sides as *bids only*: bids to buy YES
and bids to buy NO. A resting NO bid at price ``p`` cents is economically a
YES ask at ``100 - p`` cents. Getting this conversion wrong is one of the most
common silent bugs in prediction-market backtests, so the snapshot model
stores exactly what the venue publishes (two bid ladders) and *derives* asks.

JSONL wire format (one event per line):

    {"type": "book", "ts_ms": 1720000000000, "market": "KXBTC-26JUL15-B",
     "yes_bids": [[48, 120], [47, 300]], "no_bids": [[51, 90], [50, 250]]}
    {"type": "settlement", "ts_ms": 1720003600000, "market": "KXBTC-26JUL15-B",
     "result": "yes"}

Prices are integer cents in [1, 99]. Quantities are whole contracts.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Iterable, Iterator, Union


@dataclass(frozen=True, order=True)
class BookLevel:
    price_cents: int
    quantity: int

    def __post_init__(self) -> None:
        if not 1 <= self.price_cents <= 99:
            raise ValueError(f"price_cents must be in [1, 99], got {self.price_cents}")
        if self.quantity <= 0:
            raise ValueError(f"quantity must be positive, got {self.quantity}")


def _validate_bid_ladder(levels: tuple[BookLevel, ...], name: str) -> None:
    prices = [lvl.price_cents for lvl in levels]
    if prices != sorted(prices, reverse=True):
        raise ValueError(f"{name} must be sorted by price descending: {prices}")
    if len(set(prices)) != len(prices):
        raise ValueError(f"{name} has duplicate price levels: {prices}")


@dataclass(frozen=True)
class OrderbookSnapshot:
    ts_ms: int
    market: str
    yes_bids: tuple[BookLevel, ...] = field(default=())
    no_bids: tuple[BookLevel, ...] = field(default=())

    def __post_init__(self) -> None:
        if self.ts_ms < 0:
            raise ValueError("ts_ms must be non-negative")
        if not self.market:
            raise ValueError("market must be non-empty")
        object.__setattr__(self, "yes_bids", tuple(self.yes_bids))
        object.__setattr__(self, "no_bids", tuple(self.no_bids))
        _validate_bid_ladder(self.yes_bids, "yes_bids")
        _validate_bid_ladder(self.no_bids, "no_bids")
        # Crossed book: best YES bid + best NO bid > 100 means both sides
        # could be lifted for guaranteed profit; real venues match this away.
        if self.yes_bids and self.no_bids:
            if self.yes_bids[0].price_cents + self.no_bids[0].price_cents > 100:
                raise ValueError(
                    "crossed book: best yes bid "
                    f"{self.yes_bids[0].price_cents} + best no bid "
                    f"{self.no_bids[0].price_cents} > 100"
                )

    # -- Derived ask ladders ------------------------------------------------
    def yes_asks(self) -> tuple[BookLevel, ...]:
        """YES asks implied by NO bids, sorted by price ascending (best first)."""
        return tuple(
            BookLevel(price_cents=100 - lvl.price_cents, quantity=lvl.quantity)
            for lvl in self.no_bids
        )

    def no_asks(self) -> tuple[BookLevel, ...]:
        """NO asks implied by YES bids, sorted by price ascending (best first)."""
        return tuple(
            BookLevel(price_cents=100 - lvl.price_cents, quantity=lvl.quantity)
            for lvl in self.yes_bids
        )

    # -- Convenience --------------------------------------------------------
    def best_yes_bid(self) -> int | None:
        return self.yes_bids[0].price_cents if self.yes_bids else None

    def best_yes_ask(self) -> int | None:
        asks = self.yes_asks()
        return asks[0].price_cents if asks else None

    def yes_mid(self) -> float | None:
        bid, ask = self.best_yes_bid(), self.best_yes_ask()
        if bid is None or ask is None:
            return None
        return (bid + ask) / 2

    def spread_cents(self) -> int | None:
        bid, ask = self.best_yes_bid(), self.best_yes_ask()
        if bid is None or ask is None:
            return None
        return ask - bid

    # -- Serialization --------------------------------------------------------
    def to_json(self) -> str:
        return json.dumps(
            {
                "type": "book",
                "ts_ms": self.ts_ms,
                "market": self.market,
                "yes_bids": [[lvl.price_cents, lvl.quantity] for lvl in self.yes_bids],
                "no_bids": [[lvl.price_cents, lvl.quantity] for lvl in self.no_bids],
            },
            separators=(",", ":"),
        )


@dataclass(frozen=True)
class SettlementEvent:
    ts_ms: int
    market: str
    result: str  # "yes" | "no"

    def __post_init__(self) -> None:
        if self.result not in ("yes", "no"):
            raise ValueError(f"result must be 'yes' or 'no', got {self.result!r}")

    def to_json(self) -> str:
        return json.dumps(
            {
                "type": "settlement",
                "ts_ms": self.ts_ms,
                "market": self.market,
                "result": self.result,
            },
            separators=(",", ":"),
        )


Event = Union[OrderbookSnapshot, SettlementEvent]


def parse_event(line: str) -> Event:
    raw = json.loads(line)
    kind = raw.get("type")
    if kind == "book":
        return OrderbookSnapshot(
            ts_ms=int(raw["ts_ms"]),
            market=str(raw["market"]),
            yes_bids=tuple(BookLevel(int(p), int(q)) for p, q in raw.get("yes_bids", [])),
            no_bids=tuple(BookLevel(int(p), int(q)) for p, q in raw.get("no_bids", [])),
        )
    if kind == "settlement":
        return SettlementEvent(
            ts_ms=int(raw["ts_ms"]),
            market=str(raw["market"]),
            result=str(raw["result"]),
        )
    raise ValueError(f"unknown event type: {kind!r}")


def read_events(lines: Iterable[str]) -> Iterator[Event]:
    """Parse an iterable of JSONL lines, skipping blanks, enforcing time order."""
    last_ts = -1
    for lineno, line in enumerate(lines, start=1):
        line = line.strip()
        if not line:
            continue
        event = parse_event(line)
        if event.ts_ms < last_ts:
            raise ValueError(
                f"line {lineno}: events out of time order "
                f"({event.ts_ms} after {last_ts}); sort your capture file"
            )
        last_ts = event.ts_ms
        yield event
