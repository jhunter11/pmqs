"""Kalshi market-data capture (bring your own API key).

PMQS never ships market data. Kalshi's data terms restrict redistribution of
archived data, so you capture your own history, under your own API agreement,
with your own key. This module is a thin, dependency-light REST poller that
writes the same JSONL event format the replayer consumes.

Auth: Kalshi API v2 signs requests with an RSA private key (RSA-PSS/SHA-256
over ``timestamp + method + path``). The ``cryptography`` package is required
only for live capture -- install with ``pip install pmqs[capture]``. The
``--fixture`` mode needs no network, no key, and no extra dependency; it
exists so you can prove the full capture -> replay -> gate pipeline end to
end before ever touching the venue.

Never commit your private key. The repo's .gitignore refuses *.pem/*.key/.env
by default, and this module only ever reads the key path you pass explicitly.
"""

from __future__ import annotations

import argparse
import base64
import json
import time
import urllib.request
from dataclasses import dataclass

from pmqs.fixtures import FixtureConfig, write_fixture
from pmqs.orderbook import BookLevel, OrderbookSnapshot

DEFAULT_BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"


@dataclass(frozen=True)
class KalshiCredentials:
    key_id: str
    private_key_path: str


def _sign(credentials: KalshiCredentials, method: str, path: str, ts_ms: int) -> str:
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
    except ImportError as exc:  # pragma: no cover - exercised only without extra
        raise RuntimeError(
            "live capture requires the 'cryptography' package: pip install pmqs[capture]"
        ) from exc

    with open(credentials.private_key_path, "rb") as handle:
        private_key = serialization.load_pem_private_key(handle.read(), password=None)
    message = f"{ts_ms}{method}{path}".encode()
    signature = private_key.sign(
        message,
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH),
        hashes.SHA256(),
    )
    return base64.b64encode(signature).decode()


def _get(credentials: KalshiCredentials, base_url: str, path: str) -> dict:
    ts_ms = int(time.time() * 1000)
    api_path = "/trade-api/v2" + path
    request = urllib.request.Request(base_url + path, method="GET")
    request.add_header("KALSHI-ACCESS-KEY", credentials.key_id)
    request.add_header("KALSHI-ACCESS-SIGNATURE", _sign(credentials, "GET", api_path, ts_ms))
    request.add_header("KALSHI-ACCESS-TIMESTAMP", str(ts_ms))
    request.add_header("Accept", "application/json")
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode())


def snapshot_from_api(market: str, payload: dict, ts_ms: int) -> OrderbookSnapshot:
    """Convert a Kalshi orderbook payload into a snapshot.

    The API returns ``{"orderbook": {"yes": [[price, qty], ...], "no": [...]}}``
    where both ladders are *bids*. Empty sides arrive as null.
    """
    book = payload.get("orderbook") or {}
    yes_raw = book.get("yes") or []
    no_raw = book.get("no") or []
    yes_bids = tuple(
        BookLevel(int(p), int(q))
        for p, q in sorted(yes_raw, key=lambda level: -int(level[0]))
        if int(q) > 0
    )
    no_bids = tuple(
        BookLevel(int(p), int(q))
        for p, q in sorted(no_raw, key=lambda level: -int(level[0]))
        if int(q) > 0
    )
    return OrderbookSnapshot(ts_ms=ts_ms, market=market, yes_bids=yes_bids, no_bids=no_bids)


def poll(
    credentials: KalshiCredentials,
    tickers: list[str],
    out_path: str,
    *,
    base_url: str = DEFAULT_BASE_URL,
    interval_s: float = 5.0,
    iterations: int = 60,
) -> int:
    """Poll orderbooks for ``tickers`` and append JSONL snapshots to ``out_path``."""
    written = 0
    with open(out_path, "a", encoding="utf-8", newline="\n") as handle:
        for _ in range(iterations):
            for ticker in tickers:
                payload = _get(credentials, base_url, f"/markets/{ticker}/orderbook")
                snapshot = snapshot_from_api(ticker, payload, int(time.time() * 1000))
                handle.write(snapshot.to_json() + "\n")
                written += 1
            handle.flush()
            time.sleep(interval_s)
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m pmqs.capture",
        description="Capture Kalshi orderbook snapshots to JSONL (bring your own key), "
        "or generate a synthetic no-network fixture with --fixture.",
    )
    parser.add_argument("--out", required=True, help="output JSONL path")
    parser.add_argument("--fixture", action="store_true", help="no-network synthetic mode")
    parser.add_argument("--tickers", nargs="*", default=[], help="market tickers to poll")
    parser.add_argument("--key-id", help="Kalshi API key id")
    parser.add_argument("--private-key", help="path to RSA private key PEM")
    parser.add_argument("--interval", type=float, default=5.0)
    parser.add_argument("--iterations", type=int, default=60)
    parser.add_argument("--seed", type=int, default=7, help="fixture seed")
    args = parser.parse_args(argv)

    if args.fixture:
        count = write_fixture(args.out, FixtureConfig(seed=args.seed))
        print(f"wrote {count} synthetic events to {args.out} (no network used)")
        return 0

    if not args.tickers or not args.key_id or not args.private_key:
        parser.error("live capture requires --tickers, --key-id, and --private-key")
    credentials = KalshiCredentials(key_id=args.key_id, private_key_path=args.private_key)
    count = poll(
        credentials,
        args.tickers,
        args.out,
        interval_s=args.interval,
        iterations=args.iterations,
    )
    print(f"wrote {count} snapshots to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
