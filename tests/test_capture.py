import json

from pmqs.capture import main, snapshot_from_api
from pmqs.orderbook import read_events


def test_fixture_mode_writes_replayable_events(tmp_path) -> None:
    out = tmp_path / "fixture.jsonl"
    assert main(["--fixture", "--out", str(out), "--seed", "3"]) == 0
    lines = out.read_text(encoding="utf-8").splitlines()
    events = list(read_events(lines))
    assert len(events) == len(lines) > 0


def test_snapshot_from_api_payload() -> None:
    payload = {
        "orderbook": {
            "yes": [[47, 200], [48, 100]],
            "no": [[50, 150], [49, 50]],
        }
    }
    snap = snapshot_from_api("KXTEST-1", payload, ts_ms=123456)
    assert snap.market == "KXTEST-1"
    assert snap.ts_ms == 123456
    assert [(lvl.price_cents, lvl.quantity) for lvl in snap.yes_bids] == [(48, 100), (47, 200)]
    assert snap.best_yes_ask() == 50


def test_snapshot_from_api_handles_null_sides() -> None:
    snap = snapshot_from_api("KXTEST-1", {"orderbook": {"yes": None, "no": None}}, ts_ms=1)
    assert snap.yes_bids == ()
    assert snap.no_bids == ()
    assert snap.yes_mid() is None


def test_fixture_output_is_valid_json_lines(tmp_path) -> None:
    out = tmp_path / "f.jsonl"
    main(["--fixture", "--out", str(out)])
    for line in out.read_text(encoding="utf-8").splitlines():
        parsed = json.loads(line)
        assert parsed["type"] in ("book", "settlement")
