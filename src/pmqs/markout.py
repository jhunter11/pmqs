"""Markout and closing-line-value analytics.

Markout asks: after you traded, did the market move with you or against you?
It is the cheapest honest signal of whether fills carry information or are
just paying the spread. Closing-line value (CLV) compares your fill price to
the last observable mid before settlement -- if you systematically beat the
close, you were early to real information; if not, your wins were luck or
selection bias.

Sign convention: positive = good for you, in cents per contract.
"""

from __future__ import annotations

from bisect import bisect_left
from dataclasses import dataclass
from decimal import Decimal
from typing import Mapping, Sequence

from pmqs.fills import Fill
from pmqs.orderbook import OrderbookSnapshot


def _side_mid(book: OrderbookSnapshot, side: str) -> Decimal | None:
    mid = book.yes_mid()
    if mid is None:
        return None
    value = Decimal(str(mid))
    return value if side == "yes" else Decimal(100) - value


def _signed_edge(fill: Fill, mid_cents: Decimal) -> Decimal:
    """Positive when the reference mid is on the profitable side of the fill."""
    if fill.action == "buy":
        return mid_cents - fill.vwap_cents
    return fill.vwap_cents - mid_cents


@dataclass(frozen=True)
class MarkoutResult:
    fill: Fill
    horizon_ms: int
    edge_cents: Decimal


def markout(
    fill: Fill,
    snapshots: Sequence[OrderbookSnapshot],
    horizon_ms: int,
) -> MarkoutResult | None:
    """Markout for one fill against that market's time-sorted snapshots.

    Uses the first snapshot at or after ``fill.ts_ms + horizon_ms``. Returns
    None when the market has no usable snapshot at the horizon (never
    fabricate a markout from the fill's own book).
    """
    target = fill.ts_ms + horizon_ms
    timestamps = [s.ts_ms for s in snapshots]
    idx = bisect_left(timestamps, target)
    for snapshot in snapshots[idx:]:
        mid = _side_mid(snapshot, fill.side)
        if mid is not None:
            return MarkoutResult(fill=fill, horizon_ms=horizon_ms, edge_cents=_signed_edge(fill, mid))
    return None


def closing_line_value(
    fill: Fill,
    snapshots: Sequence[OrderbookSnapshot],
) -> Decimal | None:
    """CLV vs the last snapshot with a defined mid for the fill's market."""
    for snapshot in reversed(snapshots):
        mid = _side_mid(snapshot, fill.side)
        if mid is not None:
            return _signed_edge(fill, mid)
    return None


def collect_markouts(
    fills: Sequence[Fill],
    snapshots_by_market: Mapping[str, Sequence[OrderbookSnapshot]],
    horizon_ms: int,
) -> list[MarkoutResult]:
    results: list[MarkoutResult] = []
    for fill in fills:
        series = snapshots_by_market.get(fill.market, ())
        result = markout(fill, series, horizon_ms)
        if result is not None:
            results.append(result)
    return results


def collect_clv(
    fills: Sequence[Fill],
    snapshots_by_market: Mapping[str, Sequence[OrderbookSnapshot]],
) -> list[Decimal]:
    values: list[Decimal] = []
    for fill in fills:
        series = snapshots_by_market.get(fill.market, ())
        value = closing_line_value(fill, series)
        if value is not None:
            values.append(value)
    return values
