import pytest

from pmqs.orderbook import (
    BookLevel,
    OrderbookSnapshot,
    SettlementEvent,
    parse_event,
    read_events,
)


def make_book() -> OrderbookSnapshot:
    return OrderbookSnapshot(
        ts_ms=1000,
        market="TEST-1",
        yes_bids=(BookLevel(48, 100), BookLevel(47, 200)),
        no_bids=(BookLevel(50, 150), BookLevel(49, 250)),
    )


def test_no_bids_imply_yes_asks() -> None:
    book = make_book()
    asks = book.yes_asks()
    assert [(a.price_cents, a.quantity) for a in asks] == [(50, 150), (51, 250)]
    assert book.best_yes_ask() == 50
    assert book.best_yes_bid() == 48
    assert book.yes_mid() == 49.0
    assert book.spread_cents() == 2


def test_yes_bids_imply_no_asks() -> None:
    book = make_book()
    asks = book.no_asks()
    assert [(a.price_cents, a.quantity) for a in asks] == [(52, 100), (53, 200)]


def test_crossed_book_rejected() -> None:
    with pytest.raises(ValueError, match="crossed"):
        OrderbookSnapshot(
            ts_ms=1,
            market="X",
            yes_bids=(BookLevel(60, 10),),
            no_bids=(BookLevel(50, 10),),
        )


def test_unsorted_ladder_rejected() -> None:
    with pytest.raises(ValueError, match="descending"):
        OrderbookSnapshot(
            ts_ms=1,
            market="X",
            yes_bids=(BookLevel(40, 10), BookLevel(45, 10)),
        )


def test_json_round_trip() -> None:
    book = make_book()
    parsed = parse_event(book.to_json())
    assert parsed == book

    settlement = SettlementEvent(ts_ms=2000, market="TEST-1", result="yes")
    assert parse_event(settlement.to_json()) == settlement


def test_read_events_enforces_time_order() -> None:
    early = OrderbookSnapshot(ts_ms=1000, market="A", yes_bids=(BookLevel(40, 10),))
    late = OrderbookSnapshot(ts_ms=2000, market="A", yes_bids=(BookLevel(41, 10),))
    lines = [late.to_json(), early.to_json()]
    with pytest.raises(ValueError, match="out of time order"):
        list(read_events(lines))


def test_settlement_result_validated() -> None:
    with pytest.raises(ValueError):
        SettlementEvent(ts_ms=1, market="X", result="maybe")
